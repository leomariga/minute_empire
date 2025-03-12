<template>
  <div>
    <login-form @logged-in="onLoggedIn"></login-form>
  </div>
</template>

<script>
import LoginForm from '@/components/LoginForm.vue';

export default {
  name: 'LoginView',
  components: {
    LoginForm
  },
  methods: {
    onLoggedIn(userData) {
      console.log('User logged in:', userData);
      // Additional handling if needed
    }
  }
};
</script>
