// src/services/websocketService.js
import apiService from './apiService';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000; // 3 seconds
    this.pingInterval = null;
    this.token = null;
    
    // Event handlers
    this.onMessageHandlers = [];
    this.onMapUpdateHandlers = [];
    this.onConnectHandlers = [];
    this.onDisconnectHandlers = [];
  }

  /**
   * Connect to the WebSocket server
   * @param {string} token - Authentication token
   * @returns {Promise<boolean>} - Whether connection was successful
   */
  async connect(token) {
    // If already connected with the same token, don't reconnect
    if (this.socket && this.isConnected && this.token === token) {
      console.log('[WebSocket] Already connected with the same token, reusing connection');
      return true;
    }
    
    // If connected with a different token, disconnect first
    if (this.socket && this.isConnected) {
      console.log('[WebSocket] Already connected with different token, disconnecting first');
      this.disconnect();
    }
    
    this.token = token;
    
    // Vite uses import.meta.env instead of process.env
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${wsProtocol}//${API_URL.replace(/^https?:\/\//, '')}/ws?token=${token}`;
    
    // If API_URL contains full URL with http/https, extract just the hostname and port
    if (API_URL.includes('://')) {
      const url = new URL(API_URL);
      wsUrl = `${wsProtocol}//${url.host}/ws?token=${token}`;
    }
    
    console.log(`[WebSocket] Connecting to ${wsUrl}`);
    
    return new Promise((resolve) => {
      try {
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
          console.log('[WebSocket] Connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startPingInterval();
          
          // Notify connect handlers
          this.onConnectHandlers.forEach(handler => handler());
          
          resolve(true);
        };
        
        this.socket.onmessage = (event) => {
          this.handleMessage(event);
        };
        
        this.socket.onclose = (event) => {
          console.log(`[WebSocket] Disconnected: ${event.code} - ${event.reason}`);
          this.isConnected = false;
          this.stopPingInterval();
          
          // Notify disconnect handlers
          this.onDisconnectHandlers.forEach(handler => handler());
          
          // Try to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`[WebSocket] Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            setTimeout(() => {
              this.reconnectAttempts++;
              this.connect(this.token);
            }, this.reconnectInterval);
          } else {
            console.log('[WebSocket] Max reconnect attempts reached');
          }
          
          resolve(false);
        };
        
        this.socket.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          resolve(false);
        };
      } catch (error) {
        console.error('[WebSocket] Connection error:', error);
        resolve(false);
      }
    });
  }
  
  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.socket) {
      this.stopPingInterval();
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
      console.log('[WebSocket] Disconnected');
    }
  }
  
  /**
   * Handle incoming WebSocket messages
   * @param {MessageEvent} event - WebSocket message event
   */
  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      // Notify general message handlers
      this.onMessageHandlers.forEach(handler => handler(message));
      
      // Handle specific message types
      switch (message.type) {
        case 'map_update':
          console.log('[WebSocket] Received map update');
          this.handleMapUpdate(message.data);
          break;
        case 'ping':
          // Just a ping response, no need to do anything
          break;
        default:
          console.log('[WebSocket] Received unknown message type:', message.type);
          break;
      }
    } catch (error) {
      console.error('[WebSocket] Error parsing message:', error);
    }
  }
  
  /**
   * Handle map update message
   * @param {Object} mapData - Map data from server
   */
  handleMapUpdate(mapData) {
    if (!mapData) {
      console.error('[WebSocket] Received empty map data');
      return;
    }
    
    console.log('[WebSocket] Received map update with data:', {
      mapBounds: mapData.map_bounds,
      villagesCount: mapData.villages ? mapData.villages.length : 0,
      troopsCount: mapData.troops ? mapData.troops.length : 0,
      actionsCount: mapData.troop_actions ? mapData.troop_actions.length : 0
    });
    
    // Parse the server timestamp
    if (mapData.server_time) {
      const serverTime = new Date(mapData.server_time).getTime();
      const clientTime = Date.now();
      const timeDiff = serverTime - clientTime;
      
      // Update server-client time difference in store
      if (window.$store) {
        window.$store.commit('server/updateServerTimeOffset', timeDiff);
      }
    }
    
    // Update store with new data
    if (window.$store) {
      console.log('[WebSocket] Updating store with map data');
      window.$store.commit('map/updateMapData', mapData);
    }
    
    // Check if we have any handlers registered
    if (this.onMapUpdateHandlers.length === 0) {
      console.warn('[WebSocket] No map update handlers registered');
    } else {
      console.log(`[WebSocket] Notifying ${this.onMapUpdateHandlers.length} map update handlers`);
    }
    
    // Notify map update handlers
    this.onMapUpdateHandlers.forEach((handler, index) => {
      try {
        console.log(`[WebSocket] Calling handler ${index}`);
        handler(mapData);
      } catch (error) {
        console.error(`[WebSocket] Error in map update handler ${index}:`, error);
      }
    });
  }
  
  /**
   * Start sending periodic pings to keep connection alive
   */
  startPingInterval() {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 30 seconds
  }
  
  /**
   * Stop the ping interval
   */
  stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
  
  /**
   * Register a handler for all WebSocket messages
   * @param {Function} handler - Message handler function
   */
  onMessage(handler) {
    if (typeof handler === 'function') {
      this.onMessageHandlers.push(handler);
    }
  }
  
  /**
   * Register a handler for map update messages
   * @param {Function} handler - Map update handler function
   */
  onMapUpdate(handler) {
    if (typeof handler === 'function') {
      this.onMapUpdateHandlers.push(handler);
    }
  }
  
  /**
   * Register a handler for WebSocket connection
   * @param {Function} handler - Connect handler function
   */
  onConnect(handler) {
    if (typeof handler === 'function') {
      this.onConnectHandlers.push(handler);
    }
  }
  
  /**
   * Register a handler for WebSocket disconnection
   * @param {Function} handler - Disconnect handler function
   */
  onDisconnect(handler) {
    if (typeof handler === 'function') {
      this.onDisconnectHandlers.push(handler);
    }
  }
  
  /**
   * Remove a message handler
   * @param {Function} handler - Handler to remove
   */
  removeMessageHandler(handler) {
    this.onMessageHandlers = this.onMessageHandlers.filter(h => h !== handler);
  }
  
  /**
   * Remove a map update handler
   * @param {Function} handler - Handler to remove
   */
  removeMapUpdateHandler(handler) {
    this.onMapUpdateHandlers = this.onMapUpdateHandlers.filter(h => h !== handler);
  }
  
  /**
   * Remove a connect handler
   * @param {Function} handler - Handler to remove
   */
  removeConnectHandler(handler) {
    this.onConnectHandlers = this.onConnectHandlers.filter(h => h !== handler);
  }
  
  /**
   * Remove a disconnect handler
   * @param {Function} handler - Handler to remove
   */
  removeDisconnectHandler(handler) {
    this.onDisconnectHandlers = this.onDisconnectHandlers.filter(h => h !== handler);
  }
}

// Create and export a singleton instance
const websocketService = new WebSocketService();
export default websocketService; 