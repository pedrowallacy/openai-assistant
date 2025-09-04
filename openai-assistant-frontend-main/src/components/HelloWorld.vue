<template>
  <div class="chat-container">
    <div class="chat-history" ref="chatHistory">
      <div v-if="showWelcome" class="welcome-center">
        <div class="welcome-banner">
          <h2>Olá{{ nomeAssistente ? `, sou  o assistente ${nomeAssistente}` : '' }}!</h2>
          <p>Como posso ajudá-lo hoje?</p>
        </div>
        <div class="input-container centered-input">
          <div class="input-inner">
            <textarea
  v-model="pergunta"          
  :disabled="loading || typingIndex !== null"
  placeholder="Digite sua pergunta"
  @input="autoResize"
  @keydown.enter.prevent="enviarPergunta"
  @keydown.enter.shift="null"
  rows="1"
  class="chat-textarea"
/>
            <button 
              @click="typingIndex !== null ? togglePause() : enviarPergunta()" 
              :disabled="loading"
            >
              {{ typingIndex !== null ? '⏸️' : '➤' }}
            </button>
          </div>
        </div>
      </div>
      <template v-else>
        <div
          v-for="(msg, index) in historico"
          :key="index"
          :class="['chat-message', msg.role]"
        >
          <div class="message-container">
            <div class="chat-bubble-container">
              <div class="avatar" v-if="msg.role === 'assistant'">🤖</div>
              <div class="avatar user" v-if="msg.role === 'user'">🧑</div>
              <div class="bubble-content">
                <!-- Nome do assistente só para mensagens do assistente -->
                <p v-if="msg.role === 'assistant'" class="chat-author">{{ nomeAssistente }}</p>
                <div class="chat-bubble">
                  <template v-if="msg.role === 'assistant' && loading && index === historico.length - 1">
                    <div class="loading-indicator">
                      <span class="spinner"></span>
                      <span class="loading-text">Pensando...</span>
                    </div>
                  </template>
                  <template v-else-if="msg.role === 'assistant' && typingIndex === index">
                    {{ typingContent }}
                  </template>
                  <template v-else>
                    <template v-if="editingMessageIndex === index && msg.role === 'user'">
                      <textarea
                        v-model="editingContent"
                        class="edit-textarea"
                        @keydown.enter.prevent="saveEdit(index)"
                      ></textarea>
                      <button @click="saveEdit(index)" class="control-btn">✓</button>
                    </template>
                    <template v-else>
                      {{ msg.content }}
                    </template>
                  </template>
                </div>
              </div>
              <button 
                v-if="msg.role === 'user'"
                @click="startEditing(index, msg.content)"
                class="edit-btn"
              >
                ✎
              </button>
            </div>
            <!-- Botão de cópia abaixo da bolha, fora do container da resposta -->
            <div
  v-if="msg.role === 'assistant' && typingIndex !== index && !loading"
  class="copy-container"
>
  <button class="copy-btn" @click="copiarResposta(msg.content, index)">
    <template v-if="copyFeedbackIndex === index">
      <!-- Ícone de correto minimalista -->
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="11" cy="11" r="10" fill="#e6c200"/>
        <path d="M7 11.5l3 3 5-5" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </template>
    <template v-else>
      <!-- Ícone de cópia minimalista -->
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="6" y="6" width="10" height="12" rx="3" stroke="#b09821" stroke-width="1.5" fill="#fffbe6"/>
        <rect x="2.75" y="2.75" width="10.5" height="12.5" rx="3" stroke="#e6c200" stroke-width="1.5" fill="none"/>
      </svg>
    </template>
  </button>
</div>
          </div>
        </div>
      </template>
    </div>
    <div v-if="!showWelcome" class="input-container">
      <div class="input-inner">
        <textarea
          v-model="pergunta"
          :disabled="loading || typingIndex !== null"
          placeholder="Digite sua pergunta"
          @input="autoResize"
          @keydown.enter.prevent="enviarPergunta"
          @keydown.enter.shift="null"
          rows="1"
          class="chat-textarea"
        />
        <button 
          @click="typingIndex !== null ? togglePause() : enviarPergunta()" 
          :disabled="loading"
        >
          {{ typingIndex !== null ? '■' : '➤' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watchEffect, computed } from 'vue'

const pergunta = ref('')
const resposta = ref('')
const historico = ref([])
const chatHistory = ref(null)
const loading = ref(false)
const isPaused = ref(false)
const editingMessageIndex = ref(null)
const editingContent = ref('')

// --- Correção: tornar assistenteParam e rota reativos ---
const assistenteParam = ref(new URLSearchParams(window.location.search).get('assistente') || 'legislador')
const rota = computed(() => assistenteParam.value)

// Atualiza assistenteParam se a URL mudar (ex: usuário muda o parâmetro na barra de endereços)
window.addEventListener('popstate', () => {
  assistenteParam.value = new URLSearchParams(window.location.search).get('assistente') || 'legislador'
  
})

const nomeAssistente = ref('Assistente')
watchEffect(async () => {
  try {
    const res = await fetch(`http://localhost:5000/assistant_name/${rota.value}`)
    const data = await res.json()
    if (data.name) nomeAssistente.value = data.name
    else nomeAssistente.value = 'Assistente'
  } catch (e) {
    nomeAssistente.value = 'Assistente'
  }
})

// Typing effect state
const typingIndex = ref(null)
const typingContent = ref('')
let typingTimeout = null

const typeText = async (fullText, msgIndex) => {
  typingContent.value = ''
  typingIndex.value = msgIndex
  let i = 0
  function typeChar() {
    if (typingIndex.value !== msgIndex) return
    if (i <= fullText.length && !isPaused.value) {
      typingContent.value = fullText.slice(0, i)
      historico.value[msgIndex].content = typingContent.value
      i++
      typingTimeout = setTimeout(typeChar, 10)
    } else if (i <= fullText.length) {
      typingTimeout = setTimeout(typeChar, 100) // Continua checando se foi despausado
    } else {
      typingIndex.value = null
      typingContent.value = ''
    }
  }
  typeChar()
}

const togglePause = () => {
  isPaused.value = true;
  if (typingTimeout) {
    clearTimeout(typingTimeout);
  }
  // Reseta os estados de digitação
  typingIndex.value = null;
  //typingContent.value = '';
  // NÃO apague a última mensagem do assistente!
  // Apenas pare o efeito de digitação, mantendo o texto já exibido
}

const startEditing = (index, content) => {
  editingMessageIndex.value = index
  editingContent.value = content
}

const saveEdit = (index) => {
  if (editingContent.value.trim()) {
    historico.value[index].content = editingContent.value
  }
  editingMessageIndex.value = null
  editingContent.value = ''
}

const autoResize = (e) => {
  const ta = e.target;
  ta.style.height = 'auto';
  ta.style.height = ta.scrollHeight + 'px';
};


const showWelcome = computed(() => {
  // Esconde se houver pelo menos uma mensagem do usuário
  return !historico.value.some(msg => msg.role === 'user')
})

// Altere aqui para chamar o assistente "suporte pedro"
const enviarPergunta = async () => {
  isPaused.value = false;
  if (!pergunta.value.trim()) return
  const perguntaAtual = pergunta.value.trim();
  historico.value.push({ role: 'user', content: perguntaAtual })
  pergunta.value = ''

  // Resetar altura do textarea após limpar
  await nextTick(() => {
    const ta = document.querySelector('.chat-textarea');
    if (ta && !ta.value) {
      ta.style.height = '44px';
      ta.scrollTop = 0;
    }
  });

  loading.value = true
  historico.value.push({ role: 'assistant', content: '' })

  await nextTick(() => {
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  })

  // Use a rota reativa
  const res = await fetch(`http://localhost:5000/chat/${rota.value}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({ pergunta: perguntaAtual }),
    credentials: 'include'
  });

  const data = await res.json()
  loading.value = false
  await typeText(data.resposta, historico.value.length - 1)

  await nextTick(() => {
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  })
}

const copyFeedbackIndex = ref(null)
let copyTimeout = null
const showCopyGlobalFeedback = ref(false)

const copiarResposta = (texto, index) => {
  navigator.clipboard.writeText(texto)
  copyFeedbackIndex.value = index
  showCopyGlobalFeedback.value = true
  if (copyTimeout) clearTimeout(copyTimeout)
  copyTimeout = setTimeout(() => {
    copyFeedbackIndex.value = null
    showCopyGlobalFeedback.value = false
  }, 1200)
}
</script>

<style scoped>

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  height: 100%;
  background: #343541;
  font-family: 'Arial', 'Segoe UI', 'Roboto', sans-serif;
  color: #626298;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
}

.chat-container {
  align-items: end;
  position: fixed;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;      
  background: url("/backgroud_login.png") no-repeat center center;
  background-size: cover;
   left: 0;
  top: 0;
   margin: 0;
  padding: 0;
}

.chat-history::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 50px;
}

.chat-history {
  position: relative;
  display: flex;
  align-items: stretch;
  flex: 1;
  overflow-y: auto;
  padding:  0 0 120px 0;
  padding-bottom: 120px;
  display: flex;
  flex-direction: column;
  gap: 0;
  width: 100%; 
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: #a8a8a4;
  min-height: 0;
  margin: 0;
}

.chat-history::-webkit-scrollbar {
  width: 24px !important;
  min-width: 24px !important;
  max-width: 24px !important;
  background: transparent;
}

.chat-message {
  display: flex;
  flex-direction: column;
  max-width: 60%;
  width: 100%;
  margin-top: 18px;
}

.chat-message.user {
  align-items: flex-end;
  margin-left: auto;
  margin-right: auto;
}

.chat-message.assistant {
  align-items: flex-start;
  margin-left: auto;
  margin-right: auto;
}

.chat-bubble-container {
  display: flex;
  flex-direction: row; /* Ícone à esquerda, mensagem à direita */
  align-items: center;
  gap: 8px;
}

.chat-message.user .chat-bubble-container {
  flex-direction: row; /* Ícone à esquerda, mensagem à direita */
}

.bubble-content {
  flex: 1;
}

.chat-bubble {
  background: #f9ecd2;
  color: #7a6a2f;
  border-radius: 18px 18px 6px 18px;
  padding: 18px 28px;
  border: 1.5px solid #e6c20033; /* dourado translúcido */
  box-shadow: 0 2px 8px rgba(191, 160, 70, 0.08);
  font-size: 1.12em;
  transition: box-shadow 0.2s;
}

.chat-message.assistant .chat-bubble {
  background: #fffbe6;
  color: #b09821;
  border-radius: 18px 18px 18px 6px;
  border: 1.5px solid #e6c20022;
}

.chat-message.assistant .chat-bubble {
  margin-right: 20px;
  background: none;
  color: #3a3521;
  border: none;
}

.chat-message.user .chat-bubble {
  margin-left: 20px;
  background: #f9ecd2;
  color: #7a6a2f;
  border-radius: 12px;
  border: 1.5px solid #e6c200;
  box-shadow: 0 2px 8px rgba(191, 160, 70, 0.10);
}

/*container de entrada*/
.input-container {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background: transparent;
  box-shadow: none;
  z-index: 1000;
  gap: 80px;
  margin-top: auto;
  border-top: none;
}

.input-container:not(.centered-input) {
  flex-direction: column-reverse;
  align-items: center;
  display: flex;
}

.input-container:not(.centered-input) .chat-textarea {
  min-height: 44px;
  max-height: 180px !important;
  overflow-y: auto;
  resize: none;
  height: auto;
}

/*entrada da pergunta*/
.input-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 820px;
  background: #f9ecd2; /* bege claro */
  border-radius: 32px;
  padding: 12px 28px;
  box-shadow: 0 2px 16px 0 rgba(191, 160, 70, 0.10);
  border: 1.5px solid #e6c200;
  transition: box-shadow 0.2s;
}

/*entrada da pergunta*/
.input-inner:focus-within {
  box-shadow: 0 4px 24px 0 rgba(191, 160, 70, 0.18);
  border-color: #b09821;
  background: #fbe7b3; /* bege mais intenso ao focar */
}

/*entrada da pergunta*/
.input-inner input {
  flex: 100%;
  height: 44px;
  background: transparent;
  border: none;
  color: #7a6a2f;
  font-size: 1.13em;
  outline: none;
  padding: 10px 12px;
  resize: none;
  font-family: inherit;
}

/*input da pergunta*/
.input-inner input::placeholder {
  color: #bfa046;
  opacity: 0.7;
  font-size: 1.13em;
  font-family: inherit;
  font-weight: 100;
}

/*botão de enviar*/
.input-inner button {
  background: linear-gradient(90deg, #e6c200 60%, #b09821 100%);
  color: #fff;
  border-radius: 24px;
  min-width: 90px;
  height: 44px;
  font-size: 1.15em;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(191, 160, 70, 0.10);
  transition: background 0.2s, box-shadow 0.2s, color 0.2s;
  border: none;
}

/*botão de enviar*/
.input-inner button:hover {
  background: linear-gradient(90deg, #b09821 60%, #e6c200 100%);
  color: #fffbe6;
  box-shadow: 0 4px 16px rgba(191, 160, 70, 0.18);
}

/* Exemplo para mudar só no chat: */
.chat-container, .chat-history, .chat-message, .chat-bubble, .input-inner, .input-inner input, .input-inner button {
  font-family: 'Arial', 'Segoe UI', 'Roboto', sans-serif;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  font-style: italic;
  color: #b09821;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: #e6c200;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

.loading-text {
  color: #7a6a2f;
  font-size: 1em;
  margin-left: 10px;
  display: inline-block;
}

.chat-bubble > .spinner,
.chat-bubble > .loading-text {
  background: none !important;
  box-shadow: none !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

.chat-bubble .loading-indicator {
  background: none;
  box-shadow: none;
  border: none;
}

.chat-message.assistant .chat-bubble:has(.spinner) {
  background: none !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.welcome-banner {
  width: 100%;
  max-width: 700px;
  margin: 250px auto 0 auto;
  padding: 32px 24px 18px 24px;
  background: none;
  border-radius: 24px;
  box-shadow:none;
  text-align: center;
  border: none;
}

.welcome-banner h2 {
  margin: 0 0 8px 0;
  color: #b09821;
  font-size: 2em;
  font-weight: 700;
}

.welcome-banner p {
  margin: 0;
  color: #7a6a2f;
  font-size: 1.18em;
  font-weight: 500;
}

.centered-input {
  position: static !important;
  margin: 100px auto 50 auto !important;
  left: 50px;
  right: 50px;
  bottom: auto;
  top: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  background: transparent;
  box-shadow: none;
  padding: 0;
  transform:none;
  width: 100%;
}

.chat-textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #7a6a2f;
  font-size: 1.13em;
  outline: none;
  padding: 0 8px;
  font-family: inherit;
  resize: none;
  min-height: 44px;
  max-height: 180px;
  line-height: 2.5;
  overflow-y: auto;
}

.chat-textarea::-webkit-scrollbar {
  width: 20px;
  background: transparent;
}

.chat-textarea::-webkit-scrollbar-thumb {
  background: #e6c20033; /* dourado translúcido */
  border-radius: -100px;
}

.chat-textarea {
  scrollbar-width: thick;
  scrollbar-color: #e6c20033 transparent;
}

.centered-input .chat-textarea {
  min-height: 44px;
  max-height: 180px;
  resize: none;
  overflow-y: auto;
}

.chat-textarea:empty,
.chat-textarea:placeholder-shown {
  overflow-y: hidden !important;
}

.control-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  margin-left: 8px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.control-btn:hover {
  opacity: 1;
}

.edit-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  opacity: 0;
  transition: opacity 0.2s;
  color: #7a6a2f;
  font-size: 1.2em;
  align-self: flex-start;
  margin-top: 0;
  flex-shrink: 0;
}

.chat-message.user:hover .edit-btn {
  opacity: 0.7;
}

.edit-btn:hover {
  opacity: 1;
}

.edit-textarea {
  width: 100%;
  min-height: 44px;
  padding: 8px;
  border: 1px solid #e6c200;
  border-radius: 8px;
  background: #fffbe6;
  color: #7a6a2f;
  font-family: inherit;
  font-size: inherit;
  resize: vertical;
}

.chat-author {
  color: #b09821;
  font-size: 0.98em;
  font-weight: 700;
  margin-bottom: 2px;
  margin-left: 8px;
  margin-top: 0;
  text-align: left;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.avatar {
  width: 40px;
  height: 40px;
  background: #f4f0de;
  border: 2px solid #e6c200;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5em;
  margin-right: 10px;
  box-shadow: 0 2px 8px rgba(191, 160, 70, 0.10);
}
.avatar.user {
  background: #f7d774;
  border-color: #b09821;
  margin-right: -10px;
  margin-left: 10px;
}

.copy-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 2px;
  margin-left: 54px;
  min-height: 28px;
}
.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 6px;
  transition: background 0.2s;
  opacity: 0.7;
  display: flex;
  align-items: center;
}
.copy-btn:hover {
  background: #fbe7b3;
  opacity: 1;
}
.copy-feedback {
  color: #b09821;
  font-size: 1em;
  margin-left: 6px;
  font-weight: 600;
  transition: opacity 0.2s;
}

.copy-global-feedback {
  position: fixed;
  left: 32px;
  bottom: 32px;
  background: #141414ee;
  color: #efefea;
  border: none;
  border-radius: 10px;
  padding: 12px 22px;
  font-size: 1.08em;
  font-weight: 600;
  box-shadow: 0 2px 12px rgba(191, 160, 70, 0.10);
  z-index: 9999;
  opacity: 1;
  /*animation: fadeCopy 1.2s;*/
}

@keyframes fadeCopy {
  0% { opacity: 0; transform: translateY(20px); }
  10% { opacity: 1; transform: translateY(0); }
  90% { opacity: 1; }
  100% { opacity: 0; transform: translateY(20px); }
}

/* Centraliza e aproxima o ícone de edição */
.edit-btn {
  align-self: center !important;
  margin-top: 0 !important;
  margin-left: 8px !important;
  margin-right: 0 !important;
}
</style>