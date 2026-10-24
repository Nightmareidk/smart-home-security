from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings come from environment variables that start with HOME_ (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="HOME_", extra="ignore")

    env: str = "dev"
    api_token: str = "change-me"
    cors_origins: list[str] = []
    rate_limit_per_minute: int = 60

    mqtt_enabled: bool = True
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None

    db_path: str = "data/home.db"
    reading_store_interval: float = 10.0

    # Mold risk: damp and warm for long enough. Short on purpose so it can be shown in a demo.
    mold_humidity_min: float = 70.0
    mold_temp_min: float = 20.0
    mold_temp_max: float = 30.0
    mold_hold_seconds: float = 120.0

    soil_dry_pct: float = 25.0
    gas_alert_level: float = 60.0
    camera_min_confidence: float = 0.6

    failed_unlock_limit: int = 3
    failed_unlock_window: float = 60.0
    alert_cooldown: float = 60.0
    present_timeout: float = 600.0

    @model_validator(mode="after")
    def _token_must_be_set_outside_dev(self):
        if self.env != "dev" and self.api_token in ("", "change-me"):
            raise ValueError("Set HOME_API_TOKEN to a long random value when HOME_ENV is not 'dev'.")
        return self
