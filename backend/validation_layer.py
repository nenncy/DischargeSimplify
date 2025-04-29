from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from .utils import _call_openai_with_rate_limit, extract_json  # Assume these come from your main utils

model = SentenceTransformer('all-MiniLM-L6-v2')  # Load once globally

def chunk_text(text: str, chunk_size: int = 200) -> list:
    sentences = text.split('. ')
    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def build_faiss_index(chunks: list):
    embeddings = model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    return index, chunks

def retrieve_relevant_chunks(query: str, index, chunks, top_k=3):
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), top_k)
    return [chunks[i] for i in I[0]]

def validate_and_filter_fields(obj, original_text_chunks, faiss_index):
    validated_output = {
        "SimplifiedInstructions": [],
        "Importance": [],
        "FollowUpTasks": [],
        "Medications": [],
        "Precautions": [],
        "References": []
    }

    def collect_valid_content(field_key: str, text_block: list):
        for sentence in text_block:
            relevant_chunks = retrieve_relevant_chunks(sentence, faiss_index, original_text_chunks, top_k=3)
            # prompt = (
            #     "You are a medical guardrail agent.\n"
            #     "For each field in the simplified discharge instruction below, verify whether each bullet point is explicitly supported by the original context.\n"
            #     "Only include bullet points in the output if the exact idea is clearly stated in the context. Do not infer or hallucinate.\n\n"
            #     f"Context:\n{''.join(relevant_chunks)}\n\n"
            #     f"Simplified Sentence:\n{sentence}\n\n"
            #     "Return a JSON object with the following structure:\n"
            #     "{\n"
            #     "  \"SimplifiedInstructions\": [only if bullet points are supported if not remove that bullet point],\n"
            #     "  \"Importance\": [only if bullet points are supported if not remove that bullet point],\n"
            #     "  \"FollowUpTasks\": [only if bullet points are supported if not remove that bullet point],\n"
            #     "  \"Medications\": [only if bullet points are supported if not remove that bullet point],\n"
            #     "  \"Precautions\": [only if bullet points are supported if not remove that bullet point],\n"
            #     "  \"References\": [only if bullet points are supported if not remove that bullet point]\n"
            #     "}\n"
            #     "If none of the bullet points in a section are supported, return that section as an empty array. Example: \"Importance\": []\n"
            # )
            prompt = (
    f"You are a strict validation agent.\n"
    f"Task: Given the original medical context and a candidate bullet point, validate whether the bullet point is fully supported.\n\n"
    f"Context:\n{''.join(relevant_chunks)}\n\n"
    f"Candidate Bullet Point:\n{sentence}\n\n"
    "Instructions:\n"
    "- If the **exact idea and content** of the bullet point is **clearly supported** by the context, return it **exactly as given** inside the correct JSON field.\n"
    "- **Do not modify, shorten, rephrase, or rewrite** the bullet point.\n"
    "- If the bullet point is **not clearly supported**, return an empty list for that field.\n"
    "- **Never change** the text of the bullet point.\n"
    "- Output only a JSON object in this structure:\n"
    "{\n"
    f"  \"{field_key}\": [list of validated bullet points]\n"
    "}\n"
    "Examples:\n"
    "- If the bullet point is supported:\n"
    "{\n"
    f"  \"{field_key}\": [\"{sentence}\"]\n"
    "}\n"
    "- If the bullet point is not supported:\n"
    "{\n"
    f"  \"{field_key}\": []\n"
    "}\n"
)


            resp = _call_openai_with_rate_limit(prompt, model="gpt-4o")
            raw = getattr(resp.choices[0], "message", resp.choices[0]).content
            try:
                result = extract_json(raw)
               
                if result.get(field_key):
                    for item in result[field_key]:
                        if item not in validated_output[field_key]:
                            validated_output[field_key].append(item)
            except Exception:
                continue

    for key in validated_output.keys():
        block = obj.get(key, [])
        collect_valid_content(key, block)
    print(validated_output, "***********123")
    return validated_output
