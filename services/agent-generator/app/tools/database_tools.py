"""
Database & Data Tools Configuration

Tools for SQL databases, vector stores, and data warehouses.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os

from app.tools.registry import ToolCategory, ToolConfig


@dataclass
class DatabaseToolsConfig:
    """Configuration for Database & Data tools."""

    # General database settings
    query_timeout: int = 30
    max_rows: int = 1000
    connection_pool_size: int = 5

    # PostgreSQL settings
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_ssl_mode: str = "prefer"

    # MySQL settings
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_charset: str = "utf8mb4"

    # MongoDB settings
    mongo_max_pool_size: int = 100
    mongo_min_pool_size: int = 10

    # Vector DB settings
    vector_embedding_model: str = "text-embedding-3-small"
    vector_dimensions: int = 1536
    vector_distance_metric: str = "cosine"  # cosine, euclidean, dot_product

    # Qdrant settings
    qdrant_collection_name: str = "laias_vectors"

    # Weaviate settings
    weaviate_class_name: str = "Document"

    # Pinecone settings
    pinecone_index_name: str = "laias-index"

    @staticmethod
    def get_tool_configs() -> List[ToolConfig]:
        """Get all Database & Data tool configurations."""
        return [
            # SQL Databases
            ToolConfig(
                name="MySQLSearchTool",
                import_path="crewai_tools.MySQLSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Query MySQL databases",
                required_env_vars=["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"],
                dependencies=["mysql-connector-python"],
            ),
            ToolConfig(
                name="PGSearchTool",
                import_path="crewai_tools.PGSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Query PostgreSQL databases",
                required_env_vars=["PG_HOST", "PG_USER", "PG_PASSWORD", "PG_DATABASE"],
                dependencies=["psycopg2-binary"],
            ),
            ToolConfig(
                name="SnowflakeSearchTool",
                import_path="crewai_tools.SnowflakeSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Query Snowflake data warehouse",
                required_env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"],
                dependencies=["snowflake-connector-python"],
            ),
            ToolConfig(
                name="SQLiteSearchTool",
                import_path="crewai_tools.SQLiteSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Query SQLite databases",
            ),
            ToolConfig(
                name="MSSQLSearchTool",
                import_path="crewai_tools.MSSQLSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Query Microsoft SQL Server",
                required_env_vars=["MSSQL_HOST", "MSSQL_USER", "MSSQL_PASSWORD", "MSSQL_DATABASE"],
                dependencies=["pyodbc"],
            ),

            # NoSQL Databases
            ToolConfig(
                name="MongoDBSearchTool",
                import_path="crewai_tools.MongoDBSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Query MongoDB databases",
                required_env_vars=["MONGODB_URI"],
                dependencies=["pymongo"],
            ),
            ToolConfig(
                name="RedisSearchTool",
                import_path="crewai_tools.RedisSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Search Redis with RedisSearch",
                required_env_vars=["REDIS_URL"],
                dependencies=["redis"],
            ),
            ToolConfig(
                name="ElasticsearchSearchTool",
                import_path="crewai_tools.ElasticsearchSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Search Elasticsearch",
                required_env_vars=["ELASTICSEARCH_URL"],
                dependencies=["elasticsearch"],
            ),

            # Vector Databases
            ToolConfig(
                name="QdrantVectorSearchTool",
                import_path="crewai_tools.QdrantVectorSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with Qdrant",
                required_env_vars=["QDRANT_URL"],
                optional_env_vars=["QDRANT_API_KEY"],
                dependencies=["qdrant-client"],
            ),
            ToolConfig(
                name="WeaviateVectorSearchTool",
                import_path="crewai_tools.WeaviateVectorSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with Weaviate",
                required_env_vars=["WEAVIATE_URL"],
                optional_env_vars=["WEAVIATE_API_KEY"],
                dependencies=["weaviate-client"],
            ),
            ToolConfig(
                name="PineconeQueryTool",
                import_path="crewai_tools.PineconeQueryTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with Pinecone",
                required_env_vars=["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"],
                dependencies=["pinecone-client"],
            ),
            ToolConfig(
                name="ChromaDBSearchTool",
                import_path="crewai_tools.ChromaDBSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with ChromaDB",
                dependencies=["chromadb"],
            ),
            ToolConfig(
                name="MilvusSearchTool",
                import_path="crewai_tools.MilvusSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with Milvus",
                required_env_vars=["MILVUS_HOST", "MILVUS_PORT"],
                dependencies=["pymilvus"],
            ),
            ToolConfig(
                name="AstraDBSearchTool",
                import_path="crewai_tools.AstraDBSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with DataStax Astra",
                required_env_vars=["ASTRA_DB_ID", "ASTRA_TOKEN"],
                dependencies=["astrapy"],
            ),
            ToolConfig(
                name="MongoDBVectorSearchTool",
                import_path="crewai_tools.MongoDBVectorSearchTool",
                category=ToolCategory.DATABASE_DATA,
                description="Vector search with MongoDB Atlas",
                required_env_vars=["MONGODB_URI"],
                dependencies=["pymongo"],
            ),
        ]

    def get_database_tools(self, env_vars: Optional[Dict[str, str]] = None) -> List[Any]:
        """
        Get instantiated database tools.

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

    def get_postgres_connection_string(self, env_vars: Dict[str, str]) -> str:
        """Build PostgreSQL connection string."""
        host = env_vars.get("PG_HOST", self.pg_host)
        port = env_vars.get("PG_PORT", str(self.pg_port))
        user = env_vars.get("PG_USER", "")
        password = env_vars.get("PG_PASSWORD", "")
        database = env_vars.get("PG_DATABASE", "")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def get_mysql_connection_string(self, env_vars: Dict[str, str]) -> str:
        """Build MySQL connection string."""
        host = env_vars.get("MYSQL_HOST", self.mysql_host)
        port = env_vars.get("MYSQL_PORT", str(self.mysql_port))
        user = env_vars.get("MYSQL_USER", "")
        password = env_vars.get("MYSQL_PASSWORD", "")
        database = env_vars.get("MYSQL_DATABASE", "")

        return f"mysql://{user}:{password}@{host}:{port}/{database}"
