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
  }
};

export default apiService;