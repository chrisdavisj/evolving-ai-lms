from fastapi import APIRouter, HTTPException
from app.models.onboarding import OnboardingRequest
from app.services.processor import generate_learner_context

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/")
async def onboarding(request: OnboardingRequest):
    try:
        context = generate_learner_context(request)
        return {"learnerContext": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
