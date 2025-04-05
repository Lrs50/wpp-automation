
# 📄 Webhook Payload – WhatsApp Cloud API

Este documento descreve o conteúdo do webhook recebido ao usar a **API do WhatsApp Cloud**. O webhook envia notificações sempre que uma nova **mensagem**, **reação**, ou outro evento relevante acontece.

---

## 📦 Estrutura Geral

```json
{
  "object": "whatsapp_business_account",
  "entry": [ ... ]
}
```

- `object`: Sempre será `"whatsapp_business_account"`
- `entry`: Lista de eventos recebidos
  - Cada `entry` representa uma notificação para um número do WhatsApp Business

---

## 🔁 Campo `entry[]`

Cada item possui:

| Campo         | Tipo    | Descrição                                      |
|---------------|---------|-----------------------------------------------|
| `id`          | string  | ID da conta do WhatsApp Business               |
| `changes`     | array   | Mudanças associadas a esse evento              |

---

## 🔄 Campo `changes[]`

Cada item possui:

| Campo       | Tipo    | Descrição                     |
|-------------|---------|-------------------------------|
| `field`     | string  | Tipo de evento (`messages`)   |
| `value`     | object  | Dados do evento               |

---

## 🔍 Campo `value`

### Metadados

```json
"metadata": {
  "display_phone_number": "15556479575",
  "phone_number_id": "631900040002412"
}
```

- `display_phone_number`: Número comercial que enviou/recebeu a mensagem
- `phone_number_id`: ID do número na conta da API

---

### Contato

```json
"contacts": [
  {
    "profile": { "name": "Lucas Reis" },
    "wa_id": "557599646980"
  }
]
```

- `profile.name`: Nome do usuário que enviou a mensagem
- `wa_id`: ID do WhatsApp (número formatado internacionalmente, sem +)

---

## 💬 Mensagens (`messages[]`)

A lista `messages` contém uma ou mais mensagens enviadas pelo usuário.

---

### 📄 Exemplo 1: Mensagem de texto

```json
{
  "from": "557599646980",
  "id": "wamid.XXXX",
  "timestamp": "1743797149",
  "text": {
    "body": "testando"
  },
  "type": "text"
}
```

| Campo       | Tipo    | Descrição                                      |
|-------------|---------|-----------------------------------------------|
| `from`      | string  | Número de quem enviou a mensagem               |
| `id`        | string  | ID único da mensagem                           |
| `timestamp` | string  | Timestamp (em segundos Unix)                   |
| `type`      | string  | Tipo da mensagem (`text`)                      |
| `text.body` | string  | Conteúdo textual da mensagem                   |

---

### ❤️ Exemplo 2: Reação (emoji)

```json
{
  "from": "557599646980",
  "id": "wamid.XXXX",
  "timestamp": "1743797190",
  "type": "reaction",
  "reaction": {
    "message_id": "wamid.XXXX",
    "emoji": "❤️"
  }
}
```

| Campo                 | Tipo    | Descrição                                      |
|-----------------------|---------|-----------------------------------------------|
| `type`                | string  | `"reaction"`                                   |
| `reaction.message_id` | string  | ID da mensagem que recebeu a reação           |
| `reaction.emoji`      | string  | Emoji enviado como reação                      |

---

## 🧠 Observações Importantes

- O campo `type` define a estrutura que estará presente em cada mensagem (`text`, `reaction`, `image`, etc.).
- Timestamps estão no formato **Unix Epoch** (segundos desde 1970).
- O campo `wa_id` é usado para identificar o remetente e pode ser útil para respostas.
