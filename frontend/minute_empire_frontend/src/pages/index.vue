<template>
  <v-container class="bg-theme fill-height pa-0">
    <v-responsive class="fill-height">
      <v-row align="center" justify="center" class="fill-height">
        <v-col cols="12" sm="10" md="8" lg="6">
          <div class="text-center mb-6">
            <h1 class="text-h2 font-weight-bold text-white">Minute Empire</h1>
            <p class="text-subtitle-1 text-white">Build your empire and conquer the world</p>
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
  background: white
}
</style>
