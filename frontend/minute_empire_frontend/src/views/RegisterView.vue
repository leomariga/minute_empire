<template>
  <div>
    <registration-form @registered="onRegistered"></registration-form>
  </div>
</template>

<script>
import RegistrationForm from '@/components/RegistrationForm.vue';

export default {
  name: 'RegisterView',
  components: {
    RegistrationForm
  },
  methods: {
    onRegistered(userData) {
      console.log('User registered:', userData);
      // Navigate to village view after successful registration
      this.$router.push('/village');
    }
  }
};
</script> 