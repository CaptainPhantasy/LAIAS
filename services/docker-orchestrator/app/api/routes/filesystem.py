import os

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.config import settings
from app.models.responses import FileBrowserEntry, FileBrowserResponse

router = APIRouter(prefix="/api", tags=["filesystem"])


class MkdirRequest(BaseModel):
    path: str = Field(..., description="Directory path under file browser root")


def _resolve_safe_path(user_path: str | None) -> str:
    browse_root = os.path.realpath(settings.FILESYSTEM_BROWSE_ROOT)
    requested_path = (user_path or browse_root).strip()

    if os.path.isabs(requested_path):
        target_path = os.path.realpath(requested_path)
    else:
        target_path = os.path.realpath(os.path.join(browse_root, requested_path))

    if os.path.commonpath([browse_root, target_path]) != browse_root:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Path traversal not allowed"
        )

    return target_path


@router.get(
    "/filesystem/browse",
    response_model=FileBrowserResponse,
    summary="Browse directories under filesystem root",
)
async def browse_filesystem(path: str | None = Query(default=None)) -> FileBrowserResponse:
    browse_root = os.path.realpath(settings.FILESYSTEM_BROWSE_ROOT)
    target_path = _resolve_safe_path(path)
    if not os.path.isdir(target_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")

    entries: list[FileBrowserEntry] = []
    for name in sorted(os.listdir(target_path)):
        full_path = os.path.join(target_path, name)
        if not os.path.isdir(full_path):
            continue

        entries.append(
            FileBrowserEntry(
                name=name,
                path=full_path,
                type="directory",
                children_count=sum(
                    1
                    for child in os.listdir(full_path)
                    if os.path.isdir(os.path.join(full_path, child))
                ),
            )
        )

    parent_path = None
    if target_path != browse_root:
        parent_path = os.path.dirname(target_path)

    return FileBrowserResponse(current_path=target_path, parent_path=parent_path, entries=entries)


@router.post(
    "/filesystem/mkdir",
    response_model=FileBrowserEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Create directory under filesystem root",
)
async def create_directory(body: MkdirRequest) -> FileBrowserEntry:
    target_path = _resolve_safe_path(body.path)
    if os.path.exists(target_path) and not os.path.isdir(target_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path exists and is not a directory",
        )

    os.makedirs(target_path, exist_ok=True)

    return FileBrowserEntry(
        name=os.path.basename(target_path.rstrip(os.sep)) or ".",
        path=target_path,
        type="directory",
        children_count=0,
    )
