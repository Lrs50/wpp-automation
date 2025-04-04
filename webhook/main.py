from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv

"""
uvicorn webhook.main:app --reload  
ngrok 8000
"""

load_dotenv()
app = FastAPI()

VERIFY_TOKEN = os.getenv("verify_token")

@app.get("/webhook")
async def verify(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params.get("hub.challenge"))
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Mensagem recebida:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        text = message["text"]["body"]
        sender = message["from"]
        print(f"Mensagem de {sender}: {text}")
        # Aqui: processar mensagem, salvar no Google Sheets, responder, etc.
    except KeyError:
        print("Evento não contém mensagem de texto.")
    
    return {"status": "ok"}
