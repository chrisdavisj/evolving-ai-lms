import threading
import requests
from rdflib.namespace import RDF
from rdflib import Graph, Literal, Namespace, URIRef
from io import StringIO
import os
import csv
import faiss
from sentence_transformers import SentenceTransformer
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import os
from app.services.ollama_interface import chat_with_model

import re

import time
from functools import wraps


def retry_on_exception(max_retries=5, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(
                        f"Attempt {attempt} failed in '{func.__name__}': {e}")
                    if attempt < max_retries:
                        time.sleep(delay)
                    else:
                        print(
                            f"Giving up on '{func.__name__}' after {max_retries} attempts.")
                        return None
        return wrapper
    return decorator


def extract_json_content(raw_text):
    # Remove code fences like ```json or ``` (any variant)
    clean_text = re.sub(r"```(?:json)?\n?", "", raw_text).strip("`").strip()
    return json.loads(clean_text)


@retry_on_exception()
def clarify_input(image_path, prompt, learner_context):
    system_prompt = (
        "You are an intelligent educational assistant. "
        "Your role is to help clarify vague learner questions using three key sources: "
        "1) the learner's written prompt, 2) the uploaded image, and 3) their learning profile. "
        "You will infer intent, identify possible misconceptions, and output a structured result."
    )

    user_prompt = f"""\
### Learner Context
{learner_context}

### Learner Prompt
{prompt}

### Instructions
Analyze the learner's question and the provided image, using the context above. 
Use your reasoning to determine:
- What the learner is likely trying to ask
- Whether there are signs of confusion or misconception

Respond in **exact JSON format** using the following structure:

```json
{{
  "clarified_question": "<your rephrased or expanded question>",
  "possible_misunderstanding": "<short description of the learner's confusion or error, if any>"
}}
```"""

    res = chat_with_model(
        model_name="mistral-small3.2:latest-64k",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        image_paths=[image_path]
    )
    raw_output = res["message"]["content"]
    return extract_json_content(raw_output)


@retry_on_exception()
def enrich_query(clarified, learner_context):
    system_prompt = (
        "You are a semantic query expander for an educational assistant system. "
        "Your job is to transform a clarified learner question into a structured query object that improves downstream content retrieval. "
        "You must consider the learner's background and generate an enriched, search-ready query with concept tags and appropriate cognitive depth."
    )

    user_prompt = f"""\
### Clarified Question
{clarified['clarified_question']}

### Learner Context
{learner_context}

### Instructions
Use the clarified question and learner context to produce a **structured semantic query** that improves retrieval from a knowledge graph and curriculum-aligned media library.

Be specific in:
- The `concepts`: list key domain-specific terms mentioned or implied
- The `query`: write a clean, rephrased version optimized for retrieval
- The `depth`: choose `"shallow"` for factual/exploratory, or `"deep"` for explanation/inference
- The `language_level`: `"simple"` for accessible explanation, `"technical"` for domain-aligned detail

Respond using **only the following JSON format**:

```json
{{
  "concepts": ["..."],
  "query": "...",
  "depth": "shallow" or "deep",
  "language_level": "simple" or "technical"
}}
```"""

    res = chat_with_model("mistral-small3.2:latest-64k", [
                          {"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])
    message = res["message"]["content"]
    refined_message = message[message.index("{"):message.rfind("}")+1]
    return json.loads(refined_message)


# Configuration
SPARQL_ENDPOINT = "http://arsenal.cs.wright.edu:3030/evolving-ai-lms/query"
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")


@retry_on_exception()
def fetch_markdown_content(url):
    try:
        if url.endswith(".md"):
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text
    except Exception:
        pass
    return ""


@retry_on_exception()
def query_kg_for_media():
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setReturnFormat(JSON)

    query = """
    PREFIX edu: <https://edugate.cs.wright.edu/lod/ontology/>
    PREFIX res: <https://edugate.cs.wright.edu/lod/resource/>

    SELECT ?media ?title (GROUP_CONCAT(DISTINCT ?topic; separator=", ") AS ?topics) ?mediaSourceLink ?content
    WHERE {
      ?media a edu:Media .
      OPTIONAL { ?media edu:hasTitle ?title. }
      OPTIONAL { ?media edu:hasMediaSourceLink ?mediaSourceLink. }
      OPTIONAL {
        ?media edu:coversTopic ?coversTopic.
        ?coversTopic edu:asString ?topic.
      }
      OPTIONAL { ?media edu:hasContent ?content. }
    }
    GROUP BY ?media ?title ?mediaSourceLink ?content
    """
    sparql.setQuery(query)
    results = sparql.query().convert()

    media_items = []
    for row in results["results"]["bindings"]:
        mid = row["media"]["value"]
        title = row.get("title", {}).get("value", "Untitled")
        link = row.get("mediaSourceLink", {}).get("value", "")
        content = row.get("content", {}).get("value", "")
        topics_str = row.get("topics", {}).get("value", "")
        topics = [t.strip() for t in topics_str.split(",") if t.strip()]

        # Fallback: fetch .md file content if content is empty
        if not content and link.endswith(".md"):
            content = fetch_markdown_content(link)

        media_items.append({
            "id": mid,
            "title": title,
            "content": content,
            "link": link,
            "topics": topics
        })

    return media_items


@retry_on_exception()
def build_vector_index(media_items):
    texts = [
        f"{m['title']} {m['content']} {' '.join(m['topics'])}" for m in media_items]
    embeddings = EMBEDDING_MODEL.encode(texts, convert_to_numpy=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index, embeddings, media_items


@retry_on_exception()
def extract_text_from_query_obj(query_obj):
    """
    Recursively extracts all text values from an unknown-structure JSON.
    """
    texts = []

    def recurse(value):
        if isinstance(value, str):
            texts.append(value)
        elif isinstance(value, list):
            for item in value:
                recurse(item)
        elif isinstance(value, dict):
            for v in value.values():
                recurse(v)

    recurse(query_obj)
    return " ".join(texts)


@retry_on_exception()
def retrieve_media(query_obj):
    query_text = extract_text_from_query_obj(query_obj)
    query_embedding = EMBEDDING_MODEL.encode(
        [query_text], convert_to_numpy=True)

    media_items = query_kg_for_media()
    if not media_items:
        return []

    index, _, media_items = build_vector_index(media_items)
    D, I = index.search(query_embedding, k=min(5, len(media_items)))

    return [media_items[i] for i in I[0]]


@retry_on_exception()
def generate_narrative(enriched_query, media_refs, learner_context, image_path):
    # Step 1: Combine the media content into a single source block
    grounded_media_text = ""
    for media in media_refs:
        content = media.get("content", "").strip()
        if content:
            grounded_media_text += f"\n\n### {media['title']}\n{content}"
    if not grounded_media_text:
        grounded_media_text = "No media content provided."

    system_prompt = (
        "You are an AI tutor that creates personalized, pedagogically grounded explanations "
        "based on source curriculum materials, visual diagrams, and the learner's cognitive profile. "
        "Your responses are clear, engaging, voice-ready, and instructionally effective."
    )

    # Step 2: Build user prompt
    user_prompt = f"""\
### Learner Context
{learner_context}

### Learner Query
{enriched_query['query']}

### Task
Write a **Markdown-formatted narrative explanation** for the learner using the provided source content and image. Your goal is to help the learner understand the concept in a clear, engaging, voice-deliverable way.

### Guidelines
- Use facts, explanations, and vocabulary grounded in the source materials.
- Refer to visual aspects of the uploaded image where helpful (e.g., graph labels, patterns).
- Maintain a friendly, explanatory tone — like a good tutor speaking.
- Apply the following **instructional techniques implicitly** (do not name them or describe them):

  • **Interleaving** – connect the concept to related ideas the learner might know  
  • **Dual coding** – make use of the image to reinforce concepts  
  • **Elaboration** – explain why things work, not just what they are  
  • **Retrieval practice** – end with a subtle, open-ended question that prompts recall or reflection  

### Source Curriculum Content
{grounded_media_text}
"""

    # Step 3: Call the model
    response = chat_with_model(
        model_name="mistral-small3.2:latest-64k",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        image_paths=[image_path]
    )

    # Step 4: Append a Reference Section to the output
    generated_narrative = response["message"]["content"]

    reference_section = "\n\n### References\n"
    for media in media_refs:
        title = media.get("title", "Untitled")
        link = media.get("link", "#")
        topics = ", ".join(media.get("topics", []))
        reference_section += f"- [{title}]({link})  \n  _Topics: {topics}_\n"

    return generated_narrative.strip() + reference_section


@retry_on_exception()
def generate_flashcard(narrative):
    system_prompt = (
        "You generate conceptually focused flashcards in Markdown format, designed to summarize core ideas from educational narratives. "
        "The flashcards reinforce understanding, memory, and active reflection, and are tailored to the learner’s level. "
        "Do not use fill-in-the-blank. Do not mimic quiz formats. Do not name any learning techniques — instead, apply them implicitly."
    )

    user_prompt = f"""\
### Narrative Explanation
{narrative}

### Task
Create a single flashcard in **Markdown format** that distills the core insight of the explanation above.

### Guidelines
- Start with a **clear, declarative summary** of the main concept or mechanism explained.
- Make it feel like a short **mental snapshot** — the key thing the learner should walk away with.
- Include **2–4 key concepts** reinforced by this flashcard.
- End with a **self-reflection prompt** to encourage deeper thought or application.
- DO NOT format it as a quiz or Q&A.
- DO NOT use fill-in-the-blank or bullet-only definitions.
- DO NOT name any instructional techniques — embed them through structure and phrasing only.

### Output Format
```markdown
### 🧠 Flashcard

<1–3 sentence summary of the core idea>

**Key Concepts:**  
- Concept A  
- Concept B  
- Concept C

**🔁 Reflection:**  
<A self-directed prompt like: “How does this compare to…?” or “Can you think of an example where…?”>

## Example Output (Pedagogically Structured, Summarative)

```markdown
### 🧠 Flashcard

At a critical point on a curve, the slope of the tangent is zero — this indicates a local maximum, minimum, or inflection depending on the curve’s behavior. Understanding this helps you analyze change and structure in mathematical functions.

**Key Concepts:**  
- Derivative  
- Critical Point  
- Slope  
- Local Extrema

**🔁 Reflection:**  
Can you explain how the behavior before and after a critical point determines its type?
"""

    return chat_with_model("mistral-small3.2:latest-64k", [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])["message"]["content"]


@retry_on_exception()
def generate_csv_rows(narrative, flashcard, media_ids):

    system_prompt = (
        "You are an expert information extractor and pedagogy-oriented explainer. "
        "From AI-generated responses to narrow user questions, your task is to extract only the most impactful, generalizable, and transferable knowledge concepts. "
        "Avoid copying specific examples, edge cases, or tightly scoped problem phrasing. "
        "Your output should transform the narrow response into rich, structured learning material that explains the broader concepts in depth for educational purposes."
    )

    user_prompt = f"""\
### Source Inputs

#### Narrow Narrative
{narrative}

#### Flashcard
{flashcard}

---

### Instructions

Use the source content to identify **broad, generalizable knowledge concepts** that transcend the specific examples in the narrative and flashcard.

Your goal is to produce **structured, detailed instructional material** suitable for deep learning. Focus on:

- General **concept definitions**
- Underlying **principles and mechanisms**
- **Why and how** each concept works
- Key **connections between concepts**
- Any common **misconceptions** or **confusions** to clarify

Do **not** include narrow problem details, user-specific phrasing, or answer formatting from the original materials.

The output should read like a **teaching note or concept explainer** in rich, explanatory prose — not a bulleted cheat sheet or FAQ.

Output only the final instructional material. Do not include any headers like "Output:" or commentary.
"""

    res_1 = chat_with_model("mistral-small3.2:latest-64k", [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    res_1_message = res_1["message"]["content"]

    system_prompt = (
        "You convert instructional material into structured CSV rows for knowledge graph ingestion. "
        "Each row should contain a narrowed, unique media title, a concise set of relevant topics, and the recommended audience. "
        "Do not include explanations. Output only the CSV rows as plain text."
    )

    user_prompt = f"""\
### Instructional Material
{res_1_message}

### Task
Extract metadata from the instructional material above and output a single CSV row with the following headers:

`media_title,topics_covered,recommendedAudience`

### Guidelines
- `media_title`: Create a short, specific, and unique title based on the main concept — avoid overly broad or vague titles.
- `topics_covered`: Include the **top 3 most relevant and narrowly scoped** topics.
- `recommendedAudience`: Describe the intended learner group (e.g., "undergraduate CS students", "intro-level high school physics", etc.)

### Output Format
Respond with **raw CSV only**. Do not include explanations, quotes, or markdown formatting.
"""

    res = chat_with_model("mistral-small3.2:latest-64k", [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    return res_1_message, res["message"]["content"]


# RDF Namespaces
EDU_ONT = Namespace("https://edugate.cs.wright.edu/lod/ontology/")
EDU_R = Namespace("https://edugate.cs.wright.edu/lod/resource/")


def format_named_uri(label_string: str, kind: str) -> URIRef:
    label_string = label_string.strip()
    label_string = re.sub(r"[^\w\s]", "X", label_string)
    label_string = label_string.replace(" ", "_")
    parts = label_string.split("_")
    pascal_parts = [p.capitalize() for p in parts if p]
    transformed = "_".join(pascal_parts)
    return URIRef(f"https://edugate.cs.wright.edu/lod/resource/{kind}.{transformed}")


@retry_on_exception()
def upload_ttl_file(fuseki_base, dataset_name, file_path):
    data_url = f"{fuseki_base}/{dataset_name}/data"
    headers = {"Content-Type": "text/turtle"}

    with open(file_path, "rb") as f:
        response = requests.post(data_url, headers=headers, data=f)

    if response.status_code in (200, 201):
        print(f"File '{file_path}' uploaded successfully.")
    else:
        print("Error uploading file:", response.status_code, response.text)


@retry_on_exception()
def populate_kg_from_csv(csv_string, content_string, ttl_filename="temp_upload.ttl"):
    reader = csv.DictReader(StringIO(csv_string.strip()))
    g = Graph()
    g.bind("edu-ont", EDU_ONT)
    g.bind("edu-r", EDU_R)

    for row in reader:
        media_title = row["media_title"].strip()
        media_uri = format_named_uri(media_title, "Media")

        g.add((media_uri, RDF.type, EDU_ONT["Media"]))
        g.add((media_uri, EDU_ONT["hasTitle"], Literal(media_title)))
        g.add((media_uri, EDU_ONT["hasContent"],
              Literal(content_string.strip())))

        for audience in row["recommendedAudience"].split(","):
            g.add((media_uri, EDU_ONT["hasRecommended"],
                  Literal(audience.strip())))

        for topic in row["topics_covered"].split(","):
            topic = topic.strip()
            topic_uri = format_named_uri(topic, "Topic")
            g.add((media_uri, EDU_ONT["coversTopic"], topic_uri))
            g.add((topic_uri, RDF.type, EDU_ONT["Topic"]))
            g.add((topic_uri, EDU_ONT["asString"], Literal(topic)))

    # Serialize to Turtle
    g.serialize(destination=ttl_filename, format="turtle")
    print(f"📄 Turtle file '{ttl_filename}' created.")

    # Upload
    upload_ttl_file("http://arsenal.cs.wright.edu:3030",
                    "evolving-ai-lms", ttl_filename)

    # Delete the temporary file
    try:
        os.remove(ttl_filename)
        print(f"Temp file '{ttl_filename}' deleted.")
    except Exception as e:
        print(f"Could not delete temp file: {e}")


def run_full_pipeline(image_path, prompt, learner_context):
    clarified = clarify_input(image_path, prompt, learner_context)
    if clarified is None:
        return None, None

    enriched_query = enrich_query(clarified, learner_context)
    if enriched_query is None:
        return None, None

    media_data = retrieve_media(enriched_query)
    if media_data is None:
        return None, None

    narrative = generate_narrative(
        enriched_query, media_data, learner_context, image_path)
    if narrative is None:
        return None, None

    flashcard = generate_flashcard(narrative)
    if flashcard is None:
        return narrative, None

    content, csv_output = generate_csv_rows(narrative, flashcard, media_data)
    if not content or not csv_output:
        return narrative, flashcard

    csv_string = f"""media_title,topics_covered,recommendedAudience
{csv_output}
"""

    # Run KG population in background
    threading.Thread(
        target=populate_kg_from_csv,
        args=(csv_string, content),
        kwargs={"ttl_filename": "temp_upload.ttl"},
        daemon=True
    ).start()

    return narrative, flashcard
