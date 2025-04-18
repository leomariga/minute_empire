// src/store/index.js
import { reactive } from 'vue'

// Create a reactive state object
const state = reactive({
  // Server module state
  serverTimeOffset: 0,
  
  // Map module state
  mapData: null,
  villages: [],
  troops: [],
  troopActions: []
});

// Create a simple store object
const store = {
  // State accessor
  state,
  
  // Mutations (methods that change state)
  commit(type, payload) {
    switch (type) {
      case 'server/updateServerTimeOffset':
        state.serverTimeOffset = payload;
        break;
        
      case 'map/updateMapData':
        state.mapData = payload;
        state.villages = payload.villages || [];
        state.troops = payload.troops || [];
        state.troopActions = payload.troop_actions || [];
        break;
        
      default:
        console.warn(`Unknown mutation type: ${type}`);
    }
  },
  
  // Getters
  getters: {
    'server/getCurrentServerTime': () => {
      return Date.now() + state.serverTimeOffset;
    }
  }
};

// Install method for Vue.use()
function install(app) {
  app.config.globalProperties.$store = store;
}

export default {
  install,
  store
}; 