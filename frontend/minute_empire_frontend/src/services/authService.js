import apiService from './apiService';
import router from '@/router';

/**
 * Authentication service for handling user authentication
 */
const authService = {
  /**
   * Check if user is authenticated
   * @returns {boolean} True if user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('user');
  },

  /**
   * Get the current user data
   * @returns {Object|null} The current user data or null if not authenticated
   */
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Login a user
   * @param {string} username - User's username
   * @param {string} password - User's password
   * @returns {Promise<Object>} User data on successful login
   */
  async login(username, password) {
    try {
      const response = await apiService.loginUser({ username, password });
      
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify({
        id: response.user_id,
        username: response.username,
        familyName: response.family_name,
      }));
      
      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  /**
   * Logout the current user
   */
  async logout() {
    try {
      await apiService.logout();
      localStorage.removeItem('user');
      router.push('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Clear local storage even if API call fails
      localStorage.removeItem('user');
      router.push('/login');
    }
  },

  /**
   * Get user's villages
   * @returns {Promise<Array>} List of villages owned by the user
   */
  async getVillages() {
    try {
      return await apiService.getUserVillages();
    } catch (error) {
      console.error('Error fetching villages:', error);
      throw error;
    }
  },

  /**
   * Check if we are authenticated and if not, redirect to login
   */
  requireAuth(to, from, next) {
    if (!this.isAuthenticated()) {
      next({ name: 'Login', query: { redirect: to.fullPath } });
    } else {
      next();
    }
  }
};

export default authService; 