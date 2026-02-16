from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    keeping all config here.
    """

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'memvec'
    app_env: str = 'dev'

    db_host: str = '127.0.0.1'
    db_port: int = 3306
    db_name: str = 'memvec'
    db_user: str = 'root'
    db_password: str = 'root'

    ollama_base_url: str = 'http://localhost:11434'
    ollama_model: str = 'qwen2.5:3b-instruct'

    use_llm_qualifier: bool = True

    LOG_LEVEL: str = 'DEBUG'
    LOG_FORMAT: str = 'text'
    LOG_SQLALCHEMY: bool = False
    APP_NAME: str = 'app'
    ENV: str = 'local'

    qdrant_url: str = 'http://localhost:6333'
    qdrant_collection: str = 'memories'
    qdrant_vector_dim: int = 32
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'

    nebula_host: str = '127.0.0.1'
    nebula_port: int = 9669
    nebula_user: str = 'root'
    nebula_password: str = 'nebula'
    nebula_space: str = 'memkg'
    nebula_vid_len: int = 256

    @property
    def database_url(self) -> str:
        return (
            f'mysql+mysqlconnector://{self.db_user}:{self.db_password}'
            f'@{self.db_host}:{self.db_port}/{self.db_name}'
        )


settings = Settings()
