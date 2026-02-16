"""
AI & Machine Learning Tools Configuration

Tools for AI-powered operations, code interpretation, and RAG.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class AIToolsConfig:
    """Configuration for AI & Machine Learning tools."""

    # DALL-E settings
    dalle_model: str = "dall-e-3"  # dall-e-2, dall-e-3
    dalle_image_size: str = "1024x1024"  # 256x256, 512x512, 1024x1024
    dalle_quality: str = "standard"  # standard, hd
    dalle_style: str = "vivid"  # vivid, natural

    # Vision settings
    vision_model: str = "gpt-4o"  # gpt-4o, gpt-4-turbo
    vision_max_tokens: int = 1000

    # Code Interpreter settings
    code_timeout: int = 60  # seconds
    code_max_output_size: int = 10000  # characters
    code_allowed_modules: List[str] = field(default_factory=lambda: [
        "math", "random", "datetime", "json", "re", "collections",
        "itertools", "functools", "statistics", "decimal", "fractions"
    ])

    # RAG settings
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 5

    # LangChain settings
    langchain_verbose: bool = False

    # LlamaIndex settings
    llamacloud_api_key: Optional[str] = None

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
        """Get all AI & Machine Learning tool configurations."""
        return [
            # Image Generation
            ToolConfig(
                name="DallETool",
                import_path="crewai_tools.DallETool",
                category=ToolCategory.AI_ML,
                description="Generate images with DALL-E",
                required_env_vars=["OPENAI_API_KEY"],
            ),
            ToolConfig(
                name="StableDiffusionTool",
                import_path="crewai_tools.StableDiffusionTool",
                category=ToolCategory.AI_ML,
                description="Generate images with Stable Diffusion",
                required_env_vars=["STABILITY_API_KEY"],
            ),
            ToolConfig(
                name="MidjourneyTool",
                import_path="crewai_tools.MidjourneyTool",
                category=ToolCategory.AI_ML,
                description="Generate images with Midjourney",
                required_env_vars=["MIDJOURNEY_TOKEN"],
            ),

            # Vision
            ToolConfig(
                name="VisionTool",
                import_path="crewai_tools.VisionTool",
                category=ToolCategory.AI_ML,
                description="Computer vision with AI models",
                required_env_vars=["OPENAI_API_KEY"],
            ),
            ToolConfig(
                name="CLIPSearchTool",
                import_path="crewai_tools.CLIPSearchTool",
                category=ToolCategory.AI_ML,
                description="Search images with CLIP embeddings",
                dependencies=["clip"],
            ),

            # Code Execution
            ToolConfig(
                name="CodeInterpreterTool",
                import_path="crewai_tools.CodeInterpreterTool",
                category=ToolCategory.AI_ML,
                description="Execute Python code safely",
            ),
            ToolConfig(
                name="E2BCodeInterpreterTool",
                import_path="crewai_tools.E2BCodeInterpreterTool",
                category=ToolCategory.AI_ML,
                description="Execute code in E2B sandbox",
                required_env_vars=["E2B_API_KEY"],
                dependencies=["e2b-code-interpreter"],
            ),

            # RAG & Embeddings
            ToolConfig(
                name="RagTool",
                import_path="crewai_tools.RagTool",
                category=ToolCategory.AI_ML,
                description="Retrieval-Augmented Generation",
                dependencies=["langchain", "chromadb"],
            ),
            ToolConfig(
                name="LlamaIndexTool",
                import_path="crewai_tools.LlamaIndexTool",
                category=ToolCategory.AI_ML,
                description="LlamaIndex integration for RAG",
                dependencies=["llama-index"],
            ),
            ToolConfig(
                name="SemanticSearchTool",
                import_path="crewai_tools.SemanticSearchTool",
                category=ToolCategory.AI_ML,
                description="Semantic search with embeddings",
                dependencies=["sentence-transformers"],
            ),

            # Framework Integrations
            ToolConfig(
                name="LangchainTool",
                import_path="crewai_tools.LangchainTool",
                category=ToolCategory.AI_ML,
                description="Use LangChain tools in CrewAI",
                dependencies=["langchain"],
            ),
            ToolConfig(
                name="LlamaIndexRagTool",
                import_path="crewai_tools.LlamaIndexRagTool",
                category=ToolCategory.AI_ML,
                description="RAG with LlamaIndex",
                dependencies=["llama-index"],
            ),

            # Model Hubs
            ToolConfig(
                name="HuggingFaceSearchTool",
                import_path="crewai_tools.HuggingFaceSearchTool",
                category=ToolCategory.AI_ML,
                description="Search Hugging Face models and datasets",
                dependencies=["huggingface-hub"],
            ),
            ToolConfig(
                name="ReplicateTool",
                import_path="crewai_tools.ReplicateTool",
                category=ToolCategory.AI_ML,
                description="Run models on Replicate",
                required_env_vars=["REPLICATE_API_TOKEN"],
                dependencies=["replicate"],
            ),

            # Audio & Speech
            ToolConfig(
                name="WhisperTool",
                import_path="crewai_tools.WhisperTool",
                category=ToolCategory.AI_ML,
                description="Transcribe audio with Whisper",
                required_env_vars=["OPENAI_API_KEY"],
            ),
            ToolConfig(
                name="TTSTool",
                import_path="crewai_tools.TTSTool",
                category=ToolCategory.AI_ML,
                description="Text-to-speech synthesis",
                required_env_vars=["OPENAI_API_KEY"],
            ),
            ToolConfig(
                name="ElevenLabsTTSTool",
                import_path="crewai_tools.ElevenLabsTTSTool",
                category=ToolCategory.AI_ML,
                description="TTS with ElevenLabs",
                required_env_vars=["ELEVENLABS_API_KEY"],
            ),
        ]

    def get_ai_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
        """
        Get instantiated AI tools.

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

    def get_dalle_config(self) -> Dict[str, Any]:
        """Get DALL-E configuration."""
        return {
            "model": self.dalle_model,
            "size": self.dalle_image_size,
            "quality": self.dalle_quality,
            "style": self.dalle_style,
        }

    def get_rag_config(self) -> Dict[str, Any]:
        """Get RAG configuration."""
        return {
            "chunk_size": self.rag_chunk_size,
            "chunk_overlap": self.rag_chunk_overlap,
            "embedding_model": self.rag_embedding_model,
            "top_k": self.rag_top_k,
        }

    def get_code_interpreter_config(self) -> Dict[str, Any]:
        """Get Code Interpreter configuration."""
        return {
            "timeout": self.code_timeout,
            "max_output_size": self.code_max_output_size,
            "allowed_modules": self.code_allowed_modules,
        }
