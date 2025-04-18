/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import storePlugin from './store/index.js'
import authService from './services/authService'
import websocketService from './services/websocketService'

// Composables
import { createApp } from 'vue'

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(storePlugin)

registerPlugins(app)

// Make store available globally for easier access in websocket service
window.$store = storePlugin.store;

// Initialize WebSocket service if the user is already logged in
const initWebSocket = async () => {
  if (authService.isAuthenticated()) {
    try {
      const token = authService.getToken();
      if (token) {
        console.log('User is authenticated, connecting to WebSocket');
        const connected = await websocketService.connect(token);
        if (connected) {
          console.log('WebSocket connected successfully');
        } else {
          console.error('WebSocket connection failed');
          // Try again after a delay
          setTimeout(() => {
            console.log('Retrying WebSocket connection...');
            websocketService.connect(token).catch(error => {
              console.error('Error on WebSocket retry:', error);
            });
          }, 2000);
        }
      } else {
        console.warn('User is authenticated but no token available for WebSocket connection');
      }
    } catch (error) {
      console.error('Error initializing WebSocket connection:', error);
    }
  }
};

// Connect to WebSocket
initWebSocket();

app.mount('#app')
