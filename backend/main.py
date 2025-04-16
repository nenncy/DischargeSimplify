
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from LLM_simplify import simplify_discharge

app = FastAPI()
class DischargeInput(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/simplify")
async def simplify_text(payload: DischargeInput):
    simplified = simplify_discharge(payload.text)
    return {"result": simplified}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)