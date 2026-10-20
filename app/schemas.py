"""Pydantic schemas for request/response validation."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
RESERVED_CODES = {"api", "health", "docs", "openapi.json", "redoc"}


class LinkCreate(BaseModel):
    original_url: str = Field(..., min_length=1, max_length=2048, examples=["https://example.com/a/very/long/url"])
    custom_alias: str | None = Field(default=None, description="Optional custom alias (3-30 chars: letters, digits, '-' or '_')")
    expires_at: datetime | None = Field(default=None, description="Optional expiration date (ISO 8601, UTC)")

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("original_url must start with http:// or https://")
        if "." not in value.split("//", 1)[-1].split("/", 1)[0]:
            raise ValueError("original_url must contain a valid host")
        return value

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not ALIAS_PATTERN.match(value):
            raise ValueError("custom_alias must be 3-30 characters: letters, digits, '-' or '_'")
        if value.lower() in RESERVED_CODES:
            raise ValueError("custom_alias is reserved")
        return value


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    original_url: str
    is_custom_alias: bool
    click_count: int
    created_at: datetime
    last_accessed_at: datetime | None = None
    expires_at: datetime | None = None


class LinkStatsResponse(LinkResponse):
    is_expired: bool = False
