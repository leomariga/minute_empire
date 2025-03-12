<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card elevation="8" class="home-card pa-3 pa-sm-6">
          <v-card-title class="text-h5 text-sm-h4 text-md-h3 font-weight-bold text-center primary--text mb-2 mb-sm-4">
            Minute Empire
          </v-card-title>
          
          <v-card-subtitle class="text-caption text-sm-subtitle-1 text-center mb-2 mb-sm-6">
            Build your empire, conquer your enemies, rule the world!
          </v-card-subtitle>
          
          <v-img
            :src="logoUrl"
            alt="Minute Empire"
            class="mb-4 mb-sm-8 rounded-lg"
            height="160"
            max-height="200"
            cover
          >
            <template v-slot:placeholder>
              <v-row
                class="fill-height ma-0"
                align="center"
                justify="center"
              >
                <v-progress-circular
                  indeterminate
                  color="primary"
                ></v-progress-circular>
              </v-row>
            </template>
          </v-img>
          
          <!-- Login and Register Buttons -->
          <div class="button-container">
            <v-btn
              height="50"
              rounded
              color="primary"
              dark
              class="my-2 login-btn"
              @click="$router.push('/login')"
            >
              <v-icon left>mdi-login</v-icon>
              <span class="font-weight-bold">Login</span>
            </v-btn>
            
            <v-btn
              height="50"
              rounded
              color="secondary"
              dark
              class="my-2 register-btn"
              @click="$router.push('/register')"
            >
              <v-icon left>mdi-account-plus</v-icon>
              <span class="font-weight-bold">Register</span>
            </v-btn>
          </div>
          
          <v-card-text class="text-caption text-sm-subtitle-2 text-center mt-1 mt-sm-4">
            Join thousands of players in the ultimate strategy game!
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import logo from '@/assets/logo.png';

export default {
  name: 'HomeView',
  
  data() {
    return {
      logoUrl: logo
    };
  },
  
  created() {
    // If user is already logged in, redirect to village
    if (localStorage.getItem('user')) {
      this.$router.push('/village');
    }
  }
};
</script>

<style scoped>
.home-card {
  border-radius: 12px;
  max-width: 600px;
  margin: 0 auto;
  overflow: hidden; /* Prevent content overflow */
}

.button-container {
  display: flex;
  flex-direction: column;
  padding: 0 16px;
}

.login-btn, .register-btn {
  width: 100%;
  font-size: 1rem;
  text-transform: none;
  letter-spacing: 0.5px;
}

/* Mobile optimization */
@media (min-width: 600px) {
  .button-container {
    flex-direction: row;
    justify-content: space-around;
    padding: 0 24px;
  }
  
  .login-btn, .register-btn {
    width: 45%;
  }
}

@media (max-width: 600px) {
  .home-card {
    border-radius: 8px;
  }
}
</style> 