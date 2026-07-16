from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    # LLM Configuration
    llm_api_key: str = Field(default="", env="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", env="LLM_BASE_URL")
    llm_model: str = Field(default="gpt-4o-mini", env="LLM_MODEL")
    llm_heavy_model: str = Field(default="gpt-4o", env="LLM_HEAVY_MODEL")

    # External API Keys
    semantic_scholar_api_key: str = Field(default="", env="SEMANTIC_SCHOLAR_API_KEY")
    ncbi_api_key: str = Field(default="", env="NCBI_API_KEY")

    # App Settings
    max_papers_per_source: int = Field(default=25, env="MAX_PAPERS_PER_SOURCE")
    max_concurrent_summaries: int = Field(default=5, env="MAX_CONCURRENT_SUMMARIES")
    db_path: str = Field(default="./qora.db", env="DB_PATH")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
