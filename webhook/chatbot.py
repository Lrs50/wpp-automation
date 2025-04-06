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


actions = ["registrar_gasto", "consultar_gastos","registrar_divida","consultar_divida","conversa","registrar_anotacao","resgatar_anotacao"]

initial_prompt = f"""
Você é um assistente financeiro inteligente chamado *Bot da Grana*, que interage com os usuários exclusivamente através do WhatsApp.

📱 Como chatbot do WhatsApp, suas respostas devem seguir **estritamente a formatação suportada pela plataforma**.  
Não use Markdown tradicional (como `**negrito**` ou `__itálico__`), apenas os formatos reconhecidos pelo WhatsApp.  

✅ *Formatação correta no WhatsApp:*
- *Negrito:* use asteriscos → *exemplo*
- _Itálico:_ use sublinhados → _exemplo_
- ~Tachado:~ use til → ~exemplo~
- `Código:` use um acento grave (`) → `exemplo`
- ```Monoespaçado:``` use três acentos graves → ```exemplo```
- Citações: use `>` antes da linha →  
  > exemplo
- Listas com marcadores:
  - item 1  
  - item 2
- Listas numeradas:
  1. item 1  
  2. item 2

⚠️ Use sempre essa formatação para tornar suas mensagens claras, organizadas e visualmente agradáveis no WhatsApp.

🎯 Sua missão é auxiliar o usuário a:
- Entender melhor seus gastos
- Economizar dinheiro de forma consciente
- Tomar decisões financeiras mais inteligentes
- Ser um assistente pessoal para as necessidades diarias

🧠 Seu papel é ser claro, útil e educativo:
- Explique os conceitos sempre que necessário
- Ofereça orientações com base em boas práticas de educação financeira
- Prefira ser didático e direto, sem simplificações excessivas ou respostas muito longas

🔒 Regras de conduta:
- Responda **somente perguntas relacionadas ao universo financeiro**
- Recuse com gentileza temas fora do seu domínio, e oriente o usuário de volta ao foco
- Mantenha a linguagem acessível, objetiva e organizada

🧭 Sobre as mensagens:
Você receberá mensagens do usuário ou do sistema:
- Mensagens do usuário virão com o prefixo `[user]`
- Mensagens do sistema virão com o prefixo `[sys]`

Sempre utilize essas marcações para compreender o contexto antes de responder.
Você pode processar as seguintes ações internas: {actions}.
Essas ações representam funcionalidades importantes, mesmo que não estejam descritas de forma diretamente compreensível para o usuário final.
Sempre que apropriado, comunique essas funcionalidades de maneira clara, amigável e acessível — como, por exemplo:
“Posso te ajudar a registrar um gasto”, “Quer ver seus gastos anteriores?”, ou “Se quiser, posso anotar uma dívida para você”.

📌 Políticas e boas práticas com base nas intenções recebidas:

- ❌ *Você não pode atualizar registros anteriores de gastos ou dívidas.*
  - Se o usuário quiser corrigir uma informação (por exemplo, “na verdade o valor era 20”), **responda com gentileza** e registre a correção como uma observação, usando a funcionalidade `"registrar_anotacao"`.
  - Exemplo de resposta:
    > _Beleza! Não consigo mudar o que foi registrado, mas posso anotar essa correção pra você._ 😊

- ✅ *Você pode salvar e consultar anotações ou observações importantes.*
  - Quando a intenção for `"registrar_anotacao"`, armazene o conteúdo como uma anotação pessoal do usuário.
  - Quando a intenção for `"resgatar_anotacao"`, tente recuperar a informação e, caso ela não exista, **responda de forma acolhedora e proativa**, como:
    > _Ainda não tenho isso salvo, mas posso lembrar se quiser me contar agora._ 😉

- 💡 *Ao responder perguntas ou análises sobre gastos e dívidas*, sempre que possível **considere também as observações registradas**, pois elas podem conter correções ou contexto adicional relevante.

Adapte a linguagem ao contexto da conversa para tornar a interação natural e acolhedora.
"""


db = TinyDB('data/users.json')

User = Query()

genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-2.0-flash')

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
    - A data atual é {get_full_date()}.
    - Sempre que a entrada do usuário contiver uma referência de tempo relativa — como "ontem", "hoje", "anteontem", "semana passada", "último sábado", etc. —, interprete essa referência com base nessa data atual.
    Converta essas expressões em datas absolutas.
    Por exemplo:
        - "ontem" deve ser interpretado como a data de um dia antes de {get_full_date()}
        - "semana passada" deve ser interpretada como sete dias antes de {get_full_date()}
        - "última terça" deve ser a terça-feira anterior à data atual
    - Utilize essas datas absolutas nos resultados, mesmo que o usuário tenha usado linguagem relativa
    - ⚠️ **Todos os campos opcionais devem estar presentes no JSON, mesmo que vazios (ex: "descricao": "")**

    📌 Importante:

    - Apenas informações sobre **gastos** e **dívidas** são utilizadas diretamente em análises, relatórios ou consultas específicas.
    - Qualquer outra informação que o usuário deseje guardar e que pareça importante (como lembretes, anotações, correções, compromissos, fatos relevantes ou informações pessoais — como nome, CPF, etc.) deve ser registrada com a intenção `"registrar_anotacao"`, mesmo que não esteja relacionada a dinheiro.
    - Se o usuário disser algo como "meu nome é Lucas", isso deve ser salvo como `"registrar_anotacao"`. Se ele disser "qual é o meu nome?", isso deve ser interpretado como `"resgatar_anotacao"`.
    - ⚠️ Mesmo que a informação ainda não tenha sido registrada, a intenção `"resgatar_anotacao"` deve ser usada normalmente. Isso permite que o assistente responda de forma gentil, como: "Ainda não sei o seu nome, mas posso lembrar se você quiser me contar. 😊"
    - O modelo **não deve dizer que não tem acesso a informações pessoais**. Em vez disso, deve assumir que essas informações podem ter sido registradas anteriormente e sempre responder com simpatia e utilidade.
    - ❌ O modelo **não pode atualizar registros anteriores de gastos ou dívidas**.
    - ✅ Se o usuário quiser corrigir uma informação sobre um gasto ou dívida (ex: "na verdade o valor era 20"), essa correção deve ser registrada como uma nova intenção `"registrar_anotacao"`, salvando a observação como uma anotação separada.
    - 💡 **Boa prática**: ao processar mensagens que envolvem **análises ou solicitações sobre dívidas ou gastos**, é apropriado sempre considerar também as informações registradas como `"informacao_importante"` que possam fornecer contexto adicional, histórico ou observações relevantes. Isso ajuda o assistente a oferecer respostas mais completas, personalizadas e corretas.
     - É estritamente proibido realizar solicitações repetidas do mesmo tipo de dado em uma única requisição.
        - Solicitações duplicadas são redundantes, pois a base de dados consultada é a mesma.
        - Você pode requisitar múltiplos tipos de dados diferentes, mas cada tipo de solicitação deve ocorrer apenas uma vez por requisição.
    
    📦 Campos esperados para "registrar_gasto":
    - "valor": número decimal
    - "categoria": texto
    - "descricao": texto opcional
    - "data": no formato yyyy-mm-dd (use a data atual se não informado)
    - "mes": no formato yyyy-mm (derivado da data)

    📦 Campos esperados para "registrar_divida":
    - "valor": número decimal (ex: 120.50)
    - "pessoa": nome da pessoa envolvida na dívida
    - "direcao": indica a natureza da transação. Pode ser:
        - "receber": alguém te deve
        - "pagar": você deve para alguém
        - "recebido": alguém pagou o que te devia
        - "pago": você quitou o que devia
    - "descricao": texto opcional com o motivo ou contexto da dívida (ex: "almoço", "empréstimo")
    - "data": no formato yyyy-mm-dd (use a data atual se não informado)
    - "mes": no formato yyyy-mm (derivado da data)

    📦 Campos esperados para "registrar_anotacao":
    - "info": a informação considerada importante
    - "data": no formato yyyy-mm-dd (use a data atual se não informado)
    - "mes": no formato yyyy-mm (derivado da data)

    🧾 Mensagem: "{msg}"

    ⚠️ Retorne o resultado como JSON válido, com aspas duplas, sem markdown, sem explicações adicionais.
    """


    answer = call_gemini(prompt)
    return parse_json_response(answer)

def adicionar_db(numero, tipo, dados):
    # Verifica se o número já existe no banco
    usuario = db.get(User.number == numero)

    if not usuario:
        # Se não existir, cria a estrutura inicial
        usuario = {
            "number": numero,
            "gastos": {},
            "dividas": {},
            "chat":[],
            "key_info":{}
        }
        db.insert(usuario)
        usuario = db.get(User.number == numero)

    # Atualiza o documento com o novo item
    if tipo == "gasto":
        
        if dados["mes"] not in usuario["gastos"]:
            usuario["gastos"][dados["mes"]] = []
        
        usuario["gastos"][dados["mes"]].append(dados)
        
    elif tipo == "divida":
        
        if dados["pessoa"] not in usuario["dividas"]:
            usuario["dividas"][dados["pessoa"]] = []
        
        usuario["dividas"][dados["pessoa"]].append(dados)
        
    elif tipo == "chat":
        usuario["chat"].append(dados)
    elif tipo == "key_info":
        
        if dados["mes"] not in usuario["key_info"]:
            usuario["key_info"][dados["mes"]] = []
        
        usuario["key_info"][dados["mes"]].append(dados)
    else:
        raise ValueError("Tipo inválido!")

    # Atualiza no banco
    db.update(usuario, User.number == numero)    
    
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
        
    def recieve_message(self,msg,contact):
        if msg["type"] == "text":

            number = contact["wa_id"]
            name = contact["profile"]["name"]
            text = msg["text"]["body"]
            
            list_actions= parser(text)
            text = f"[user]:{text}"
            #actions = ["registrar_gasto", "consultar_gastos","registrar_divida","consultar_divida", "ajuda","conversa"]
            sys_info = ""
            
            repete = set()
            
            for act in list_actions:
                intention = act["intencao"]
                
                if ("resgatar" in intention) and (intention in repete):
                    continue
                
                repete.add(intention)
                    
                print(intention)
                if intention in ["conversa","ajuda"]:
                    sys_info += f"""\n[sys]: O usuario quer {intention}"""
                    
                elif intention == "registrar_gasto":
                    
                    try:
                        dados = act["dados"]
                        
                        new_data = {
                        "valor":float(dados["valor"]),
                        "categoria":dados["categoria"],
                        "mes":dados["mes"],
                        "data":dados["data"],
                        "descricao":dados["descricao"],
                        "timestamp": datetime.now().isoformat(),
                        }
                        
                        adicionar_db(number,"gasto",new_data)
                        
                        sys_info += f"""\n[sys]: gasto salvo com successo"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar o gasto motivo: {e}"""
                    
                elif intention == "consultar_gastos":
                    
                    try:
                        data = db.get(User.number == number)
                        data = data["gastos"]
                        sys_info += f"""\n[sys]: informações resgatadas com sucesso: {data}"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar resgatar os dados solicitados: {e}"""
                
                elif intention == "registrar_divida":   
                    try:
                        dados = act["dados"]
                        
                        new_data = {
                        "valor":float(dados["valor"]),
                        "pessoa": dados["pessoa"],
                        "direcao":dados["direcao"],
                        "mes":dados["mes"],
                        "data":dados["data"],
                        "descricao":dados["descricao"],
                        "timestamp": datetime.now().isoformat()
                        }
                        
                        adicionar_db(number,"divida",new_data)
                        
                        sys_info += f"""\n[sys]: divida salvo com successo"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar o divida motivo: {e}"""
                
                elif intention == "consultar_divida":
                    try:
                        data = db.get(User.number == number)
                        data = data["dividas"]
                        sys_info += f"""\n[sys]: informações resgatadas com sucesso: {data}"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar resgatar os dados solicitados: {e}"""
                
                elif intention == "registrar_anotacao":
                    try:
                        dados = act["dados"]
                        new_data = {
                        "info":dados["info"],
                        "mes":dados["mes"],
                        "data":dados["data"],
                        "timestamp": datetime.now().isoformat()
                        }
                        
                        adicionar_db(number,"key_info",new_data)
                        sys_info += f"""\n[sys]: informação salvo com successo"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar a informação motivo: {e}"""
                        
                elif intention == "resgatar_anotacao":
                    try:
                        data = db.get(User.number == number)
                        data = data["key_info"]
                        sys_info += f"""\n[sys]: informações resgatadas com sucesso: {data}"""
                    except Exception as e:
                        sys_info += f"""\n[sys]: falha ao salvar resgatar os dados solicitados: {e}"""
                
            prompt = f"""{text}\n{sys_info}"""
            
            new_data = {
                "msg": prompt,
                "role":"user",
                "timestamp": datetime.now().isoformat(),
            }
            adicionar_db(number,"chat",new_data)
            
            response = self.chat_with_gemini(prompt,contact)
            
            new_data = {
                "msg": response,
                "role":"model",
                "timestamp": datetime.now().isoformat(),
            }
            adicionar_db(number,"chat",new_data)
            
            self.send_message(number=number,msg=response)
            
    def chat_with_gemini(self,text,contact):
        
        number = contact["wa_id"]
        
        history = self.load_history(number)
        chat = model.start_chat(history=history)
        response = chat.send_message(text).text
        
        return response
    
    def load_history(self,number):
        result = db.get(User.number == number)
        result = result["chat"][:50]
        history = [{"role":"user","parts":initial_prompt}]
        if result:
            for msg in result:
                history.append({"role":msg['role'], "parts":msg["msg"]})
                
        return history        
    
def main():
    data = db.get(User.number == personal_number)
    
    pprint(data)

    pass
    
if __name__=="__main__":
    main()