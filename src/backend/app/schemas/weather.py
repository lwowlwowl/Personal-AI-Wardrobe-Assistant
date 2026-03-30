"""Pydantic models for weather APIs (shared with routes / future use)."""
from pydantic import BaseModel, ConfigDict, Field


class WeatherLatLonParams(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
