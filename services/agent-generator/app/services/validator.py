"""
Validator Service for Agent Generator.

Provides code validation against Godzilla pattern,
syntax checking, and quality assessment.
"""

import ast
import re
from typing import Any, Dict, List, Optional, Tuple
import structlog

from app.utils.code_parser import CodeParser
from app.utils.exceptions import CodeValidationError

logger = structlog.get_logger()


class CodeValidator:
    """
    Validator for generated agent code.

    Performs:
    - Python syntax validation
    - Godzilla pattern compliance checking
    - Quality assessment
    """

    def __init__(self):
        """Initialize the validator."""
        self.parser = CodeParser()

    def validate_code(
        self,
        code: str,
        check_pattern_compliance: bool = True,
        check_syntax: bool = True
    ) -> Dict[str, Any]:
        """
        Validate code against Godzilla pattern.

        Args:
            code: Python source code
            check_pattern_compliance: Check pattern compliance
            check_syntax: Check Python syntax

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        missing_patterns = []
        suggestions = []

        # Step 1: Syntax validation
        if check_syntax:
            is_valid_syntax, syntax_errors = self.parser.validate_syntax(code)
            if not is_valid_syntax:
                errors.extend(syntax_errors)
                return {
                    "is_valid": False,
                    "syntax_errors": syntax_errors,
                    "pattern_compliance": 0.0,
                    "warnings": [],
                    "suggestions": [],
                    "missing_patterns": []
                }

        # Step 2: Pattern compliance
        compliance_score = 1.0
        if check_pattern_compliance:
            is_valid, compliance_score, pattern_errors, pattern_warnings = \
                self.parser.validate_godzilla_pattern(code)
            errors.extend(pattern_errors)
            warnings.extend(pattern_warnings)

        # Step 3: Extract missing patterns
        if check_pattern_compliance:
            missing_patterns = [e for e in errors if "Missing" in e]

        # Step 4: Generate suggestions
        suggestions = self._generate_suggestions(code, errors, warnings)

        # Step 5: Determine validity
        is_valid = len(errors) == 0 or compliance_score >= 0.8

        logger.info(
            "Code validation complete",
            is_valid=is_valid,
            compliance_score=compliance_score,
            error_count=len(errors),
            warning_count=len(warnings)
        )

        return {
            "is_valid": is_valid,
            "syntax_errors": [e for e in errors if "Syntax" in e],
            "pattern_compliance": compliance_score,
            "warnings": warnings,
            "suggestions": suggestions,
            "missing_patterns": missing_patterns
        }

    def _generate_suggestions(
        self,
        code: str,
        errors: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Generate improvement suggestions based on validation results."""
        suggestions = []

        # Check for common issues
        if "Flow[State]" not in code:
            suggestions.append("Use Flow[AgentState] as base class for type safety")

        if "@start()" not in code:
            suggestions.append("Add @start() decorator to mark entry point")

        if "@listen(" not in code:
            suggestions.append("Add @listen() decorators for event-driven transitions")

        if "try:" not in code:
            suggestions.append("Add try/except blocks for error handling")

        if "logger." not in code:
            suggestions.append("Add structlog for structured logging")

        if "async def" not in code:
            suggestions.append("Consider using async methods for better performance")

        if "@router(" not in code:
            suggestions.append("Consider adding @router() for conditional branching")

        return suggestions

    def quick_validate(self, code: str) -> bool:
        """Quick validation check (syntax only)."""
        try:
            ast.parse(code)
            return True
        except:
            return False

    def extract_flow_info(self, code: str) -> Dict[str, Any]:
        """Extract information about the flow structure."""
        classes = self.parser.extract_classes(code)
        functions = self.parser.extract_functions(code)
        decorators = self.parser.detect_decorators(code)

        flow_class = None
        for cls in classes:
            if "Flow" in cls.get("bases", []):
                flow_class = cls
                break

        return {
            "flow_class": flow_class,
            "total_classes": len(classes),
            "total_functions": len(functions),
            "decorators": decorators,
            "async_functions": sum(1 for f in functions if f.get("is_async"))
        }


# Global service instance
_validator: Optional[CodeValidator] = None


def get_validator() -> CodeValidator:
    """Get or create validator instance."""
    global _validator
    if _validator is None:
        _validator = CodeValidator()
    return _validator
