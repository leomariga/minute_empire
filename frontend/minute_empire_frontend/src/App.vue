<template>
  <v-app>
    <v-main>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
body {
  background-color: #f5f5f5;
  margin: 0;
  padding: 0;
  font-family: 'Roboto', sans-serif;
}
</style>
