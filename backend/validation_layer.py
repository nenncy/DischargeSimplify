# # from sentence_transformers import SentenceTransformer
# # import faiss
# # import numpy as np
# # from utils import _call_openai_with_rate_limit, extract_json  # Assume these come from your main utils

# # model = SentenceTransformer('all-MiniLM-L6-v2')  # Load once globally

# # def chunk_text(text: str, chunk_size: int = 200) -> list:
# #     sentences = text.split('. ')
# #     chunks, current_chunk = [], ""
# #     for sentence in sentences:
# #         if len(current_chunk) + len(sentence) < chunk_size:
# #             current_chunk += sentence + ". "
# #         else:
# #             chunks.append(current_chunk.strip())
# #             current_chunk = sentence + ". "
# #     if current_chunk:
# #         chunks.append(current_chunk.strip())
# #     return chunks

# # def build_faiss_index(chunks: list):
# #     embeddings = model.encode(chunks)
# #     index = faiss.IndexFlatL2(embeddings.shape[1])
# #     index.add(np.array(embeddings))
# #     return index, chunks

# # def retrieve_relevant_chunks(query: str, index, chunks, top_k=3):
# #     query_embedding = model.encode([query])
# #     D, I = index.search(np.array(query_embedding), top_k)
# #     return [chunks[i] for i in I[0]]

# # def validate_and_filter_fields(obj, original_text_chunks, faiss_index):
# #     validated_output = {}

# #     def is_contextually_valid(text_block: list) -> bool:
# #         for sentence in text_block:
# #             relevant_chunks = retrieve_relevant_chunks(sentence, faiss_index, original_text_chunks, top_k=3)
# #             # prompt = (
# #             #     "You are a medical validator.\n"
# #             #     "Determine whether the following simplified text is present in this original medical context.\n\n"
# #             #     f"Context:\n{''.join(relevant_chunks)}\n\n"
# #             #     f"Simplified: {sentence}\n\n"
# #             #     "if not present, please provide a JSON object with the following keys:\n"
                
# #             # )
# #             prompt = (
# #     "You are a medical validator.\n"
# #     "Determine whether the following simplified sentence is present in the original medical context provided.\n"
# #     "Only return the field content if it is directly supported by the context. Do not infer or hallucinate.\n\n"
# #     f"Context:\n{''.join(relevant_chunks)}\n\n"
# #     f"Simplified Sentence:\n{sentence}\n\n"
# #     "Return a JSON object with the following possible keys ONLY if they are present in the context:\n"
# #     "  \"SimplifiedInstructions\": [...],\n"
# #     "  \"Importance\": [...],\n"
# #     "  \"FollowUpTasks\": [...],\n"
# #     "  \"Medications\": [...],\n"
# #     "  \"Precautions\": [...],\n"
# #     "  \"References\": [...]\n\n"
# #     "If none of them are supported, return an empty object: {}\n"
# # )

# #             resp = _call_openai_with_rate_limit(prompt, model="gpt-4o")
# #             raw = getattr(resp.choices[0], "message", resp.choices[0]).content
# #             try:
# #                 result = extract_json(raw)
# #                 if not result.get("is_valid", False):
# #                     return False
# #             except Exception:
# #                 return False
# #         return True

# #     # Validate core fields
# #     for key in ["SimplifiedInstructions", "Importance", "FollowUpTasks", "Precautions", "References"]:
# #         block = obj.get(key, [])
# #         validated_output[key] = block if is_contextually_valid(block) else []

# #     # Validate Medications if present
# #     medications = obj.get("Medications", [])
# #     if medications and is_contextually_valid(medications):
# #         validated_output["Medications"] = medications
# #     else:
# #         validated_output["Medications"] = []

# #     return validated_output

# from sentence_transformers import SentenceTransformer
# import faiss
# import numpy as np
# from utils import _call_openai_with_rate_limit, extract_json  # Assume these come from your main utils

# model = SentenceTransformer('all-MiniLM-L6-v2')  # Load once globally

# def chunk_text(text: str, chunk_size: int = 200) -> list:
#     sentences = text.split('. ')
#     chunks, current_chunk = [], ""
#     for sentence in sentences:
#         if len(current_chunk) + len(sentence) < chunk_size:
#             current_chunk += sentence + ". "
#         else:
#             chunks.append(current_chunk.strip())
#             current_chunk = sentence + ". "
#     if current_chunk:
#         chunks.append(current_chunk.strip())
#     return chunks

# def build_faiss_index(chunks: list):
#     embeddings = model.encode(chunks)
#     index = faiss.IndexFlatL2(embeddings.shape[1])
#     index.add(np.array(embeddings))
#     return index, chunks

# def retrieve_relevant_chunks(query: str, index, chunks, top_k=3):
#     query_embedding = model.encode([query])
#     D, I = index.search(np.array(query_embedding), top_k)
#     return [chunks[i] for i in I[0]]

# def validate_and_filter_fields(obj, original_text_chunks, faiss_index):
#     validated_output = {
#         "SimplifiedInstructions": [],
#         "Importance": [],
#         "FollowUpTasks": [],
#         "Medications": [],
#         "Precautions": [],
#         "References": []
#     }

#     def collect_valid_content(field_key: str, text_block: list):
#         for sentence in text_block:
#             relevant_chunks = retrieve_relevant_chunks(sentence, faiss_index, original_text_chunks, top_k=3)
#             # prompt = (
#             #     "You are a medical validator.\n"
#             #     "Determine whether the following simplified sentence is present in the original medical context provided.\n"
#             #     "Only return the field content if it is directly supported by the context. Do not infer or hallucinate.\n\n"
#             #     f"Context:\n{''.join(relevant_chunks)}\n\n"
#             #     f"Simplified Sentence:\n{sentence}\n\n"
#             #     "Return a JSON object with the following possible keys ONLY if they are present in the context:\n"
#             #     "  \"SimplifiedInstructions\": [...],\n"
#             #     "  \"Importance\": [...],\n"
#             #     "  \"FollowUpTasks\": [...],\n"
#             #     "  \"Medications\": [...],\n"
#             #     "  \"Precautions\": [...],\n"
#             #     "  \"References\": [...]\n\n"
#             #     "If one of them or more than one componenets mentioned are not supported in original text return an empty object:{} for particular component.\n"
#             # )
#             prompt = (
#                 "You are a medical validator.\n"
#                 "For each field in the simplified discharge instruction below, verify whether every bullet point is explicitly supported by the original context.\n"
#                 "Only include bullet points in the output if the exact idea is clearly stated in the context. Do not infer or hallucinate.\n\n"
#                 f"Context:\n{''.join(relevant_chunks)}\n\n"
#                 f"Simplified Sentence:\n{sentence}\n\n"
#                 "Return a JSON object with the following structure:\n"
#                 "{\n"
#                 "  \"SimplifiedInstructions\": [only if bullet points are supported],\n"
#                 "  \"Importance\": [only if bullet points are supported],\n"
#                 "  \"FollowUpTasks\": [only if bullet points are supported],\n"
#                 "  \"Medications\": [only if bullet points are supported],\n"
#                 "  \"Precautions\": [only if bullet points are supported],\n"
#                 "  \"References\": [only if bullet points are supported]\n"
#                 "}\n"
#                 "If none of the bullet points in a section are supported, return that section as an empty array. Example: \"Importance\": []\n"
#             )


#             resp = _call_openai_with_rate_limit(prompt, model="gpt-4o")
#             raw = getattr(resp.choices[0], "message", resp.choices[0]).content
#             try:
#                 result = extract_json(raw)
#                 print(result, "***********123")
#                 if result.get(field_key):
#                     validated_output[field_key].extend(result[field_key])
#             except Exception:
#                 continue

#     for key in validated_output.keys():
#         block = obj.get(key, [])
#         collect_valid_content(key, block)

#     return validated_output

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from utils import _call_openai_with_rate_limit, extract_json  # Assume these come from your main utils

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
            prompt = (
                "You are a medical validator.\n"
                "For each field in the simplified discharge instruction below, verify whether every bullet point is explicitly supported by the original context.\n"
                "Only include bullet points in the output if the exact idea is clearly stated in the context. Do not infer or hallucinate.\n\n"
                f"Context:\n{''.join(relevant_chunks)}\n\n"
                f"Simplified Sentence:\n{sentence}\n\n"
                "Return a JSON object with the following structure:\n"
                "{\n"
                "  \"SimplifiedInstructions\": [only if bullet points are supported],\n"
                "  \"Importance\": [only if bullet points are supported],\n"
                "  \"FollowUpTasks\": [only if bullet points are supported],\n"
                "  \"Medications\": [only if bullet points are supported],\n"
                "  \"Precautions\": [only if bullet points are supported],\n"
                "  \"References\": [only if bullet points are supported]\n"
                "}\n"
                "If none of the bullet points in a section are supported, return that section as an empty array. Example: \"Importance\": []\n"
            )

            resp = _call_openai_with_rate_limit(prompt, model="gpt-4o")
            raw = getattr(resp.choices[0], "message", resp.choices[0]).content
            try:
                result = extract_json(raw)
                print(result, "***********123")
                if result.get(field_key):
                    for item in result[field_key]:
                        if item not in validated_output[field_key]:
                            validated_output[field_key].append(item)
            except Exception:
                continue

    for key in validated_output.keys():
        block = obj.get(key, [])
        collect_valid_content(key, block)

    return validated_output
