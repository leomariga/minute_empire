<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6">
        <v-card elevation="8" class="login-card pa-4">
          <v-card-title class="text-h4 font-weight-bold justify-center primary--text">
            Minute Empire
          </v-card-title>
          <v-card-subtitle class="text-h6 text-center secondary--text mb-4">
            Login to your empire
          </v-card-subtitle>

          <v-alert
            v-if="error"
            type="error"
            dismissible
            class="mb-4"
            @click="error = ''"
          >
            {{ error }}
          </v-alert>

          <v-form
            ref="form"
            v-model="valid"
            lazy-validation
            @submit.prevent="login"
          >
            <v-text-field
              v-model="username"
              :rules="usernameRules"
              label="Username"
              required
              outlined
              dense
              prepend-inner-icon="mdi-account"
              class="mb-2"
            ></v-text-field>

            <v-text-field
              v-model="password"
              :rules="passwordRules"
              label="Password"
              type="password"
              required
              outlined
              dense
              prepend-inner-icon="mdi-lock"
              class="mb-4"
            ></v-text-field>

            <div class="d-flex flex-column">
              <v-btn
                :disabled="!valid || loading"
                :loading="loading"
                color="primary"
                x-large
                rounded
                class="mb-4"
                type="submit"
              >
                Login
              </v-btn>
              
              <v-btn
                text
                color="secondary"
                class="align-self-center"
                @click="goToRegister"
              >
                Don't have an account? Register now
              </v-btn>
            </div>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import authService from '@/services/authService';

export default {
  name: 'LoginForm',
  
  data() {
    return {
      valid: false,
      loading: false,
      error: '',
      username: '',
      password: '',
      usernameRules: [
        v => !!v || 'Username is required',
        v => v.length >= 3 || 'Username must be at least 3 characters',
      ],
      passwordRules: [
        v => !!v || 'Password is required',
        v => v.length >= 6 || 'Password must be at least 6 characters',
      ],
    };
  },
  
  methods: {
    async login() {
      if (!this.$refs.form.validate()) return;
      
      this.loading = true;
      this.error = '';
      
      try {
        const response = await authService.login(this.username, this.password);
        this.$emit('logged-in', response);
        // Navigate to village page after successful login
        this.$router.push('/village');
      } catch (error) {
        this.error = error.response?.data?.detail || 'Invalid username or password';
      } finally {
        this.loading = false;
      }
    },
    
    goToRegister() {
      this.$router.push('/register');
    }
  }
};
</script>

<style scoped>
.login-card {
  border-radius: 12px;
  max-width: 500px;
  margin: 0 auto;
}
</style> 