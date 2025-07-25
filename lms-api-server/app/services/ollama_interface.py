from ollama import Client
import base64
from pathlib import Path
import concurrent.futures
import time


OLLAMA_HOST = "10.1.1.56:9007"

client = Client(host=OLLAMA_HOST)


def get_ollama_models():
    models_info = client.list()

    models = [model.model for model in models_info.models]
    return models


DEFAULT_OPTIONS = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": -1,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "repeat_penalty": 1.1,
    "stop": [],
    "seed": None,
}


def chat_with_model(model_name, messages, options=None, image_paths=None, stream=False, timeout=20 * 60):
    """
    Wrapper for chatting with an Ollama model, supporting optional image input, streaming, and default options.

    Args:
        model_name (str): One of the supported models.
        messages (list): List of dicts, each with "role" and "content" keys.
                         Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        options (dict, optional): Inference options such as:
            - temperature (float): Sampling temperature (e.g., 0.7)
            - top_p (float): Nucleus sampling parameter (e.g., 0.9)
            - presence_penalty, frequency_penalty, stop, mirostat, etc.
            Full list here: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-request-with-options
        image_paths (list of str, optional): Local image paths (for multimodal models). (Images are added to the last message in chat)
        stream (bool): If True, yields tokens incrementally.
        timeout (int): Timeout in seconds for the response (non-stream mode only).

    Returns:
        If stream=True: yields str tokens.
        If stream=False: dict: Full response object with the following keys:

            {
                'model': str,                # Model used (e.g., "phi4-mini")
                'created_at': str,           # ISO timestamp
                'done': bool,                # Whether generation is complete
                'done_reason': str,          # e.g. "stop"
                'total_duration': int,       # Total response time in nanoseconds
                'load_duration': int,        # Time to load the model (ns)
                'prompt_eval_count': int,    # Number of prompt tokens
                'prompt_eval_duration': int, # Time taken to evaluate prompt
                'eval_count': int,           # Number of tokens generated
                'eval_duration': int,        # Time spent generating tokens
                'message': {
                    'role': str,             # "assistant"
                    'content': str           # Model response content (what you care about)
                }
            }

    Example usage:
        content = chat_with_model("phi4", messages)["message"]["content"]
    """

    supported_models = get_ollama_models()

    if model_name not in supported_models:
        raise ValueError(
            f"Model '{model_name}' is not supported. Choose from: {supported_models}")

    # Merge default and user-provided options
    final_options = DEFAULT_OPTIONS.copy()
    if options:
        final_options.update(options)

    images = None
    if image_paths:
        images = []
        for path in image_paths:
            file_path = Path(path)
            if not file_path.is_file():
                raise FileNotFoundError(f"Image file not found: {path}")
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                images.append(encoded)

    final_messages = messages.copy()

    if images:
        temp = final_messages[-1]
        temp["images"] = images
        final_messages[-1] = temp

    if stream:
        def stream_generator():
            response_stream = client.chat(
                model=model_name,
                messages=final_messages,
                options=final_options,
                stream=True
            )
            for chunk in response_stream:
                yield chunk["message"]["content"]

        return stream_generator()
    else:
        for _ in range(5):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    client.chat, model=model_name, messages=final_messages, options=final_options)
                try:
                    response = future.result(timeout=timeout)
                    return response
                except concurrent.futures.TimeoutError:
                    print("Timeout reached. Sleeping and retrying...")
                    print("fallback placeholder sleeps for 5 minutes?")
                    time.sleep(60 * 6)
