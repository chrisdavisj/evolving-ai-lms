from pydantic import BaseModel, Field
from typing import List, Optional


class Message(BaseModel):
    role: str = Field(..., example="user")
    message: str = Field(..., example="What is a neural network?")
    images: Optional[List[str]] = []


class InferenceRequest(BaseModel):
    conversation: List[Message]
    learner_context: str = Field(
        ..., example="I am a 25-year-old with a Bachelor's Degree, aiming to learn Python. Challenges: time management. Background: data analysis.")
