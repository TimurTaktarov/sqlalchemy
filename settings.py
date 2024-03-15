import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_NAME = os.getenv('DATABASE_NAME', '')
    DATABASE_USER = os.getenv('DATABASE_USER', '')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
    DATABASE_HOST = os.getenv('DATABASE_HOST', '')
    DATABASE_PORT = os.getenv('DATABASE_PORT', '')

    SMTP_SERVER = os.getenv('SMTP_SERVER', '')
    EMAIL_TOKEN = os.getenv('EMAIL_TOKEN', '')
    EMAIL_USER = os.getenv('EMAIL_USER', '')

    JWT_SECRET = os.getenv('JWT_SECRET', '')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', '')
    REFRESH_TOKEN_TIME_MINUTES = 60 * 24  # one day
    ACCESS_TOKEN_TIME_MINUTES = 50

    @property
    def DATABASE_URL(self) -> str:
        return f'postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@' \
               f'{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}'


settings = Settings()
