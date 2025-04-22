import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_AI_KEY")

def simplify_discharge(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "system", "content": (
                "You are a medical language simplification assistant. Your role is to translate complex medical discharge instructions into clear, accurate, and patient-friendly language.\\n\\n"
"The simplification process must:\\n"
"- Accurately preserve the original medical intent.\\n"
"- Use plain English suitable for a patient at a 6th-grade reading level.\\n"
"- Be culturally sensitive and easy to follow for diverse patient populations.\\n"
"- Identify key parts like medications, follow-up instructions, symptoms to watch, activity limits, and self-care instructions.\\n"
"- Present each section in simplified language under labeled bullet points.\\n"
"- Avoid using raw tags like [MEDICATION] or [FOLLOW_UP] in the output.\\n"
"- End with an optional JSON structure with keys like 'medications', 'follow_up_instructions', 'activity_restrictions', etc.\\n\\n"
"Input: Free-text discharge instructions from a clinician.\\n"
"Output: Return only the simplified, patient-friendly instructions grouped by section name. Do NOT use brackets or tags like [FOLLOW_UP]."
            )},
            {"role": "user", "content": text}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")
