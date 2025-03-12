/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#2E7D32',   // Forest green
          secondary: '#1B5E20', // Dark green
          accent: '#00BFA5',    // Teal accent
          error: '#B00020',
          info: '#0288D1',
          success: '#4CAF50',
          warning: '#FB8C00',
          background: '#F0F0F0'
        }
      }
    }
  },
})
