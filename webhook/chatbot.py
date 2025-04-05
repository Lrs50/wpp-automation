from dotenv import load_dotenv
import os
from heyoo import WhatsApp
from pprint import pprint
from tinydb import TinyDB, Query
from datetime import datetime
import google.generativeai as genai
import textwrap
import json
import re
# Load the .env file
load_dotenv()

wpp_token = os.getenv("wpp_token")
chatbot_number = os.getenv("chatbot_number")
personal_number = os.getenv("personal_number")
carol_number = os.getenv("carol_number")
mae_number = os.getenv("mae_number")
gemini_key = os.getenv("gemini_key")

initial_prompt = """
Você é um assistente financeiro inteligente chamado *Bot da Grana*, que interage com os usuários exclusivamente através do WhatsApp.

📱 Como chatbot de WhatsApp, você **deve formatar suas respostas usando a sintaxe de formatação compatível com o WhatsApp**.  
Aqui estão as regras de formatação que você pode usar nas suas mensagens:

✅ **Regras de formatação do WhatsApp:**
- *Negrito:* use asteriscos em volta do texto → *exemplo*
- _Itálico:_ use sublinhado em volta do texto → _exemplo_
- ~Tachado:~ use til em volta do texto → ~exemplo~
- `Código:` use um acento grave (`) de cada lado → `exemplo`
- ```Monoespaçado:``` use três acentos graves de cada lado (```exemplo```)
- > Citação: use `>` antes da frase →  
  > exemplo
- Listas com marcadores:
  * item 1  
  * item 2  
  ou  
  - item 1  
  - item 2
- Listas numeradas:
  1. passo 1  
  2. passo 2

⚠️ Use essa formatação sempre que for útil para deixar a resposta mais clara, elegante e organizada.

🎯 Sua missão é auxiliar o usuário a:
- Entender melhor seus gastos
- Economizar dinheiro de forma consciente
- Tomar decisões financeiras mais inteligentes

🧠 Seu papel é ser claro, útil e educativo:
- Explique os conceitos quando necessário, especialmente se o usuário demonstrar dúvida.
- Dê orientações com base em boas práticas de educação financeira.
- Evite simplificações excessivas: prefira ser didático, mesmo em explicações curtas.

🔒 Regras importantes:
- Você deve **responder apenas perguntas relacionadas ao universo financeiro**.
- Caso receba mensagens fora desse tema, recuse educadamente e oriente o usuário de volta ao foco.
- Suas respostas devem ser **claras, bem estruturadas e com linguagem acessível**, mas sem se alongar demais desnecessariamente.

🧭 Sobre as mensagens:
Você pode receber entradas vindas do usuário ou do sistema.
- Mensagens do usuário virão com o prefixo `[user]`
- Mensagens do sistema virão com o prefixo `[sys]`

Use essas marcações para entender melhor o contexto antes de responder.
"""



actions = ["registrar_gasto", "consultar_gastos", "ajuda","conversa"]

db_users = TinyDB('data/users.json')
db_expenses = TinyDB('data/expenses.json')

User = Query()

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-2.0-flash')


import json
import re

def parse_json_response(text):
    """
    Limpa blocos de markdown como ```json e prefixos como >>> ou >, e converte a string JSON
    em uma lista de dicionários Python. Se a resposta contiver apenas um objeto JSON, ele será
    encapsulado em uma lista para padronizar a saída.
    """
    if not isinstance(text, str):
        print("Erro: entrada não é uma string.")
        return []

    # Remove blocos markdown como ```json ... ```
    text = text.strip()
    text = re.sub(r"^```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text, flags=re.IGNORECASE)

    # Remove prefixos de linha tipo >>> ou > com ou sem espaços
    text = re.sub(r"^\s*(>{1,3})\s?", "", text, flags=re.MULTILINE)

    # Limpa espaços finais
    text = text.strip()

    try:
        data = json.loads(text)

        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            print("Formato inesperado de JSON.")
            return []

    except json.JSONDecodeError as e:
        print("Erro ao converter JSON:", e,f"\n{text}")
        return []


def parser(msg):

    prompt = f"""
    Você é um analisador de mensagens para um assistente financeiro.

    Sua tarefa é interpretar a mensagem a seguir e retornar um JSON com **uma lista de intenções detectadas**, no seguinte formato:

    [
    {{
        "intencao": "registrar_gasto",
        "dados": {{
        "valor": 15.0,
        "categoria": "alimentação",
        "descricao": "leite",
        "data": "2025-04-05",
        "mes": "2025-04"
        }}
    }},
    {{
        "intencao": "registrar_gasto",
        "dados": {{
        "valor": 10.0,
        "categoria": "transporte",
        "descricao": "uber",
        "data": "2025-04-05",
        "mes": "2025-04"
        }}
    }},
    {{
        "intencao": "consultar_gastos",
        "dados": {{
        "mes": "2025-04"
        }}
    }}
    ]

    📌 Regras:
    - Cada item da lista deve conter:
    - "intencao": uma das opções válidas: {actions}
    - "dados": um único conjunto de dados associado à intenção
    - Mesmo que existam várias intenções iguais (ex: vários gastos), **crie uma entrada separada para cada uma**
    - Se não houver dados relevantes, use um objeto vazio: {{}}

    📦 Campos esperados para "registrar_gasto":
    - "valor": número decimal
    - "categoria": texto
    - "descricao": texto opcional
    - "data": no formato yyyy-mm-dd (use a data atual se não informado: {get_full_date()})
    - "mes": no formato yyyy-mm (derivado da data)

    🧾 Mensagem: "{msg}"

    ⚠️ Retorne o resultado como JSON válido, com aspas duplas, sem markdown, sem explicações adicionais.
    """


    answer = call_gemini(prompt)
    return parse_json_response(answer)

    

def call_gemini(prompt):

    response = model.generate_content(prompt)
    return response.text

def format_output_llm(text: str) -> str:
    text = text.replace('•', '*')
    
    text = '\n'.join(line.strip() for line in text.strip().splitlines() if line.strip())
    
    return textwrap.indent(text, '', predicate=lambda _: True)

def get_full_date():
    return datetime.now().strftime("%Y-%m-%d")

class Chatbot(object):
    def __init__(self):
        self.messenger = WhatsApp(wpp_token,phone_number_id=chatbot_number)
        
        
    def send_message(self,number = personal_number,msg="Resposta teste"):
        try:
            self.messenger.send_message(msg, number)
        except Exception as e:
            print(f"Error Chatbot {e}")
    
    def save_user_message(self,text,contact):
        number = contact["wa_id"]
        name = contact["profile"]["name"]
            
        db_users.insert({
            "timestamp": datetime.now().isoformat(),
            "number": number,
            "text": text,
            "name":name,
            "role":"user"
        })
        
    def recieve_message(self,msg,contact):
        if msg["type"] == "text":

            number = contact["wa_id"]
            name = contact["profile"]["name"]
            text = msg["text"]["body"]
            
            list_actions= parser(text)
            text = f"[user]:{text}"
            # actions = ["registrar_gasto", "consultar_gastos", "ajuda"]
            sys_info = ""
            for act in list_actions:
                intetion = act["intencao"]
                print(intetion)
                if intetion in ["conversa","ajuda"]:
                    sys_info += f"""\n[sys]: O usuario quer {intetion}"""
                elif intetion == "registrar_gasto":
                    
                    try:
                        dados = act["dados"]
                        
                        db_expenses.insert({
                        "tipo":"gasto",
                        "valor":float(dados["valor"]),
                        "categoria":dados["categoria"],
                        "mes":dados["mes"],
                        "data":dados["data"],
                        "descricao":dados["descricao"],
                        "number":number
                        })
                        sys_info += f"""\n[sys]: gasto salvo com successo"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar o gasto motivo: {e}"""
                    
                elif intetion == "consultar_gastos":
                    
                    try:
                        data = db_expenses.search((User.number == number)|(User.tipo=="gasto"))
                        sys_info += f"""\n[sys]: informações resgatadas com sucesso: {data}"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar resgatar os dados solicitados: {e}"""
                    
            
            prompt = f"""{text}\n{sys_info}"""
            self.save_user_message(prompt,contact)
            response = self.chat_with_gemini(prompt,contact)
            self.send_message(number=number,msg=response)
            
            # if msg_info["intencao"] == "conversa":
            #     response = self.chat_with_gemini(text,contact)
            #     self.send_message(number=number,msg=response)
                
            # elif msg_info["intencao"] == "registrar_gasto":
            #     dados = msg_info["dados"]
                
            #     db_expenses.insert({
            #         "tipo":"gasto",
            #         "valor":int(dados["valor"]),
            #         "categoria":dados["categoria"],
            #         "mes":dados["mes"],
            #         "data":dados["data"],
            #         "descricao":dados["descricao"],
            #         "number":number
            #     })
            #     text = f"""
            #     {text}
                
            #     [sys]: O seu gasto foi salvo com sucesso no banco de dados.
            #     """

            #     response = self.chat_with_gemini(text,contact)
            #     self.send_message(number=number,msg=response)
            # elif msg_info["intencao"] == "consultar_gastos":
                
            #     data = db_expenses.search((User.number == number)|(User.tipo=="gasto"))
            #     text = f"""
            #     {text}
                
            #     [sys]: banco de dados retornou {str(data)}
            #     """

            #     response = self.chat_with_gemini(text,contact)
            #     self.send_message(number=number,msg=response)
                
            # else:
                
            #     text = f"""
            #     {text}
                
            #     [sys]: A intenção "{msg_info['intencao']}" ainda não está disponível no sistema. Informe o usuário de forma educada que essa funcionalidade ainda não foi implementada e que, por isso, você não poderá ajudá-lo com isso no momento. Em seguida, pergunte se ele gostaria de ajuda com outra coisa relacionada às finanças.
            #     """

            #     response = self.chat_with_gemini(text,contact)
            #     self.send_message(number=number,msg=response)
            #self.send_message(number=number,msg=response)
            
    def chat_with_gemini(self,text,contact):
        
        number = contact["wa_id"]
        name = contact["profile"]["name"]
        
        history = self.load_history(number)
        chat = model.start_chat(history=history)
        response = chat.send_message(text).text
        
        db_users.insert({
            "timestamp": datetime.now().isoformat(),
            "number": number,
            "text": response,
            "name":name,
            "role":"model"
        })
        
        return response
    
    def load_history(self,number):
        result = db_users.search(User.number == number)
        if result:
            history = [{"role":"user","parts":initial_prompt}]
            for msg in result:
                msg = dict(msg)
                history.append({"role":msg['role'], "parts":msg["text"]})
            return history
        return []        
    
def main():
    answer = db_users.search((User.number == personal_number)|(User.tipo=="gasto"))
    
    for data in answer:
        data = dict(data)
        print(f"{data['role']}: ",data["text"])

    
    pass
    
if __name__=="__main__":
    main()