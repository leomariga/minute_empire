// src/services/apiService.js
import axios from 'axios';

// Vite uses import.meta.env instead of process.env
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
console.log('API_URL:', API_URL); // For debugging

/**
 * API service for making HTTP requests to the backend
 */
const apiService = {
  /**
   * Configure axios instance with credentials
   */
  _api: axios.create({
    baseURL: API_URL,
    withCredentials: true, // Important for cookie-based auth
    headers: {
      'Content-Type': 'application/json'
    }
  }),

  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @returns {Promise<Object>} Response from the server
   */
  async registerUser(userData) {
    try {
      const response = await this._api.post('/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Login a user
   * @param {Object} credentials - User login credentials
   * @returns {Promise<Object>} Response from the server
   */
  async loginUser(credentials) {
    try {
      const response = await this._api.post('/login', credentials);
      return response.data;
    } catch (error) {
      console.error('Login error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Logout the current user
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      await this._api.post('/logout');
    } catch (error) {
      console.error('Logout error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Get current user information
   * @returns {Promise<Object>} Current user data
   */
  async getCurrentUser() {
    try {
      const response = await this._api.get('/me');
      
      // If the response includes a token, store it for WebSocket connections
      if (response.data && response.data.access_token) {
        localStorage.setItem('auth_token', response.data.access_token);
      }
      
      return response.data;
    } catch (error) {
      console.error('Get user error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Get villages for the current user
   * @returns {Promise<Array>} Array of village data
   */
  async getUserVillages() {
    try {
      const response = await this._api.get('/villages/me');
      return response.data;
    } catch (error) {
      console.error('Get villages error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Execute a command on a village
   * @param {string} villageId - ID of the village
   * @param {string} command - Command to execute
   * @returns {Promise<Object>} Command execution result
   */
  async executeCommand(villageId, command) {
    try {
      console.log(`[ApiService] Executing command with params:`, { villageId, command });
      if (!villageId) {
        throw new Error('Village ID is required');
      }
      if (!command) {
        throw new Error('Command is required');
      }
      
      const requestBody = {
        command: command,
        village_id: villageId
      };
      console.log('[ApiService] Request body:', JSON.stringify(requestBody, null, 2));
      
      const response = await this._api.post('/villages/command', requestBody);
      console.log('[ApiService] Command response:', response.data);
      return response.data;
    } catch (error) {
      console.error('[ApiService] Command error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Destroy an item (building or resource field)
   * @param {Object} options - Destruction options
   * @param {string} options.villageId - ID of the village
   * @param {string} options.itemType - Type of item ('field' or 'building')
   * @param {number} options.slot - Slot number of the item to destroy
   * @returns {Promise<Object>} Destruction result
   */
  async destroyItem(options) {
    try {
      console.log('[ApiService] Destroying item with options:', options);
      
      if (!options.villageId) {
        throw new Error('Village ID is required for destruction');
      }
      
      if (!options.itemType || !options.slot) {
        throw new Error('Item type and slot are required for destruction');
      }
      
      // Format the destroy command
      const command = `destroy ${options.itemType} in ${options.slot}`;
      console.log('[ApiService] Formatted destroy command:', command);
      
      // Execute the command using the existing method
      return await this.executeCommand(options.villageId, command);
    } catch (error) {
      console.error('[ApiService] Destroy item error:', error.response?.data || error.message);
      throw error;
    }
  },

  /**
   * Get map information including bounds and villages
   * @returns {Promise<Object>} Map data including bounds and villages
   */
  async getMapInfo() {
    try {
      const clientRequestTime = Date.now();
      const response = await this._api.get('/map/info');
      const clientResponseTime = Date.now();
      
      // Validate the response data structure
      const data = response.data;
      if (!data || !data.map_bounds || !Array.isArray(data.villages)) {
        console.error('[ApiService] Invalid map data structure:', data);
        throw new Error('Invalid map data format received from server');
      }
      
      // Enhance the response with client timing information
      return {
        ...data,
        client_request_time: clientRequestTime,
        client_response_time: clientResponseTime,
        request_duration: clientResponseTime - clientRequestTime
      };
    } catch (error) {
      console.error('[ApiService] Map info error:', error.response?.data || error.message);
      throw error;
    }
  }
};

export default apiService;