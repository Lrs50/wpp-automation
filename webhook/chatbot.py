from dotenv import load_dotenv
import os
from heyoo import WhatsApp
from pprint import pprint
from tinydb import TinyDB, Query
from datetime import datetime
import google.generativeai as genai
import textwrap

# Load the .env file
load_dotenv()

wpp_token = os.getenv("wpp_token")
chatbot_number = os.getenv("chatbot_number")
personal_number = os.getenv("personal_number")
carol_number = os.getenv("carol_number")
gemini_key = os.getenv("gemini_key")

initial_prompt = """
Você é um assistente financeiro chamado *Bot da Grana*.

Seu objetivo é ajudar o usuário a:
- Entender melhor seus gastos
- Economizar dinheiro
- Fazer escolhas financeiras mais conscientes

Importante:
- Você **só deve responder perguntas relacionadas a finanças**.
- Ignore ou recuse educadamente qualquer assunto fora do universo financeiro.

Se esta for sua **primeira conversa** com o usuário:
1. Apresente-se como Bot da Grana.
2. Explique que está aqui para ajudar com finanças.
3. Em seguida, responda normalmente à mensagem do usuário.
"""


db = TinyDB('data/users.json')
User = Query()

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-2.0-flash')


def call_gemini(prompt):

    response = model.generate_content(prompt)
    return format_output_llm(response.text)

def format_output_llm(text: str) -> str:
    text = text.replace('•', '*')
    
    text = '\n'.join(line.strip() for line in text.strip().splitlines() if line.strip())
    
    return textwrap.indent(text, '', predicate=lambda _: True)


class Chatbot(object):
    def __init__(self):
        self.messenger = WhatsApp(wpp_token,phone_number_id=chatbot_number)
        
        
    def send_message(self,number = personal_number,msg="Resposta teste"):
        try:
            self.messenger.send_message(msg, number)
        except Exception as e:
            print(f"Error Chatbot {e}")
            
    def recieve_message(self,msg,contact):
        if msg["type"] == "text":
            number = contact["wa_id"]
            name = contact["profile"]["name"]
            text = msg["text"]["body"]
            db.insert({
                "timestamp": datetime.now().isoformat(),
                "number": number,
                "text": text,
                "name":name,
                "role":"user"
            })
            
            history = self.load_history(number)
            chat = model.start_chat(history=history)
            
            history = self.load_history(number)
            chat = model.start_chat(history=history)
            response = chat.send_message(text).text
            db.insert({
                "timestamp": datetime.now().isoformat(),
                "number": number,
                "text": response,
                "name":name,
                "role":"model"
            })
            
            self.send_message(number=number,msg=response)
    
    def load_history(self,number):
        result = db.search(User.number == number)
        if result:
            history = [{"role":"user","parts":initial_prompt}]
            for msg in result:
                msg = dict(msg)
                history.append({"role":msg['role'], "parts":msg["text"]})
            return history
        return []        
            
def main():
    answer = db.search(User.number == carol_number)
    
    for data in answer:
        data = dict(data)
        print(f"{data['role']}: ",data["text"])
    
    
if __name__=="__main__":
    main()