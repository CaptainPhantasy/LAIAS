"""
Validate Code endpoint for Agent Generator API.

POST /api/validate-code
Validates Python code against Godzilla architectural pattern.
"""

from fastapi import APIRouter, HTTPException, status
import structlog

from app.models.requests import ValidateCodeRequest
from app.models.responses import ValidateCodeResponse
from app.services.validator import get_validator

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["validation"])


@router.post("/validate-code", response_model=ValidateCodeResponse, status_code=status.HTTP_200_OK)
async def validate_code(request: ValidateCodeRequest) -> ValidateCodeResponse:
    """
    Validate Python code against Godzilla pattern.

    This endpoint performs:
    - Python syntax validation
    - Pattern compliance checking
    - Quality assessment
    - Improvement suggestions

    - **code**: Python source code to validate
    - **check_pattern_compliance**: Enable Godzilla pattern checking
    - **check_syntax**: Enable Python syntax validation
    """
    try:
        logger.info(
            "Code validation request received",
            check_pattern_compliance=request.check_pattern_compliance,
            check_syntax=request.check_syntax
        )

        validator = get_validator()
        result = validator.validate_code(
            code=request.code,
            check_pattern_compliance=request.check_pattern_compliance,
            check_syntax=request.check_syntax
        )

        return ValidateCodeResponse(**result)

    except Exception as e:
        logger.error("Code validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate code: {str(e)}"
        )


@router.get("/validation-rules", status_code=status.HTTP_200_OK)
async def get_validation_rules():
    """
    Get Godzilla pattern validation rules.

    Returns the rules used for pattern validation.
    """
    from app.services.template_service import get_template_service

    template_service = get_template_service()
    rules = template_service.get_validation_rules()

    return {
        "required_patterns": [
            {"pattern": p, "description": d}
            for p, d in rules.get("required_patterns", [])
        ],
        "recommended_patterns": [
            {"pattern": p, "description": d}
            for p, d in rules.get("recommended_patterns", [])
        ]
    }
