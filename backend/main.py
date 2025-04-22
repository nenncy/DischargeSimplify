
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from LLM_simplify import simplify_discharge
from patient_chat import patient_chat

app = FastAPI()
class DischargeInput(BaseModel):
    text: str

class ChatInput(BaseModel):
    context: str
    question: str
    history: list = []

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/simplify")
async def simplify_text(payload: DischargeInput):
    simplified = simplify_discharge(payload.text)
    return {"result": simplified}

@app.post("/chat")
async def chat(payload: ChatInput):
    answer = patient_chat(
        context=payload.context,
        question=payload.question,
        history=payload.history
    )
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)