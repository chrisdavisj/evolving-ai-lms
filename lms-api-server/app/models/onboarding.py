from pydantic import BaseModel, Field


class OnboardingRequest(BaseModel):
    age: str = Field(..., example="30")
    qualification: str = Field(..., example="Bachelor's Degree")
    goals: str = Field(..., example="Become a data analyst")
    challenges: str = Field(..., example="No programming experience")
    description: str = Field(..., example="Worked in retail for 5 years...")
