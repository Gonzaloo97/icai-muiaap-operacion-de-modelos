from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Scope = Literal["predict", "admin"]


class ClientConfig(BaseModel):
    key: SecretStr = Field(min_length=1)
    scopes: list[Scope]
    rate_limit_per_minute: int = Field(default=60, gt=0, strict=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WINE_API_",
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    mode: Literal["ready", "unavailable"] = "ready"
    clients: dict[str, ClientConfig] = Field(default_factory=dict)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])
    docs_enabled: bool = True

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard(cls, origins: list[str]) -> list[str]:
        if any("*" in origin for origin in origins):
            raise ValueError("Los orígenes CORS deben ser explícitos")
        return origins
