def generate_learner_context(request_data):
    # mock implementation for generating learner context
    print("Generating learner context with request data:", request_data)
    age, qualification, goals, challenges, description = "25, Bachelor's Degree, learn Python, time management, and a background in data analysis"
    return (
        f"{age}-year-old with {qualification}, aiming to {goals}. "
        f"Challenges: {challenges}. Background: {description}"
    )


def run_inference(conversation, learner_context=""):
    print("Running inference on:", conversation, learner_context)
    return {
        "explanation": "Response based on analysis of conversation.",
        "flashcard_contents": "summarative flashcard content",
    }
