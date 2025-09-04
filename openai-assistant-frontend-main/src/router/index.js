import { createRouter, createWebHistory } from 'vue-router';
import Helloword from '../components/Helloword.vue'; // Verifique o caminho para seu componente

// (Opcional) Crie um componente para a página inicial
const Home = {
  template: `
    <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
      <h1>Escolha um Assistente</h1>
      <ul>
        <li><router-link to="/chat/suporte">Assistente de Suporte</router-link></li>
        <li><router-link to="/chat/suporte pedro">Assistente de Vendas (Pedro)</router-link></li>
        <li><router-link to="/chat/financas">Assistente Financeiro</router-link></li>
      </ul>
    </div>
  `,
};

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home, // Página inicial para escolher o chat
  },
  {
    // Esta é a rota dinâmica. O ":rota" é um parâmetro.
    path: '/chat/:rota',
    name: 'Chat',
    component: Helloword,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;