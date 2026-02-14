"""
Log streaming endpoints.

Provides REST and WebSocket access to container logs.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, List
from datetime import datetime
import asyncio

from app.models.responses import LogsResponse, LogEntry
from app.services.log_streamer import get_log_streamer
from app.services.docker_service import get_docker_service
from app.utils.exceptions import (
    ContainerNotFoundError,
    LogStreamingError,
    exception_to_http_response,
)

router = APIRouter(prefix="/api", tags=["logs"])


@router.get(
    "/containers/{container_id}/logs",
    response_model=LogsResponse,
    summary="Get container logs",
    description="Retrieve logs from a container",
)
async def get_container_logs(
    container_id: str,
    tail: int = Query(100, ge=1, le=10000, description="Number of lines from end"),
    since: Optional[str] = Query(None, description="ISO timestamp to start from"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    offset: Optional[int] = Query(0, ge=0, description="Offset from start of logs"),
) -> LogsResponse:
    """
    Get container logs with pagination support.

    Args:
        container_id: Container ID
        tail: Number of lines from end of logs (for pagination: fetches tail+offset)
        since: ISO timestamp to start from
        level: Optional log level filter
        offset: Number of lines to skip from the start of returned logs

    Returns:
        LogsResponse: Container logs with pagination info

    Raises:
        HTTPException: If container not found or logs unavailable
    """
    try:
        # Verify container exists
        await get_docker_service().get_container(container_id)

        # For pagination, we fetch more logs than requested to determine if there are more
        # We fetch (tail + offset + 1) lines, then apply offset and check for extra
        fetch_count = tail + offset + 1

        # Get logs
        log_lines = await get_docker_service().get_container_logs(
            container_id=container_id,
            tail=fetch_count,
            since=since,
        )

        # Calculate if more logs exist (before filtering)
        # If we got more lines than tail + offset, there are more logs available
        has_more_unfiltered = len(log_lines) > (tail + offset)

        # Apply offset (skip first N lines)
        if offset > 0:
            log_lines = log_lines[offset:] if offset < len(log_lines) else []

        # Slice to requested tail size
        paginated_lines = log_lines[:tail]

        # Parse log entries
        log_entries = []
        for line in paginated_lines:
            if not line.strip():
                continue

            entry = get_log_streamer().parse_log_line(line)
            if entry:
                # Apply level filter if provided
                if level is None or entry["level"].upper() == level.upper():
                    log_entries.append(
                        LogEntry(
                            timestamp=entry["timestamp"],
                            level=entry["level"],
                            message=entry["message"],
                            source=entry["source"],
                        )
                    )

        # Determine if there are more logs after this page
        # We have more if either:
        # 1. We had more raw lines before slicing (has_more_unfiltered)
        # 2. We filtered some entries and might have more matching entries
        has_more = has_more_unfiltered or len(paginated_lines) > len(log_entries)

        return LogsResponse(
            container_id=container_id,
            logs=log_entries,
            has_more=has_more,
        )

    except Exception as e:
        if "not found" in str(e).lower():
            raise exception_to_http_response(
                ContainerNotFoundError(container_id, detail=str(e))
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GET_LOGS_FAILED",
                "message": f"Failed to get logs for container {container_id}",
                "detail": str(e),
            },
        )


@router.websocket("/containers/{container_id}/logs/stream")
async def stream_container_logs(
    websocket: WebSocket,
    container_id: str,
    tail: int = Query(100, ge=0, le=1000),
):
    """
    Stream container logs via WebSocket.

    Args:
        websocket: WebSocket connection
        container_id: Container ID
        tail: Number of previous lines to include before streaming

    Connection closes when:
    - Container stops
    - WebSocket disconnects
    - Error occurs
    """
    await websocket.accept()

    try:
        # Verify container exists
        await get_docker_service().get_container(container_id)

        # Create log streaming task
        stream_task = asyncio.create_task(
            _log_stream_handler(websocket, container_id, tail)
        )

        # Wait for client disconnect
        try:
            while True:
                # Receive ping from client to keep connection alive
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data == "close":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            # Cancel streaming task
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e),
        })
        await websocket.close()


async def _log_stream_handler(
    websocket: WebSocket,
    container_id: str,
    tail: int,
) -> None:
    """
    Handle the log streaming logic.

    Args:
        websocket: WebSocket connection
        container_id: Container ID
        tail: Number of previous lines to include
    """
    import structlog
    logger = structlog.get_logger()

    try:
        # Send previous logs first if requested
        if tail > 0:
            previous_logs = await get_docker_service().get_container_logs(
                container_id=container_id,
                tail=tail,
            )
            for line in previous_logs:
                if line.strip():
                    entry = get_log_streamer().parse_log_line(line)
                    if entry:
                        await websocket.send_json({
                            "type": "log",
                            "data": entry,
                        })

        # Stream new logs
        async for log_entry in get_log_streamer().stream_logs(container_id):
            await websocket.send_json({
                "type": "log",
                "data": log_entry,
            })

    except asyncio.CancelledError:
        # Normal shutdown
        logger.info("Log stream cancelled", container_id=container_id)
    except Exception as e:
        logger.error("Log stream error", container_id=container_id, error=str(e))
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e),
            })
        except Exception:
            pass
