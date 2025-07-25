from app.services.ollama_interface import chat_with_model


def create_learner_context_using_llms(request_data):
    system_prompt = (
        "You are an expert in learning sciences and adaptive instruction. "
        "Your task is to generate a pedagogically grounded learner model based on onboarding data. "
        "This model will guide downstream personalization of learning materials."
    )

    user_prompt = f"""\
### Onboarding Data

- Age: {request_data.age}
- Qualification: {request_data.qualification}
- Goals: {request_data.goals}
- Challenges: {request_data.challenges}
- Background: {request_data.description}

### Instructions

Based on the above, generate a structured JSON object describing the learner using the following keys:

- `profile_summary`: A short paragraph summarizing the learner’s situation, motivation, and background.
- `strengths`: What prior knowledge, skills, or attitudes may help this learner succeed?
- `barriers`: What challenges, gaps, or misconceptions may limit their learning?
- `preferred_style`: Inferred learning preferences or instructional approaches likely to resonate (e.g. visual, structured steps, relevance to career).
- `instructional_goals`: What should the tutor aim for in how it explains and supports this learner?

Respond only in this **exact JSON format**:
```json
{{
  "profile_summary": "...",
  "strengths": "...",
  "barriers": "...",
  "preferred_style": "...",
  "instructional_goals": "..."
}}
```"""

    res = chat_with_model(
        model_name="mistral-small3.2:latest-64k",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    import json
    import re

    try:
        raw = res["message"]["content"]
        cleaned = re.sub(r"```json|```", "", raw).strip()
        return json.loads(cleaned)
    except Exception as e:
        print("Error parsing learner context:", e)
        return {
            "profile_summary": "A motivated learner.",
            "strengths": "Unknown",
            "barriers": "Unknown",
            "preferred_style": "Unknown",
            "instructional_goals": "Support with adaptive strategies."
        }
