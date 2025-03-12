// src/services/apiService.js
import axios from 'axios';

// Vite uses import.meta.env instead of process.env
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
console.log('API_URL:', API_URL); // For debugging

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
});

// API service methods
export default {
  // User registration
  async registerUser(userData) {
    try {
      const response = await apiClient.post('/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error.response?.data || error.message || 'Registration failed';
    }
  },

  // Add more API methods as needed
  // Example:
  // async login(credentials) { ... },
  // async fetchVillage(id) { ... },
};