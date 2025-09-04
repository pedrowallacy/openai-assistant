from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import session 
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()


app = Flask(__name__)
from flask_cors import CORS

CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_key")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROTAS_ASSISTENTES = {
    "legislador": os.getenv("ASSISTANT_ID_LEGISLADOR"),
    "pedro": os.getenv("ASSISTANT_ID_PEDRO"),
    "maxsei": os.getenv("ASSISTANT_ID_MAXSEI")
}

def enviar_para_assistente(assistant_id, pergunta, rota_assistente):
    thread_key = f"thread_id_{rota_assistente}"
    thread_id = session.get(thread_key)
    
    if not thread_id:
        # Se não houver thread_id na sessão, cria uma nova thread
        thread = client.beta.threads.create()
        thread_id = thread.id
        session[thread_key] = thread.id
        print(f"Nova thread criada para {rota_assistente}: {thread_id}")
    else:
        # Se já houver thread_id na sessão, usa a thread existente
        print(f"Usando thread existente {rota_assistente}: {thread_id}")

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=pergunta
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    esperar_run_finalizar(thread_id, run.id)
    
    mensagens = client.beta.threads.messages.list(thread_id=thread_id)
    print(f"mensagens {mensagens}")

    # Filtra as mensagens do assistente
    respostas_assistente = [m for m in mensagens.data if m.role == "assistant"]

    print(f"respostas_assistente {respostas_assistente}")

    if respostas_assistente:
        ultima_resposta = respostas_assistente[0].content[0].text.value  # geralmente a resposta mais recente vem primeiro
        return ultima_resposta
    else:
        return "Nenhuma resposta do assistente foi encontrada."


def esperar_run_finalizar(thread_id, run_id, timeout=30):
    """
    Aguarda até que o run seja concluído ou até atingir o timeout.
    """
    tempo_inicial = time.time()
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run_status.status == "completed":
            return
        elif run_status.status in ["failed", "cancelled", "expired"]:
            raise Exception(f"Execução falhou com status: {run_status.status}")
        elif time.time() - tempo_inicial > timeout:
            raise TimeoutError("Timeout ao aguardar o run do assistente.")
        time.sleep(0.1) 

@app.route("/version")
def version():
    return jsonify({"version": "1.0.0"})

@app.route("/", methods=["POST"])
def send_message():
    print("entrou no barra send_message")    
    pergunta = request.form.get("pergunta")
    resposta, _ = enviar_para_assistente(ROTAS_ASSISTENTES.get("suporte"), pergunta)
    return jsonify({"resposta": resposta})

@app.route("/chat/<rota_assistente>", methods=["POST"])
def chat_especifico(rota_assistente):
    print(f"rota_assistente {rota_assistente}")
    print("entrou no barra chat_especifico")
    pergunta = request.form.get("pergunta", "")
    print(f"pergunta {pergunta}")
    assistant_id = ROTAS_ASSISTENTES.get(rota_assistente)
    print(f"assistant_id {assistant_id}")

    if not assistant_id:
        return jsonify({"erro": "Rota de assistente inválida"}), 404

    try:
        resposta = enviar_para_assistente(assistant_id, pergunta, rota_assistente)
        return jsonify({"resposta": resposta})
    except Exception as e:
        print(f"Erro ao enviar para assistente: {e}")
        return jsonify({"erro": str(e)}), 500
    
@app.route("/reset", methods=["POST"])
def reset_thread():
    session.pop("thread_id", None)
    return jsonify({"mensagem": "Thread reiniciada."})

# NOVO ENDPOINT PARA PEGAR O NOME DO ASSISTENTE
@app.route("/assistant_name/<rota_assistente>", methods=["GET"])
def get_assistant_name(rota_assistente):
    assistant_id = ROTAS_ASSISTENTES.get(rota_assistente)
    if not assistant_id:
        return jsonify({"erro": "Rota de assistente inválida"}), 404
    try:
        assistant = client.beta.assistants.retrieve(assistant_id)
        return jsonify({"name": assistant.name})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

print("ID do legislador:", ROTAS_ASSISTENTES["legislador"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
