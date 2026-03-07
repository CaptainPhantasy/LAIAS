"""
Format conversion service for agent outputs.

Converts between content formats (e.g., Markdown to HTML) using mistune.
"""

from typing import Literal

import mistune

# =============================================================================
# Format Converter Service
# =============================================================================


class FormatConverter:
    """Stateless format converter with singleton access."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def convert(self, content: str, target_format: Literal["html", "markdown"]) -> str:
        """Convert content to the specified target format.

        Args:
            content: Source content (assumed Markdown).
            target_format: Target format — "html" or "markdown".

        Returns:
            Converted content string.

        Raises:
            ValueError: If target_format is not supported.
        """
        if target_format == "html":
            html_body = mistune.html(content)
            return (
                "<!DOCTYPE html>\n"
                "<html>\n"
                '<head><meta charset="utf-8">'
                "<style>body { font-family: system-ui; max-width: 800px;"
                " margin: 0 auto; padding: 20px; }</style></head>\n"
                f"<body>{html_body}</body>\n"
                "</html>"
            )
        elif target_format == "markdown":
            return content
        else:
            raise ValueError(f"Unsupported format: {target_format}")


# =============================================================================
# Singleton accessor
# =============================================================================

_format_converter: FormatConverter | None = None


def get_format_converter() -> FormatConverter:
    """Get the singleton FormatConverter instance."""
    global _format_converter
    if _format_converter is None:
        _format_converter = FormatConverter()
    return _format_converter
