import os

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev")

settings = Settings()
