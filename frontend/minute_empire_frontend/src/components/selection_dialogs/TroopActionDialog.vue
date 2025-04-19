<template>
  <BaseSelectionDialog
    :show="show"
    @update:show="$emit('update:show', $event)"
    @close="closeDialog"
    :slot-id="targetLocation ? `${targetLocation.x},${targetLocation.y}` : ''"
    :title="getTitle"
    :description="getDescription"
    :type-color="getTypeColor"
    :type-icon="getTypeIcon"
    :image-url="getImageUrl"
    :is-troop-dialog="true"
  >
    <!-- Header actions slot -->
    <template v-slot:header-actions>
      <div class="troop-quantity">
        <v-icon size="16" color="primary" class="mr-1">mdi-account-group</v-icon>
        {{ troop?.quantity || 0 }}
      </div>
    </template>
    
    <!-- Custom status badge -->
    <template v-slot:image-badges>
      <div class="badge status-badge" :style="getStatusBadgeStyle()">
        <v-icon size="14" color="white" class="mr-1">{{ getTroopStatusIcon() }}</v-icon>
        <span>{{ getTroopStatus() }}</span>
      </div>
    </template>
    
    <!-- Main content -->
    <template v-slot:content>
      <!-- Troop Information Panel -->
      <div class="game-panel mb-3">
        <div class="panel-header">
          <v-icon size="18" color="grey-darken-1" class="mr-2">mdi-account-group</v-icon>
          <span>Troop Information</span>
        </div>
        
        <div class="panel-content">
          <div class="info-grid">
            <div class="info-item">
              <div class="info-label"><v-icon size="12" class="mr-1" color="grey-darken-1">mdi-home</v-icon>Origin Base</div>
              <div class="info-value">{{ getHomeVillageName() }}</div>
            </div>
            
            <div class="info-item full-width">
              <div class="info-label"><v-icon size="12" class="mr-1" color="grey-darken-1">mdi-map-marker</v-icon>Coordinates</div>
              <div class="location-display">
                <div class="location-value">[{{ formatLocation(troop?.location) }}]</div>
                <v-icon color="grey" class="mx-2">mdi-arrow-right</v-icon>
                <div class="location-value target">[{{ formatLocation(targetLocation) }}]</div>
              </div>
            </div>
            
            <!-- Show backpack if troop is carrying resources -->
            <div v-if="hasCargo" class="info-item full-width">
              <div class="info-label">Carrying</div>
              <div class="resources-grid">
                <div v-for="resource in ['wood', 'food', 'stone', 'iron']" 
                     :key="resource"
                     v-if="getBackpackAmount(resource) !== undefined" 
                     class="mini-resource">
                  <v-icon size="14" :color="resourceColor(resource)">{{ resourceIcon(resource) }}</v-icon>
                  <span>{{ formatNumber(getBackpackAmount(resource)) }}</span>
                </div>
              </div>
            </div>
            
            <!-- Only show current status if troop has an active action -->
            <div v-if="hasActiveAction" class="info-item full-width">
              <div class="info-label">Status</div>
              <div class="status-indicator">
                <v-icon size="14" color="primary" class="mr-1 rotating-icon">mdi-refresh</v-icon>
                <span>{{ getTroopActionDescription() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Action Options -->
      <div v-if="!hasActiveAction" class="game-panel">
        <div class="panel-header">
          <v-icon size="18" color="grey-darken-1" class="mr-2">mdi-lightning-bolt</v-icon>
          <span>Available Actions</span>
        </div>
        
        <div class="panel-content">
          <!-- Action selection buttons -->
          <div class="action-buttons">
            <v-btn 
              color="primary" 
              :disabled="!canMove"
              @click="executeAction('move')"
              block
              class="mb-2 action-btn"
            >
              <div class="action-btn-content">
                <div class="action-btn-left">
                  <v-icon size="18" class="mr-2">mdi-map-marker-path</v-icon>
                  <span>Move to Location</span>
                </div>
                <div class="action-btn-time">
                  <v-icon size="14" color="white" class="mr-1">mdi-clock-outline</v-icon>
                  <span>{{ formatTime(1) }}</span>
                </div>
              </div>
            </v-btn>
            
            <v-btn 
              color="error" 
              :disabled="!canAttack"
              @click="executeAction('attack')"
              block
              class="action-btn"
            >
              <div class="action-btn-content">
                <div class="action-btn-left">
                  <v-icon size="18" class="mr-2">mdi-sword-cross</v-icon>
                  <span>Attack Target</span>
                </div>
                <div class="action-btn-time">
                  <v-icon size="14" color="white" class="mr-1">mdi-clock-outline</v-icon>
                  <span>{{ formatTime(1) }}</span>
                </div>
              </div>
            </v-btn>
          </div>
        </div>
      </div>
    </template>
  </BaseSelectionDialog>
</template>

<script>
import { getTroopColor, getTroopIcon, getResourceColor, getResourceIcon, UI_COLORS, getTroopTypeName, getTroopStatus, getTroopActionDescription, getTroopStatusColor, getTroopStatusIcon } from '@/constants/gameElements';
import apiService from '@/services/apiService';
import BaseSelectionDialog from './BaseSelectionDialog.vue';

// Standalone helper function that can be imported directly
export function getStatusBadgeStyle(troopMode) {
  const mode = troopMode || 'idle';
  const bgColor = getTroopStatusColor(mode, 0.8);
  return {
    backgroundColor: bgColor
  };
}

export default {
  name: 'TroopActionDialog',
  
  components: {
    BaseSelectionDialog
  },
  
  props: {
    show: {
      type: Boolean,
      required: true
    },
    troop: {
      type: Object,
      required: false,
      default: null
    },
    targetLocation: {
      type: Object,
      required: false,
      default: () => ({ x: 0, y: 0 })
    },
    canMove: {
      type: Boolean,
      default: true
    },
    canAttack: {
      type: Boolean,
      default: false
    },
    village: {
      type: Object,
      required: false,
      default: null
    },
    estimatedTime: {
      type: Number,
      default: 0
    }
  },
  
  data() {
    return {
      selectedAction: null
    }
  },
  
  computed: {
    getTitle() {
      if (!this.troop) return 'Troop Action';
      
      return getTroopTypeName(this.troop.type);
    },
    
    getDescription() {
      if (!this.troop) return 'Select an action for your troops';
      
      const baseDesc = `A group of ${this.troop.quantity} ${getTroopTypeName(this.troop.type).toLowerCase()} from your village.`;
      
      if (this.hasActiveAction) {
        return `${baseDesc} Currently engaged in a ${this.troop.mode.toLowerCase()} action.`;
      }
      
      return baseDesc;
    },
    
    getTypeColor() {
      if (!this.troop) return UI_COLORS.DIALOG.EMPTY_ICON;
      
      return getTroopColor(this.troop.type);
    },
    
    getTypeIcon() {
      if (!this.troop) return 'mdi-account-group';
      
      return getTroopIcon(this.troop.type);
    },
    
    getImageUrl() {
      // You might want to replace this with actual troop images when available
      return ''; // Fallback to icon display
    },
    
    hasCargo() {
      if (!this.troop || !this.troop.backpack) return false;
      
      // Check if any resources are being carried
      return ['wood', 'food', 'stone', 'iron'].some(resource => 
        this.troop.backpack[resource] !== undefined && this.troop.backpack[resource] > 0
      );
    },
    
    hasActiveAction() {
      if (!this.troop || !this.troop.mode) return false;
      
      // Check if the troop is already engaged in an action
      return ['move', 'attack', 'return'].includes(this.troop.mode.toLowerCase());
    }
  },
  
  watch: {
    show(newVal) {
      // Reset selected action when dialog is opened
      if (newVal) {
        this.selectedAction = null;
      }
    }
  },
  
  emits: ['update:show', 'error', 'success', 'action-executed'],
  
  methods: {
    closeDialog() {
      this.$emit('update:show', false);
      console.log('TroopActionDialog: closeDialog called, emitting update:show=false');
    },
    
    getStatusBadgeStyle() {
      // Use the standalone function that we've exported
      return getStatusBadgeStyle(this.troop?.mode);
    },
    
    getTroopStatusIcon() {
      return getTroopStatusIcon(this.troop?.mode);
    },
    
    getTroopStatus() {
      return getTroopStatus(this.troop?.mode);
    },
    
    getTroopActionDescription() {
      return getTroopActionDescription(this.troop?.mode);
    },
    
    getHomeVillageName() {
      if (!this.troop || !this.troop.home_id) return 'Unknown';
      
      // If village data is available, return the name
      if (this.village && this.village.name) {
        return this.village.name;
      }
      
      // Fallback to ID if name not available
      return `Village #${this.troop.home_id.substring(0, 6)}`;
    },
    
    formatLocation(location) {
      if (!location || (location.x === undefined && location.y === undefined)) {
        return 'Unknown';
      }
      
      return `${location.x}, ${location.y}`;
    },
    
    getBackpackAmount(resourceType) {
      if (!this.troop || !this.troop.backpack) {
        return 0;
      }
      
      // Check if the property exists and return its value, or 0 if it doesn't exist
      return this.troop.backpack[resourceType] !== undefined ? this.troop.backpack[resourceType] : 0;
    },
    
    resourceColor(resourceType) {
      return getResourceColor(resourceType);
    },
    
    resourceIcon(resourceType) {
      return getResourceIcon(resourceType);
    },
    
    formatNumber(value) {
      if (value === undefined || value === null) return '0';
      
      if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
      } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
      }
      
      return Math.floor(value).toLocaleString();
    },
    
    formatTime(minutes) {
      if (!minutes) return '0m';
      
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      
      if (hours > 0) {
        return `${hours}h ${mins}m`;
      }
      
      return `${mins}m`;
    },
    
    executeAction(actionType) {
      if (!actionType || !this.troop || !this.targetLocation) return;
      
      // Construct the command using the correct format: "move [troop_id] to loc_x,loc_y"
      let command;
      if (actionType === 'move') {
        command = `move ${this.troop.id} to ${this.targetLocation.x},${this.targetLocation.y}`;
      } else if (actionType === 'attack') {
        command = `attack ${this.troop.id} to ${this.targetLocation.x},${this.targetLocation.y}`;
      } else {
        return;
      }
      
      // Use village ID from troop's home_id if village prop not provided
      const villageId = this.village ? this.village.id : this.troop.home_id;
      
      console.log("Executing command:", command, "for village:", villageId);
      
      // Store command data for API call
      const actionData = {
        villageId, 
        command,
        actionType
      };
      
      // Forcefully close the dialog
      console.log("TroopActionDialog: Closing dialog after action clicked");
      this.$emit('update:show', false);
      
      // Wait a small delay to ensure the UI has time to update 
      // before making the API call
      setTimeout(() => {
        // Execute the command via API
        apiService.executeCommand(actionData.villageId, actionData.command)
          .then(response => {
            // Check if the command was successful
            if (response && response.success === false) {
              const errorMessage = response.message || `Failed to ${actionData.actionType}: ${actionData.command}`;
              this.$emit('error', errorMessage);
              return;
            }
            
            // Show success message
            this.$emit('success', `${actionData.actionType === 'attack' ? 'Attack' : 'Movement'} command issued successfully!`);
            
            // Emit the action event to parent
            this.$emit('action-executed', {
              action: actionData.actionType,
              troopId: this.troop.id,
              targetLocation: this.targetLocation,
              response: response
            });
          })
          .catch(error => {
            console.error(`Failed to execute ${actionData.actionType} command:`, error);
            this.$emit('error', `Error: ${error.message || 'Failed to execute command'}`);
          });
      }, 100);
    }
  }
}
</script>

<style scoped>
.game-panel {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background-color: white;
  margin-bottom: 8px;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  background-color: #f5f5f5;
  font-weight: 600;
  font-size: 14px;
}

.panel-content {
  padding: 10px;
}

.troop-quantity {
  background-color: rgba(33, 150, 243, 0.15);
  color: #1976d2;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

.status-badge {
  color: white;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 12px;
  color: #757575;
  margin-bottom: 4px;
}

.info-value {
  font-weight: 500;
}

.location-display {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.location-value {
  font-weight: 500;
}

.location-value.target {
  color: #4caf50;
  font-weight: 600;
}

.resources-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.mini-resource {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.status-indicator {
  display: flex;
  align-items: center;
  background-color: rgba(33, 150, 243, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #1976d2;
  width: fit-content;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  height: 48px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-btn-content {
  display: flex;
  width: 100%;
  align-items: center;
  position: relative;
  padding-right: 85px; /* Make room for the time display */
}

.action-btn-left {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.action-btn-time {
  display: flex;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.15);
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  position: absolute;
  right: 4px;
}

.mr-1 {
  margin-right: 4px;
}

.mr-2 {
  margin-right: 8px;
}

.mx-2 {
  margin-left: 8px;
  margin-right: 8px;
}

.mb-2 {
  margin-bottom: 8px;
}

.mb-3 {
  margin-bottom: 12px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-4 {
  margin-top: 16px;
}

.rotating-icon {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style> 