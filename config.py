from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str
    
    # OpenAI
    openai_api_key: str
    
    # JWT (get this from your Supabase project settings)
    jwt_secret: str
    
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

