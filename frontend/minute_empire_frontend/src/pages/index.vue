<template>
  <v-container class="bg-theme fill-height pa-0 pa-sm-4">
    <v-responsive class="fill-height">
      <v-row align="center" justify="center" class="fill-height ma-0">
        <v-col cols="12" sm="10" md="8" lg="6" class="pa-0 pa-sm-2">
          <div class="text-center mb-4">
            <h1 class="text-h3 text-sm-h2 font-weight-bold app-title">Minute Empire</h1>
            <p class="text-body-2 text-sm-subtitle-1 app-subtitle">Build your empire and conquer the world</p>
          </div>
          <registration-form @registered="onRegistered" />
        </v-col>
      </v-row>
    </v-responsive>

    <!-- Success dialog -->
    <v-dialog v-model="showSuccessDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5">Registration Successful!</v-card-title>
        <v-card-text>
          <p>Welcome to Minute Empire, {{ registrationData.username }}!</p>
          <p>Your village <strong>{{ registrationData.villageName }}</strong> has been created.</p>
          <p class="text-caption">User ID: {{ registrationData.userId }}</p>
          <p class="text-caption">Village ID: {{ registrationData.villageId }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="showSuccessDialog = false">Start Playing</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import RegistrationForm from '@/components/RegistrationForm.vue'

const showSuccessDialog = ref(false)
const registrationData = reactive({
  userId: '',
  villageId: '',
  username: '',
  villageName: ''
})

function onRegistered(data) {
  registrationData.userId = data.userId
  registrationData.villageId = data.villageId
  registrationData.username = data.username
  registrationData.villageName = data.villageName
  showSuccessDialog.value = true
}
</script>

<style scoped>
.bg-theme {
  background-color: #f0f0f0;
  overflow-x: hidden;
}

.app-title {
  color: #1B5E20;
  margin-bottom: 8px;
}

.app-subtitle {
  color: #2E7D32;
}

.v-card {
  background-color: #ffffff !important;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
  transition: all 0.3s ease;
}

.v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12) !important;
}

/* Make stepper transparent on mobile */
@media (max-width: 600px) {
  .v-stepper {
    background-color: transparent !important;
  }
  
  .v-stepper-header {
    box-shadow: none !important;
  }
  
  .app-title {
    font-size: 1.75rem !important;
  }
}
</style>
