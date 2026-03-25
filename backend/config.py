"""
EcoLens — Application Configuration
Loaded once at startup via pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = Field("development", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_service_key: str = Field(..., alias="SUPABASE_SERVICE_KEY")

    # Storage buckets
    scan_results_bucket: str = Field("scan-results", alias="SCAN_RESULTS_BUCKET")
    heatmaps_bucket: str = Field("heatmaps", alias="HEATMAPS_BUCKET")

    # Classifier confidence threshold
    classifier_conf: float = Field(0.20, alias="CLASSIFIER_CONF")

    # Security
    max_image_size_mb: int = Field(10, alias="MAX_IMAGE_SIZE_MB")
    analyze_rate_limit: str = Field("30/minute", alias="ANALYZE_RATE_LIMIT")
    max_ws_connections: int = Field(4, alias="MAX_WS_CONNECTIONS")

    @property
    def max_image_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024


settings = Settings()
