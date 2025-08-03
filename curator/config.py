from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration settings for the Curator application.
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

    # Database settings
    db_url: str = 'sqlite:///./curator.db'
    db_echo: bool = False
    chroma_path: str = './curator.chroma'

    # Logging settings
    log_level: str = 'INFO'

    # LLM settings
    description_model: str = 'gemma3:4b'
    use_ollama: bool = True
    device: str = 'cuda'  # Default to GPU if available

    # Scheduler settings
    scheduler_interval: int = 3600  # Default to 1 hour

settings = Settings()