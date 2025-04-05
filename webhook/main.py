from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv
from webhook.chatbot import Chatbot
from pprint import pprint
"""
uvicorn webhook.main:app --reload  
ngrok http 8000
"""

load_dotenv()
app = FastAPI()
bot = Chatbot()
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
    try:
        value = data["entry"][0]["changes"][0]["value"]
        
        if "messages" in value:
        
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            contact = data["entry"][0]["changes"][0]["value"]["contacts"][0]
            bot.recieve_message(message,contact)
    except Exception as e:
        print(f"Error receive_message API {e}")

    
    return {"status": "ok"}
