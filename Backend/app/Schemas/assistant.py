from pydantic import BaseModel, Field


class AssistantMessage(BaseModel):
    """A deliberately small request payload for the local SCNA assistant."""

    message: str = Field(min_length=1, max_length=500)


class AssistantResponse(BaseModel):
    answer: str
    source: str
    link: str | None = None
