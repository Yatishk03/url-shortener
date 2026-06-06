from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    url: str  # The long URL to shorten


class ShortenResponse(BaseModel):
    short_code: str
    short_url:  str
    original:   str


class StatsResponse(BaseModel):
    short_code: str
    original:   str
    hit_count:  int