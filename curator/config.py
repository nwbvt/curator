from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Configuration settings for the Curator application.
    """
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Database settings
    db_url: str = 'sqlite:///./curator.db'

    # Logging settings
    log_level: str = 'INFO'

settings = Settings()