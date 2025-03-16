<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="primary--text">
            <v-icon large left color="primary">mdi-castle</v-icon>
            Your Empire: {{ userData ? userData.familyName : 'Loading...' }}
            <v-spacer></v-spacer>
            <v-btn color="error" @click="logout" text>
              <v-icon left>mdi-logout</v-icon>
              Logout
            </v-btn>
          </v-card-title>
          <v-card-subtitle>
            <span class="font-weight-bold">Username:</span> {{ userData ? userData.username : 'Loading...' }}
          </v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        <div class="mt-4 text-h6">Loading your empire data...</div>
      </v-col>
    </v-row>

    <template v-else>
      <v-row v-if="error">
        <v-col cols="12">
          <v-alert type="error" dismissible>
            {{ error }}
          </v-alert>
        </v-col>
      </v-row>

      <v-row v-else-if="villages.length === 0">
        <v-col cols="12">
          <v-alert type="info">
            You don't have any villages yet. Something might be wrong with your account.
          </v-alert>
        </v-col>
      </v-row>

      <template v-else>
        <v-row>
          <v-col cols="12">
            <v-card>
              <v-card-title class="secondary--text">
                <v-icon left color="secondary">mdi-map-marker</v-icon>
                Your Villages
              </v-card-title>
              
              <v-tabs v-model="activeVillage" background-color="primary" dark slider-color="accent">
                <v-tab v-for="(village, index) in villages" :key="village._id">
                  {{ village.name || `Village ${index + 1}` }}
                </v-tab>
              </v-tabs>

              <v-tabs-items v-model="activeVillage">
                <v-tab-item v-for="village in villages" :key="village._id">
                  <v-card flat>
                    <v-card-text>
                      <!-- Command Interface -->
                      <v-row class="mb-4">
                        <v-col cols="12">
                          <v-card outlined>
                            <v-card-title>Command Center</v-card-title>
                            <v-card-text>
                              <v-form @submit.prevent="executeCommand()">
                                <v-text-field
                                  v-model="commandInput"
                                  label="Enter command"
                                  placeholder="e.g., upgrade field in 1"
                                  :error-messages="commandError"
                                  @input="commandError = ''"
                                  append-outer-icon="mdi-send"
                                  @click:append-outer="executeCommand()"
                                ></v-text-field>
                              </v-form>
                              <v-alert
                                v-if="commandResult"
                                :type="commandResult.success ? 'success' : 'error'"
                                class="mt-2"
                                dismissible
                              >
                                {{ commandResult.message }}
                              </v-alert>
                              <v-card-subtitle>
                                Available commands:
                                <ul class="mt-2">
                                  <li>upgrade field in [slot]</li>
                                  <li>upgrade building in [slot]</li>
                                  <li>create [wood|stone|iron|food] field in [slot]</li>
                                  <li>create [city_center|rally_point|barraks|archery|stable|warehouse|granary|hide_spot|wall] building in [slot]</li>
                                </ul>
                              </v-card-subtitle>
                            </v-card-text>
                          </v-card>
                        </v-col>
                      </v-row>
                      
                      <v-row>
                        <v-col cols="12" md="6">
                          <v-card outlined>
                            <v-card-title>Village Information</v-card-title>
                            <v-list>
                              <v-list-item>
                                <v-list-item-content>
                                  <v-list-item-title>Name</v-list-item-title>
                                  <v-list-item-subtitle>{{ village.name || 'Unnamed Village' }}</v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>

                              <v-list-item>
                                <v-list-item-content>
                                  <v-list-item-title>Location</v-list-item-title>
                                  <v-list-item-subtitle>X: {{ village.location.x }}, Y: {{ village.location.y }}</v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>

                              <v-list-item>
                                <v-list-item-content>
                                  <v-list-item-title>Created At</v-list-item-title>
                                  <v-list-item-subtitle>{{ new Date(village.created_at).toLocaleString() }}</v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                            </v-list>
                          </v-card>
                        </v-col>

                        <v-col cols="12" md="6">
                          <v-card outlined>
                            <v-card-title>Resources</v-card-title>
                            <v-list dense>
                              <v-list-item v-for="(value, key) in village.resources" :key="key">
                                <v-list-item-content>
                                  <v-list-item-title class="text-capitalize">{{ key.replace('_', ' ') }}</v-list-item-title>
                                  <v-list-item-subtitle>{{ value }}</v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                            </v-list>
                          </v-card>
                        </v-col>
                      </v-row>

                      <v-row class="mt-4">
                        <v-col cols="12">
                          <v-expansion-panels>
                            <v-expansion-panel>
                              <v-expansion-panel-header>
                                Raw Village Data (JSON)
                              </v-expansion-panel-header>
                              <v-expansion-panel-content>
                                <pre class="json-code">{{ JSON.stringify(village, null, 2) }}</pre>
                              </v-expansion-panel-content>
                            </v-expansion-panel>
                          </v-expansion-panels>
                        </v-col>
                      </v-row>
                    </v-card-text>
                  </v-card>
                </v-tab-item>
              </v-tabs-items>
            </v-card>
          </v-col>
        </v-row>
      </template>
    </template>
  </v-container>
</template>

<script>
import authService from '@/services/authService';
import apiService from '@/services/apiService';

export default {
  name: 'VillageView',
  
  data() {
    return {
      loading: true,
      error: null,
      userData: null,
      villages: [],
      activeVillage: 0,
      commandInput: '',
      commandError: '',
      commandResult: null,
    };
  },
  
  async created() {
    if (!authService.isAuthenticated()) {
      this.$router.push('/login');
      return;
    }
    
    this.userData = authService.getCurrentUser();
    await this.fetchVillages();
  },
  
  methods: {
    async fetchVillages() {
      try {
        this.loading = true;
        this.error = null;
        this.villages = await apiService.getUserVillages();
      } catch (error) {
        this.error = 'Failed to load village data. Please try again later.';
        console.error('Error fetching villages:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async logout() {
      try {
        await authService.logout();
      } catch (error) {
        console.error('Logout error:', error);
      }
    },
    
    async executeCommand() {
      if (!this.commandInput.trim()) {
        this.commandError = 'Please enter a command';
        return;
      }

      const currentVillage = this.villages[this.activeVillage];
      const villageId = currentVillage?.id || currentVillage?._id;

      if (!villageId) {
        this.commandError = 'No village selected or village ID not found';
        return;
      }
      
      try {
        console.log(`[Command] Executing "${this.commandInput}" for village ${villageId}`);
        const response = await apiService.executeCommand(villageId, this.commandInput);
        
        this.commandResult = response;
        if (response.success) {
          this.commandInput = '';
          await this.fetchVillages();
        }
      } catch (error) {
        console.error('[Command] Error:', error);
        this.commandResult = {
          success: false,
          message: error.response?.data?.detail || 'Failed to execute command'
        };
      }
    },
  }
};
</script>

<style scoped>
.json-code {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style> 