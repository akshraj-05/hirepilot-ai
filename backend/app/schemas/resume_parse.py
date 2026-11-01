"""Structured resume parsing output (BD-02)."""

from pydantic import BaseModel, Field


class ParsedResume(BaseModel):
    skills: list[str] = Field(default_factory=list)
    experience: str = ""
    education: str = ""
    red_flags: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)