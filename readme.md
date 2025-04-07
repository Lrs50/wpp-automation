# 💰 Bot da Grana – Chatbot Financeiro Pessoal via WhatsApp

Um assistente financeiro pessoal no WhatsApp que ajuda você a registrar gastos, controlar dívidas, definir orçamentos e tirar dúvidas sobre economia e assuntos correlatos. Tudo de forma simples, automatizada e com linguagem natural.

---

## ⚙️ Funcionamento

O funcionamento do bot segue o seguinte fluxo:

1. **Envio de Mensagem pelo Usuário**
   - O usuário envia uma mensagem pelo **WhatsApp**, que é encaminhada pela **API do WhatsApp Cloud** para o webhook da aplicação.

2. **Webhook com FastAPI**
   - O webhook, implementado com **FastAPI** e exposto via **Ngrok**, recebe a mensagem e a encaminha para o **backend** da aplicação.

3. **Parser Inteligente**
   - A primeira etapa de processamento utiliza um **parser** que combina **expressões regulares** com o **modelo Gemini (stateless)**.
   - O parser interpreta a intenção do usuário e transforma a mensagem em uma **requisição JSON estruturada**.
   - As requisições podem ser de dois tipos:
     - **Registro:** salvar gastos, dívidas, orçamentos, etc.
     - **Consulta:** recuperar dados previamente armazenados.

4. **Banco de Dados**
   - Utilizamos o **TinyDB**, um banco de dados **não relacional** e leve, para armazenar as informações dos usuários.

5. **Resposta Inteligente**
   - A requisição é passada para outra instância do modelo **Gemini**, que utiliza o contexto necessário (incluindo dados do banco) para gerar uma resposta personalizada ao usuário.

6. **Envio da Resposta**
   - A resposta é enviada de volta ao usuário através da biblioteca **Heyoo**, que integra com a API do WhatsApp Cloud.

Esse ciclo se repete continuamente, permitindo uma **conversa fluida e inteligente** entre o usuário e o bot.

---

## 🧰 Tecnologias Utilizadas

- [FastAPI](https://fastapi.tiangolo.com/)
- [Ngrok](https://ngrok.com/)
- [Gemini API](https://ai.google.dev/)
- [Heyoo](https://pypi.org/project/heyoo/)
- [TinyDB](https://tinydb.readthedocs.io/en/latest/)
- [Regex](https://docs.python.org/3/library/re.html)

---