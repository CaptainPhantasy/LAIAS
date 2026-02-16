"""
File & Document Tools Configuration

Tools for reading, writing, and searching various file formats.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class FileToolsConfig:
    """Configuration for File & Document tools."""

    # Base paths for file operations
    allowed_directories: List[str] = field(default_factory=lambda: ["./data", "./workspace"])
    max_file_size_mb: int = 100
    allowed_extensions: List[str] = field(default_factory=lambda: [
        ".txt", ".pdf", ".docx", ".doc", ".xlsx", ".xls",
        ".csv", ".json", ".xml", ".md", ".html", ".rtf"
    ])

    # PDF settings
    pdf_extract_images: bool = False
    pdf_ocr_enabled: bool = False

    # CSV/Excel settings
    csv_encoding: str = "utf-8"
    csv_delimiter: str = ","
    excel_max_rows: int = 100000

    # JSON settings
    json_max_depth: int = 10

    # XML settings
    xml_remove_namespaces: bool = True

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
        """Get all File & Document tool configurations."""
        return [
            ToolConfig(
                name="FileReadTool",
                import_path="crewai_tools.FileReadTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Read content from various file formats",
                dependencies=["pypdf", "python-docx"],
                default_config={
                    "max_file_size": 100 * 1024 * 1024,  # 100MB
                }
            ),
            ToolConfig(
                name="FileWriteTool",
                import_path="crewai_tools.FileWriteTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Write content to files",
            ),
            ToolConfig(
                name="DirectoryReadTool",
                import_path="crewai_tools.DirectoryReadTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Read and list directory contents",
            ),
            ToolConfig(
                name="DirectorySearchTool",
                import_path="crewai_tools.DirectorySearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search for files within directories",
            ),
            ToolConfig(
                name="CSVSearchTool",
                import_path="crewai_tools.CSVSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search and query CSV files",
                dependencies=["pandas"],
            ),
            ToolConfig(
                name="JSONSearchTool",
                import_path="crewai_tools.JSONSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search and query JSON files",
            ),
            ToolConfig(
                name="XMLSearchTool",
                import_path="crewai_tools.XMLSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search and query XML files",
                dependencies=["lxml"],
            ),
            ToolConfig(
                name="PDFSearchTool",
                import_path="crewai_tools.PDFSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search and extract content from PDF files",
                dependencies=["pypdf"],
            ),
            ToolConfig(
                name="DocxSearchTool",
                import_path="crewai_tools.DocxSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search and extract content from DOCX files",
                dependencies=["python-docx"],
            ),
            ToolConfig(
                name="ExcelSearchTool",
                import_path="crewai_tools.ExcelSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search and query Excel files",
                dependencies=["openpyxl", "pandas"],
            ),
            ToolConfig(
                name="MDXSearchTool",
                import_path="crewai_tools.MDXSearchTool",
                category=ToolCategory.FILE_DOCUMENT,
                description="Search MDX documentation files",
            ),
        ]

    def get_file_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
        """
        Get instantiated file tools.

        Args:
            env_vars: Environment variables for configuration

        Returns:
            List of tool instances
        """
        from app.tools.registry import get_tool_registry

        registry = get_tool_registry()
        env = env_vars or dict(os.environ)

        tools = []
        for config in self.get_tool_configs():
            if config.is_available(env):
                try:
                    tool = registry.instantiate_tool(config.name)
                    tools.append(tool)
                except Exception as e:
                    # Log but continue with other tools
                    pass

        return tools

    def is_file_allowed(self, filepath: str) -> bool:
        """Check if a file path is allowed based on config."""
        # Check extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self.allowed_extensions:
            return False

        # Check directory
        abs_path = os.path.abspath(filepath)
        for allowed_dir in self.allowed_directories:
            allowed_abs = os.path.abspath(allowed_dir)
            if abs_path.startswith(allowed_abs):
                return True

        return False
