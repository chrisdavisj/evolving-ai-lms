from pydantic import BaseModel, Field
from typing import List, Optional


class Message(BaseModel):
    role: str = Field(..., example="user")
    message: str = Field(..., example="What is a neural network?")
    images: Optional[List[str]] = []


class InferenceRequest(BaseModel):
    conversation: List[Message]
