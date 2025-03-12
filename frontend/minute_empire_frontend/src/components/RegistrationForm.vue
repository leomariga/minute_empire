<template>
  <v-card
    class="mx-auto pa-4"
    max-width="500"
    elevation="8"
    rounded="lg"
  >
    <v-card-title class="text-h4 text-md-h3 text-center mb-3">
      Join Minute Empire
    </v-card-title>
    
    <v-card-subtitle class="text-center mb-4">
      Register to build your empire and conquer the world
    </v-card-subtitle>

    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="error = ''"
    >
      {{ error }}
    </v-alert>

    <v-form
      ref="form"
      v-model="valid"
      @submit.prevent="register"
    >
      <v-text-field
        v-model="username"
        label="Username"
        :rules="usernameRules"
        prepend-inner-icon="mdi-account"
        variant="outlined"
        required
        autocomplete="username"
        class="mb-3"
      ></v-text-field>

      <v-text-field
        v-model="password"
        label="Password"
        :rules="passwordRules"
        prepend-inner-icon="mdi-lock"
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        :type="showPassword ? 'text' : 'password'"
        variant="outlined"
        required
        autocomplete="new-password"
        class="mb-3"
        @click:append-inner="showPassword = !showPassword"
      ></v-text-field>

      <v-text-field
        v-model="familyName"
        label="Family Name"
        :rules="familyNameRules"
        prepend-inner-icon="mdi-family-tree"
        variant="outlined"
        required
        class="mb-3"
      ></v-text-field>

      <v-text-field
        v-model="villageName"
        label="Village Name"
        :rules="villageNameRules"
        prepend-inner-icon="mdi-home-city"
        variant="outlined"
        required
        class="mb-3"
      ></v-text-field>

      <v-label>Choose Your Banner Color</v-label>
      <v-color-picker
        v-model="color"
        mode="hex"
        hide-inputs
        hide-canvas
        show-swatches
        :swatches="colorSwatches"
        class="mb-3 mx-auto color-picker-centered"
      ></v-color-picker>

      <v-btn
        type="submit"
        color="primary"
        size="large"
        block
        :loading="loading"
        :disabled="!valid || loading"
        class="mt-4 text-body-1"
      >
        Create Empire
      </v-btn>
    </v-form>
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import apiService from '@/services/apiService'

const form = ref(null)
const valid = ref(false)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

// Form fields
const username = ref('')
const password = ref('')
const familyName = ref('')
const villageName = ref('')
const color = ref('#1976D2') // Default color

// Validation rules
const usernameRules = [
  v => !!v || 'Username is required',
  v => (v && v.length >= 3) || 'Username must be at least 3 characters',
  v => (v && v.length <= 20) || 'Username must be less than 20 characters',
  v => /^[a-zA-Z0-9_-]+$/.test(v) || 'Username can only contain letters, numbers, underscores and hyphens'
]

const passwordRules = [
  v => !!v || 'Password is required',
  v => (v && v.length >= 6) || 'Password must be at least 6 characters'
]

const familyNameRules = [
  v => !!v || 'Family name is required',
  v => (v && v.length >= 2) || 'Family name must be at least 2 characters',
  v => (v && v.length <= 30) || 'Family name must be less than 30 characters'
]

const villageNameRules = [
  v => !!v || 'Village name is required',
  v => (v && v.length >= 2) || 'Village name must be at least 2 characters',
  v => (v && v.length <= 30) || 'Village name must be less than 30 characters'
]

// Predefined color swatches for banners
const colorSwatches = [
  ['#F44336', '#E91E63', '#9C27B0', '#673AB7', '#3F51B5', '#2196F3', '#03A9F4'],
  ['#00BCD4', '#009688', '#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107'],
  ['#FF9800', '#FF5722', '#795548', '#607D8B', '#000000', '#FFFFFF', '#9E9E9E']
]

// Register function
const register = async () => {
  if (!form.value.validate()) return

  loading.value = true
  error.value = ''
  
  try {
    const data = await apiService.registerUser({
      username: username.value,
      password: password.value,
      family_name: familyName.value,
      color: color.value,
      village_name: villageName.value
    });
    
    // Emit registered event with user data
    emit('registered', {
      userId: data.user_id,
      villageId: data.village_id,
      username: username.value,
      villageName: villageName.value
    })
    
    // Reset form
    form.value.reset()
  } catch (err) {
    error.value = typeof err === 'string' ? err : (err.detail || 'An error occurred during registration')
    console.error('Registration error:', err)
  } finally {
    loading.value = false
  }
}

// Define emits
const emit = defineEmits(['registered'])
</script>

<style scoped>
.color-picker-centered {
  display: flex;
  justify-content: center;
  max-width: 350px;
}

/* Mobile optimization */
@media (max-width: 600px) {
  :deep(.v-color-picker) {
    width: 100%;
  }
}
</style> 