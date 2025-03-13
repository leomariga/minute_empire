<template>
  <div>
    <!-- Progress indicator -->
    <v-stepper v-model="currentStep" class="mb-4 bg-transparent elevation-0">
      <v-stepper-header class="bg-transparent elevation-0">
        <v-stepper-item step="1" :complete="currentStep > 1"></v-stepper-item>
        <v-divider></v-divider>
        <v-stepper-item step="2" :complete="currentStep > 2"></v-stepper-item>
        <v-divider></v-divider>
        <v-stepper-item step="3"></v-stepper-item>
      </v-stepper-header>
    </v-stepper>

    <!-- Alert for errors -->
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

    <!-- Step 1: Account creation -->
    <v-card
      v-if="currentStep === 1"
      class="mx-auto pa-4"
      max-width="500"
      elevation="8"
      rounded="lg"
    >
      <div class="text-center mb-2">
        <img src="@/assets/scroll.svg" alt="Scroll" width="120" class="mb-3" />
        <v-card-title class="text-body-1 text-sm-h5 mb-2">Begin Your Legend</v-card-title>
        <v-card-subtitle class="text-caption text-sm-subtitle-1 text-wrap px-4">
          Sign the royal decree and begin your journey to greatness
        </v-card-subtitle>
      </div>

      <v-form
        ref="accountForm"
        v-model="accountValid"
      >
        <v-text-field
          v-model="username"
          label="Choose your username"
          :rules="usernameRules"
          prepend-inner-icon="mdi-account"
          variant="outlined"
          required
          autocomplete="username"
          class="mb-3"
        ></v-text-field>

        <v-text-field
          v-model="password"
          label="Create a password"
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

        <v-btn
          color="primary"
          size="large"
          block
          :disabled="!accountValid"
          class="mt-4"
          @click="nextStep"
        >
          Continue
        </v-btn>
      </v-form>
    </v-card>

    <!-- Step 2: Family and color -->
    <v-card
      v-if="currentStep === 2"
      class="mx-auto pa-4"
      max-width="500"
      elevation="8"
      rounded="lg"
    >
      <div class="text-center mb-2">
        <img src="@/assets/coat-of-arms.svg" alt="Coat of Arms" width="120" class="mb-3" />
        <v-card-title class="text-body-1 text-sm-h5 mb-2">Your Noble House</v-card-title>
        <v-card-subtitle class="text-caption text-sm-subtitle-1 text-wrap px-4">
          The name of your family will cause terror for your enemies and respect from your allies
        </v-card-subtitle>
      </div>

      <v-form
        ref="familyForm"
        v-model="familyValid"
      >
        <v-text-field
          v-model="familyName"
          label="Family Name"
          :rules="familyNameRules"
          prepend-inner-icon="mdi-family-tree"
          variant="outlined"
          required
          class="mb-3"
        ></v-text-field>

        <div>
          <v-label class="mb-2 d-block">Choose Your Banner Color</v-label>
          <v-color-picker
            v-model="color"
            mode="hex"
            hide-inputs
            hide-canvas
            show-swatches
            :swatches="colorSwatches"
            class="mb-3 mx-auto color-picker-centered"
          ></v-color-picker>
        </div>

        <div class="button-container">
          <v-btn
            variant="outlined"
            size="large"
            :disabled="!familyValid"
            class="mt-2 mb-1 button-width"
            @click="prevStep"
          >
            Back
          </v-btn>
          <v-btn
            color="primary"
            size="large"
            :disabled="!familyValid"
            class="mt-1 mb-2 button-width"
            @click="nextStep"
          >
            Continue
          </v-btn>
        </div>
      </v-form>
    </v-card>

    <!-- Step 3: Village name -->
    <v-card
      v-if="currentStep === 3"
      class="mx-auto pa-4"
      max-width="500"
      elevation="8"
      rounded="lg"
    >
      <div class="text-center mb-2">
        <img src="@/assets/village.svg" alt="Village" width="120" class="mb-3" />
        <v-card-title class="text-body-1 text-sm-h5 mb-2">Your First Settlement</v-card-title>
        <v-card-subtitle class="text-caption text-sm-subtitle-1 text-wrap px-4">
          From humble beginnings rise great empires. Name your first village!
        </v-card-subtitle>
      </div>

      <v-form
        ref="villageForm"
        v-model="villageValid"
        @submit.prevent="register"
      >
        <v-text-field
          v-model="villageName"
          label="Village Name"
          :rules="villageNameRules"
          prepend-inner-icon="mdi-home-city"
          variant="outlined"
          required
          class="mb-3"
        ></v-text-field>

        <div class="button-container">
          <v-btn
            variant="outlined"
            size="large"
            class="mt-2 mb-1 button-width"
            @click="prevStep"
          >
            Back
          </v-btn>
          <v-btn
            type="submit"
            color="primary"
            size="large"
            :loading="loading"
            :disabled="!villageValid || loading"
            class="mt-1 mb-2 button-width"
          >
            Found Empire
          </v-btn>
        </div>
      </v-form>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import apiService from '@/services/apiService'

// Form state
const accountForm = ref(null)
const familyForm = ref(null)
const villageForm = ref(null)
const accountValid = ref(false)
const familyValid = ref(false)
const villageValid = ref(false)
const currentStep = ref(1)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

// Form fields
const username = ref('')
const password = ref('')
const familyName = ref('')
const villageName = ref('')
const color = ref('#2E7D32') // Default color - forest green

// Validation rules
const usernameRules = [
  v => !!v || 'Username is required',
  v => (v && v.length >= 3) || 'Username must be at least 3 characters',
  v => (v && v.length <= 50) || 'Username must be less than 50 characters',
  v => /^[a-zA-Z0-9_-]+$/.test(v) || 'Username can only contain letters, numbers, underscores and hyphens'
]

const passwordRules = [
  v => !!v || 'Password is required',
  v => (v && v.length >= 8) || 'Password must be at least 8 characters'
]

const familyNameRules = [
  v => !!v || 'Family name is required',
  v => (v && v.length >= 2) || 'Family name must be at least 2 characters',
  v => (v && v.length <= 50) || 'Family name must be less than 50 characters'
]

const villageNameRules = [
  v => !!v || 'Village name is required',
  v => (v && v.length >= 3) || 'Village name must be at least 3 characters',
  v => (v && v.length <= 50) || 'Village name must be less than 50 characters'
]

// Predefined color swatches for banners
const colorSwatches = [
  ['#2E7D32', '#1B5E20', '#388E3C', '#43A047', '#4CAF50', '#66BB6A', '#81C784'],
  ['#00BFA5', '#00897B', '#009688', '#26A69A', '#4DB6AC', '#80CBC4', '#006064'],
  ['#795548', '#3E2723', '#5D4037', '#A1887F', '#BCAAA4', '#D7CCC8', '#EFEBE9']
]

// Navigation functions
function nextStep() {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// Register function
const register = async () => {
  if (!accountValid.value || !familyValid.value || !villageValid.value) {
    return
  }

  loading.value = true
  error.value = ''
  
  try {
    const response = await apiService.registerUser({
      username: username.value,
      password: password.value,
      family_name: familyName.value,
      color: color.value,
      village_name: villageName.value
    });
    
    // Emit registration event
    emit('registered', response);
    
    // Store user data in localStorage
    localStorage.setItem('user', JSON.stringify({
      id: response.user_id,
      username: response.username,
      familyName: response.family_name,
    }));
    
    // Navigate to village view
    router.push('/village');
  } catch (err) {
    error.value = typeof err === 'string' ? err : (err.detail || 'Registration failed. Please try again.');
    console.error('Registration error:', err);
  } finally {
    loading.value = false;
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

.button-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.button-width {
  width: 100%;
}

/* Mobile optimization */
@media (min-width: 600px) {
  .button-container {
    flex-direction: row;
    gap: 8px;
  }
  
  .button-width {
    width: 50%;
  }
}

@media (max-width: 600px) {
  :deep(.v-color-picker) {
    width: 100%;
  }
  
  :deep(.v-card-subtitle) {
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
    display: block;
    font-size: 12px;
    line-height: 1.2;
  }
}
</style> 