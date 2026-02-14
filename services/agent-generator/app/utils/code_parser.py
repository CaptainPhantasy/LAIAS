"""
Code parsing utilities for Agent Generator Service.

Provides AST-based code analysis and validation.
"""

import ast
import re
from typing import List, Tuple, Optional, Dict, Any


class CodeParser:
    """
    Parser for analyzing and validating Python code.

    Uses AST for syntax analysis and regex for pattern matching.
    """

    def __init__(self):
        """Initialize the parser with validation rules."""
        self.required_patterns = [
            (r"class \w+\(Flow\[", "Must use Flow[State] base class"),
            (r"@start\(\)", "Must have @start() decorated entry point"),
            (r"@listen\(", "Must have @listen() event-driven methods"),
            (r"class \w+State\(BaseModel\)", "Must define typed state class with BaseModel"),
            (r"def _create_\w+_agent\(self\)", "Must have agent factory methods"),
            (r"try:", "Must include error handling (try/except)"),
            (r"logger\.", "Must use structlog logging"),
            (r"self\.state\.", "Must use typed state management"),
        ]

        self.recommended_patterns = [
            (r"@router\(", "Consider adding @router() for conditional branching"),
            (r"AnalyticsService", "Consider adding analytics for monitoring"),
            (r"async def", "Consider using async methods for better performance"),
            (r"@persist", "Consider adding @persist for state persistence"),
        ]

    def parse(self, code: str) -> Optional[ast.Module]:
        """
        Parse Python code into AST.

        Args:
            code: Python source code

        Returns:
            AST module or None if parsing fails
        """
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    def validate_syntax(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate Python syntax.

        Args:
            code: Python source code

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Parse error: {str(e)}")

        return len(errors) == 0, errors

    def validate_godzilla_pattern(self, code: str) -> Tuple[bool, float, List[str], List[str]]:
        """
        Validate code against Godzilla architectural pattern.

        Args:
            code: Python source code

        Returns:
            Tuple of (is_valid, compliance_score, errors, warnings)
        """
        errors = []
        warnings = []

        # First, check syntax
        is_valid_syntax, syntax_errors = self.validate_syntax(code)
        if not is_valid_syntax:
            return False, 0.0, syntax_errors, []

        # Check required patterns
        patterns_found = 0
        for pattern, error_msg in self.required_patterns:
            if re.search(pattern, code):
                patterns_found += 1
            else:
                errors.append(f"Missing required pattern: {error_msg}")

        # Check recommended patterns (warnings only)
        for pattern, warning_msg in self.recommended_patterns:
            if not re.search(pattern, code):
                warnings.append(f"Recommended: {warning_msg}")

        # Calculate compliance score
        compliance_score = patterns_found / len(self.required_patterns)

        # Valid if no critical errors and compliance >= 80%
        is_valid = len(errors) == 0 or compliance_score >= 0.8

        return is_valid, compliance_score, errors, warnings

    def extract_imports(self, code: str) -> Dict[str, List[str]]:
        """
        Extract import statements from code.

        Args:
            code: Python source code

        Returns:
            Dictionary with 'imports' and 'from_imports' keys
        """
        imports = {"import": [], "from_import": []}

        tree = self.parse(code)
        if not tree:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports["import"].append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports["from_import"].append(node.module.split(".")[0])

        return imports

    def extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract class definitions from code.

        Args:
            code: Python source code

        Returns:
            List of class info dictionaries
        """
        classes = []
        tree = self.parse(code)
        if not tree:
            return classes

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(base) for base in node.bases]
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]

                classes.append({
                    "name": node.name,
                    "bases": bases,
                    "methods": methods,
                    "lineno": node.lineno
                })

        return classes

    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract function definitions from code.

        Args:
            code: Python source code

        Returns:
            List of function info dictionaries
        """
        functions = []
        tree = self.parse(code)
        if not tree:
            return functions

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "lineno": node.lineno,
                    "is_async": False
                })
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "lineno": node.lineno,
                    "is_async": True
                })

        return functions

    def detect_decorators(self, code: str) -> Dict[str, List[str]]:
        """
        Detect CrewAI Flow decorators in code.

        Args:
            code: Python source code

        Returns:
            Dictionary mapping decorators to decorated methods
        """
        decorators = {
            "@start": [],
            "@listen": [],
            "@router": [],
            "@persist": []
        }

        tree = self.parse(code)
        if not tree:
            return decorators

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    decorator_name = ast.unparse(decorator)
                    for key in decorators:
                        if key in decorator_name:
                            decorators[key].append(node.name)

        return decorators

    def estimate_complexity(self, code: str) -> Dict[str, int]:
        """
        Estimate code complexity metrics.

        Args:
            code: Python source code

        Returns:
            Dictionary with complexity metrics
        """
        tree = self.parse(code)
        if not tree:
            return {}

        classes = 0
        functions = 0
        async_functions = 0
        imports = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes += 1
            elif isinstance(node, ast.FunctionDef):
                functions += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                async_functions += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports += 1

        return {
            "classes": classes,
            "functions": functions,
            "async_functions": async_functions,
            "imports": imports,
            "total_functions": functions + async_functions
        }


# Convenience functions
def parse_python_code(code: str) -> Optional[ast.Module]:
    """Parse Python code into AST."""
    parser = CodeParser()
    return parser.parse(code)


def validate_godzilla(code: str) -> Tuple[bool, float, List[str], List[str]]:
    """Validate code against Godzilla pattern."""
    parser = CodeParser()
    return parser.validate_godzilla_pattern(code)
