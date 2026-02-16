"""
Cloud & Storage Tools Configuration

Tools for cloud services including AWS, Azure, GCP, and storage.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class CloudToolsConfig:
    """Configuration for Cloud & Storage tools."""

    # AWS settings
    aws_region: str = "us-east-1"
    aws_s3_default_bucket: Optional[str] = None
    aws_s3_max_file_size: int = 100 * 1024 * 1024  # 100MB

    # Azure settings
    azure_container_name: Optional[str] = None

    # GCP settings
    gcp_project_id: Optional[str] = None
    gcp_bucket_name: Optional[str] = None

    # Cloudflare R2 settings
    r2_account_id: Optional[str] = None
    r2_bucket_name: Optional[str] = None

    # Amazon Bedrock settings
    bedrock_region: str = "us-east-1"
    bedrock_default_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
        """Get all Cloud & Storage tool configurations."""
        return [
            # AWS S3
            ToolConfig(
                name="S3ReaderTool",
                import_path="crewai_tools.S3ReaderTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Read files from AWS S3",
                required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                dependencies=["boto3"],
            ),
            ToolConfig(
                name="S3WriterTool",
                import_path="crewai_tools.S3WriterTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Write files to AWS S3",
                required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                dependencies=["boto3"],
            ),

            # Amazon AI Services
            ToolConfig(
                name="AmazonBedrockTool",
                import_path="crewai_tools.AmazonBedrockTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Use Amazon Bedrock AI services",
                required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
                dependencies=["boto3"],
            ),
            ToolConfig(
                name="TextractTool",
                import_path="crewai_tools.TextractTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Extract text from documents with AWS Textract",
                required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                dependencies=["boto3"],
            ),
            ToolConfig(
                name="RekognitionTool",
                import_path="crewai_tools.RekognitionTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Image analysis with AWS Rekognition",
                required_env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                dependencies=["boto3"],
            ),

            # Azure
            ToolConfig(
                name="AzureBlobStorageTool",
                import_path="crewai_tools.AzureBlobStorageTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Access Azure Blob Storage",
                required_env_vars=["AZURE_STORAGE_CONNECTION_STRING"],
                dependencies=["azure-storage-blob"],
            ),
            ToolConfig(
                name="AzureOpenAITool",
                import_path="crewai_tools.AzureOpenAITool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Use Azure OpenAI Service",
                required_env_vars=["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
                dependencies=["openai"],
            ),
            ToolConfig(
                name="AzureAISearchTool",
                import_path="crewai_tools.AzureAISearchTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Azure AI Search",
                required_env_vars=["AZURE_SEARCH_KEY", "AZURE_SEARCH_ENDPOINT"],
                dependencies=["azure-search-documents"],
            ),

            # Google Cloud
            ToolConfig(
                name="GCSTool",
                import_path="crewai_tools.GCSTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Access Google Cloud Storage",
                required_env_vars=["GOOGLE_APPLICATION_CREDENTIALS"],
                dependencies=["google-cloud-storage"],
            ),
            ToolConfig(
                name="BigQueryTool",
                import_path="crewai_tools.BigQueryTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Query Google BigQuery",
                required_env_vars=["GOOGLE_APPLICATION_CREDENTIALS"],
                dependencies=["google-cloud-bigquery"],
            ),
            ToolConfig(
                name="VertexAITool",
                import_path="crewai_tools.VertexAITool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Use Google Cloud Vertex AI",
                required_env_vars=["GOOGLE_APPLICATION_CREDENTIALS"],
                dependencies=["google-cloud-aiplatform"],
            ),

            # Other Cloud Storage
            ToolConfig(
                name="CloudflareR2Tool",
                import_path="crewai_tools.CloudflareR2Tool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Access Cloudflare R2 storage",
                required_env_vars=["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_ACCESS_KEY", "CLOUDFLARE_SECRET_KEY"],
                dependencies=["boto3"],
            ),
            ToolConfig(
                name="DropboxTool",
                import_path="crewai_tools.DropboxTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Access Dropbox files",
                required_env_vars=["DROPBOX_ACCESS_TOKEN"],
                dependencies=["dropbox"],
            ),
            ToolConfig(
                name="BoxTool",
                import_path="crewai_tools.BoxTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Access Box files",
                required_env_vars=["BOX_CLIENT_ID", "BOX_CLIENT_SECRET"],
                dependencies=["boxsdk"],
            ),
            ToolConfig(
                name="OneDriveTool",
                import_path="crewai_tools.OneDriveTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Access Microsoft OneDrive",
                required_env_vars=["ONEDRIVE_CLIENT_ID", "ONEDRIVE_CLIENT_SECRET"],
                dependencies=["msgraph-sdk"],
            ),

            # Cloud Deployment
            ToolConfig(
                name="VercelTool",
                import_path="crewai_tools.VercelTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Deploy to Vercel",
                required_env_vars=["VERCEL_TOKEN"],
            ),
            ToolConfig(
                name="RailwayTool",
                import_path="crewai_tools.RailwayTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Deploy to Railway",
                required_env_vars=["RAILWAY_TOKEN"],
            ),
            ToolConfig(
                name="RenderTool",
                import_path="crewai_tools.RenderTool",
                category=ToolCategory.CLOUD_STORAGE,
                description="Deploy to Render",
                required_env_vars=["RENDER_API_KEY"],
            ),
        ]

    def get_cloud_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
        """
        Get instantiated cloud tools.

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
                except Exception:
                    pass

        return tools

    def get_aws_config(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Get AWS configuration."""
        return {
            "aws_access_key_id": env_vars.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": env_vars.get("AWS_SECRET_ACCESS_KEY"),
            "region_name": env_vars.get("AWS_REGION", self.aws_region),
        }

    def get_bedrock_config(self) -> Dict[str, Any]:
        """Get Amazon Bedrock configuration."""
        return {
            "region": self.bedrock_region,
            "default_model": self.bedrock_default_model,
        }
