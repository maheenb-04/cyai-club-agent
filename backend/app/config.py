from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    mistral_api_key: str = ""
    tavily_api_key: str = ""
    gmail_address: str = ""
    gmail_app_password: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""
    database_url: str = "sqlite:///./cyai_agent.db"
    supabase_database_url: str = ""
    token_secret_key: str = ""
    agent_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
