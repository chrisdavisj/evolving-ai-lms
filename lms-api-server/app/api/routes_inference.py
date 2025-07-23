from fastapi import APIRouter, HTTPException
from app.models.inference import InferenceRequest
from app.services.processor import run_inference

router = APIRouter(prefix="/inference", tags=["Inference"])


@router.post("/")
async def inference(request: InferenceRequest):
    try:
        result = run_inference(request.conversation, request.learner_context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
