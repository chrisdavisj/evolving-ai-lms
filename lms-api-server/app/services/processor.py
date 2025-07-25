import base64
import tempfile
from app.services.inference_functions import run_full_pipeline
from app.services.onboarding_functions import create_learner_context_using_llms


def generate_learner_context(request_data):
    print("Generating learner context with request data:", request_data)
    learner_model_context = create_learner_context_using_llms(request_data)
    return str(learner_model_context)


def summarize_conversation(conversation):
    summary = []
    for msg in conversation:
        summary.append(f"{msg.role.title()}: {msg.message}")
    return "\n".join(summary)


def run_inference(conversation, learner_context=""):
    print("Running inference on:", conversation, learner_context)
    if not conversation:
        return {"error": "No conversation history provided."}

    # Get the last user message
    last_user_message = next(
        (msg for msg in reversed(conversation) if msg.role == "user"), None)
    if not last_user_message:
        return {"error": "No user message found."}

    prompt = last_user_message.message.strip()
    image_data_base64 = (
        last_user_message.images[0] if last_user_message.images else None
    )

    if not prompt or not image_data_base64:
        return {"error": "Missing prompt or image."}

    if image_data_base64.startswith("data:image"):
        try:
            image_data_base64 = image_data_base64.split(",", 1)[1]
        except IndexError:
            return {"error": "Malformed image data."}

    # Decode image to temp file
    try:
        image_bytes = base64.b64decode(image_data_base64)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(image_bytes)
            image_path = temp_file.name
    except Exception as e:
        return {"error": f"Failed to decode image: {str(e)}"}

    # Build contextual learner summary from full conversation
    conversation_summary = summarize_conversation(conversation)
    full_context = f"""Conversation Summary:
{conversation_summary}

Learner Profile:
{learner_context}
"""

    narrative, flashcard = run_full_pipeline(image_path, prompt, full_context)

    if not narrative:
        return {"error": "Narrative generation failed."}

    return {
        "explanation": narrative,
        "flashcard_contents": flashcard or "Flashcard generation failed."
    }
