from dotenv import load_dotenv
from openai import OpenAI
import requests

from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENROUTER_AI_KEY")


def patient_chat(context: str, question: str, history: list = []) -> str:
    try:
        url="https://openrouter.ai/api/v1/chat/completions"  # Replace with the actual OpenRouter API URL
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"          
        }
        data = {
            "model": "openai/gpt-4o",
            "messages": [
                {"role": "system", "content": f"You are a helpful assistant answering patient questions based on these simplified discharge instructions:\n\n{context.strip()}"},
                {"role": "user", "content": question}
            ]
        }
       
        # [
        #     {"role": "system", "content": f"You are a helpful assistant answering patient questions based on these simplified discharge instructions:\n\n{context.strip()}"},
        # ] + history

        # messages.append({"role": "user", "content": question})

        response =requests.post(url, headers=headers , json= data)
        print(response, "*********")
        if response.status_code == 200:
            res_json = response.json()  
            reply = res_json["choices"][0]["message"]["content"]
            return reply
        else:
             raise Exception(f"API call failed: {response.status_code} - {response.text}")
    except Exception as e:
        return f"Error: {str(e)}"
