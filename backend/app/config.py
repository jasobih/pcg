
from pydantic import BaseModel
from typing import List

class Settings(BaseModel):
    MAIL_USERNAME: str = "user@example.com"
    MAIL_PASSWORD: str = "password"
    MAIL_FROM: str = "user@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

settings = Settings()
