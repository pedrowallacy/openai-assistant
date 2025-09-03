# 🤖 Multi-Assistente Chat (Flask + Vue.js)

Este projeto integra **Flask (backend)** e **Vue.js (frontend)** para criar uma interface de chat com múltiplos assistentes da OpenAI.  
Cada assistente é acessado por rotas diferentes e mantém histórico de conversas (threads) com estado persistente na sessão.

---

## 🚀 Funcionalidades
- 🔹 Backend Flask integrado com OpenAI Assistants API  
- 🔹 Suporte a múltiplos assistentes via rotas (`/chat/<rota_assistente>`)  
- 🔹 Persistência de threads por sessão  
- 🔹 Endpoint para recuperar nome do assistente  
- 🔹 Frontend Vue.js com:
  - Efeito de digitação
  - Histórico de mensagens
  - Edição de perguntas do usuário
  - Botão de cópia para respostas
  - Tela de boas-vindas personalizada  

---

## 🛠️ Tecnologias
- **Backend**: Flask, Flask-CORS, Python, OpenAI API  
- **Frontend**: Vue.js 3, Composition API  
- **Outros**: dotenv para variáveis de ambiente  

---

## 📂 Estrutura
- `app.py` → Backend Flask que gerencia rotas, threads e comunicação com OpenAI  
- `helloworld.vue` → Componente Vue que renderiza o chat e interage com o backend  

---

## ⚙️ Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/pedrowallacy/openai-assistant.git
   cd openai-assistant
