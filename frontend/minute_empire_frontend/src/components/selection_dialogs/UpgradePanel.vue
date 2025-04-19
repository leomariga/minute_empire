<template>
  <div class="game-panel" :class="{
    'disabled-panel': isBeingUpgraded,
    'destroying-panel': isBeingDestroyed
  }">
    <div class="panel-header">
      <v-icon size="16" :color="isBeingDestroyed ? 'error-darken-2' : 'amber-darken-3'" class="mr-2">
        {{ isBeingDestroyed ? 'mdi-delete-forever' : 'mdi-hammer' }}
      </v-icon>
      <span>{{ isBeingDestroyed ? 'Destroying' : 'Upgrade' }}</span>
      <div class="level-indicator ml-1" v-if="!isBeingDestroyed">→ Lv.{{ (item?.level || 0) + 1 }}</div>
    </div>
    
    <div class="panel-content mini-padding">
      <!-- Resources and Time (only when not upgrading) -->
      <div v-if="!isBeingUpgraded && !isBeingDestroyed" class="mini-requirements">
        <div class="mini-resources">
          <!-- Display all resource types, default to 0 if not needed -->
          <div v-for="resourceType in ['wood', 'food', 'stone', 'iron']" 
               :key="resourceType" 
               class="mini-resource-cost"
               :class="{'insufficient': hasCost(resourceType) && !hasEnoughResources(resourceType, getCost(resourceType))}">
            <v-icon size="14" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
            <span>{{ formatNumber(getCost(resourceType)) }}</span>
          </div>
        </div>
        
        <div class="mini-time">
          <v-icon size="14" color="grey-darken-1">mdi-clock-outline</v-icon>
          <span>{{ formatTime(item.upgrade_time) }}</span>
        </div>
      </div>
      
      <!-- Destruction in Progress Message -->
      <div v-if="isBeingDestroyed" class="destruction-message">
        <v-icon size="18" color="error" class="mr-2 destroy-icon">mdi-alert</v-icon>
        <span class="destruction-text">Destruction in progress...</span>
      </div>
      
      <!-- Button Container -->
      <div class="button-container">
        <!-- Upgrade Button -->
        <v-btn
          class="mt-2 mini-btn action-btn primary-action"
          :color="isBeingDestroyed ? 'error' : (isBeingUpgraded ? 'info' : 'primary')"
          :disabled="!canUpgrade || !hasSufficientResources || isBeingUpgraded || isBeingDestroyed"
          @click="handleUpgrade"
          variant="elevated"
        >
          <v-icon v-if="isBeingDestroyed" size="16" class="mr-1 destroy-icon">mdi-delete-forever</v-icon>
          <v-icon v-else-if="isBeingUpgraded" size="16" class="mr-1 rotating-icon">mdi-refresh</v-icon>
          <v-icon v-else size="16" class="mr-1">mdi-arrow-up</v-icon>
          <span>{{ isBeingDestroyed ? 'Destroying' : (isBeingUpgraded ? 'Upgrading' : 'Upgrade') }}</span>
        </v-btn>
        
        <!-- Destroy Button -->
        <v-btn
          v-if="!isBeingUpgraded && !isBeingDestroyed && item.type !== 'town'"
          color="error"
          variant="outlined"
          :loading="destructionInProgress"
          class="mt-2 destroy-btn"
          @click="openDestructionDialog"
          :disabled="destructionInProgress"
          size="small"
          icon
        >
          <v-tooltip activator="parent" location="top">Destroy</v-tooltip>
          <v-icon size="16">mdi-delete</v-icon>
        </v-btn>
      </div>
    </div>
    
    <!-- Destruction Confirmation Dialog -->
    <teleport to="body">
      <v-dialog
        v-model="showConfirmDialog"
        max-width="400"
        persistent
        class="confirmation-dialog"
        :retain-focus="true"
        :scrim="true"
        :z-index="9999"
        eager
        width="90%"
      >
        <v-card elevation="24" class="destroy-dialog pa-0">
          <v-card-title class="text-h6 pa-4 bg-error-lighten-4">
            <v-icon color="error" class="mr-2">mdi-alert</v-icon>
            Confirm Destruction
          </v-card-title>
          <v-card-text class="pa-4 pt-5">
            <p class="mb-2">Are you sure you want to destroy this {{ item.type === 'food' || item.type === 'wood' || item.type === 'stone' || item.type === 'iron' ? 'resource field' : 'building' }}?</p>
            <p class="text-caption">This action will permanently remove the item and cannot be undone.</p>
          </v-card-text>
          <v-card-actions class="pa-4 pt-2">
            <v-spacer></v-spacer>
            <v-btn color="grey" variant="text" @click="cancelDestruction">
              Cancel
            </v-btn>
            <v-btn color="error" variant="elevated" @click="destroyItem">
              Yes, Destroy
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </teleport>
  </div>
</template>

<script>
import { getResourceColor, getResourceIcon } from '@/constants/gameElements';
import apiService from '@/services/apiService';

export default {
  name: 'UpgradePanel',
  
  props: {
    item: {
      type: Object,
      required: true
    },
    isBeingUpgraded: {
      type: Boolean,
      default: false
    },
    village: {
      type: Object,
      required: true
    }
  },
  
  data() {
    return {
      showConfirmDialog: false,
      destructionInProgress: false
    };
  },
  
  watch: {
    showConfirmDialog(newVal) {
      console.log('UpgradePanel - Confirm dialog visibility:', newVal);
      // Force redraw when dialog is opened
      if (newVal) {
        this.$nextTick(() => {
          window.dispatchEvent(new Event('resize'));
        });
      }
    }
  },
  
  computed: {
    canUpgrade() {
      if (!this.item) return false;
      return this.item.level < 10 && !this.isBeingUpgraded;
    },
    
    isBeingDestroyed() {
      if (!this.village || !this.village.construction_tasks || !this.item) {
        return false;
      }
      
      // Check if there's an active destruction task for this item
      const itemType = this.item.type === 'food' || this.item.type === 'wood' || 
                      this.item.type === 'stone' || this.item.type === 'iron' ? 
                      'field' : 'building';
      
      return this.village.construction_tasks.some(task => 
        task.task_type === `destroy_${itemType}` && 
        Number(task.slot) === Number(this.item.slot) &&
        !task.processed
      );
    },
    
    hasSufficientResources() {
      // If no upgrade costs are available, or no resources data, we can't determine if sufficient
      if (!this.item || !this.item.upgrade_cost || !this.village || !this.village.resources) {
        return false;
      }
      
      try {
        for (const [resource, cost] of Object.entries(this.item.upgrade_cost)) {
          if (!this.hasEnoughResources(resource, cost)) {
            return false;
          }
        }
        return true;
      } catch (error) {
        console.error('Error checking resource sufficiency:', error);
        return false;
      }
    }
  },
  
  methods: {
    handleUpgrade() {
      this.$emit('upgrade', {
        type: this.item.type,
        slot: this.item.slot,
        currentLevel: this.item.level
      });
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
    
    hasEnoughResources(resourceType, cost) {
      if (!this.village || !this.village.resources) {
        return false;
      }
      
      const available = this.getAvailableResource(resourceType);
      return available >= cost;
    },
    
    getAvailableResource(resourceType) {
      if (!this.village || !this.village.resources || !this.village.resources[resourceType]) {
        return 0;
      }
      
      return this.village.resources[resourceType].current;
    },
    
    hasCost(resourceType) {
      if (!this.item || !this.item.upgrade_cost) {
        return false;
      }
      
      return resourceType in this.item.upgrade_cost && this.item.upgrade_cost[resourceType] > 0;
    },
    
    getCost(resourceType) {
      if (!this.item || !this.item.upgrade_cost) {
        return 0;
      }
      
      return this.item.upgrade_cost[resourceType] || 0;
    },
    
    openDestructionDialog() {
      console.log("Opening destruction dialog");
      this.showConfirmDialog = true;
      
      // Force a redraw of the dialog
      this.$nextTick(() => {
        console.log("Dialog state after nextTick:", this.showConfirmDialog);
        setTimeout(() => {
          const dialogElement = document.querySelector('.confirmation-dialog');
          console.log("Dialog element found:", !!dialogElement);
        }, 100);
      });
    },
    
    cancelDestruction() {
      console.log("Cancelling destruction");
      this.showConfirmDialog = false;
    },
    
    destroyItem() {
      console.log("Destruction confirmed, proceeding with destruction");
      this.destructionInProgress = true;
      
      // Close the dialog
      this.showConfirmDialog = false;
      
      // Determine if this is a resource field or a building
      const itemType = this.item.type === 'food' || this.item.type === 'wood' || 
                        this.item.type === 'stone' || this.item.type === 'iron' ? 
                        'field' : 'building';
      
      // Emit the destroy event with the necessary data
      // This follows the same pattern as handleUpgrade
      this.$emit('destroy', {
        type: this.item.type,
        slot: this.item.slot,
        itemType: itemType,
        villageId: this.village.id
      });
      
      // Reset the destruction progress state
      this.destructionInProgress = false;
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

.mini-padding {
  padding: 8px;
}

.disabled-panel {
  opacity: 0.8;
}

.mr-2 {
  margin-right: 8px;
}

.ml-1 {
  margin-left: 4px;
}

.ml-2 {
  margin-left: 8px;
}

.level-indicator {
  font-weight: 600;
  font-size: 12px;
  color: #757575;
}

/* Mini Requirements */
.mini-requirements {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.mini-resources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mini-resource-cost {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.insufficient {
  color: #f44336;
}

.mini-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #757575;
}

/* Buttons */
.button-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 8px;
}

.mini-btn {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 13px;
  height: 32px;
  min-width: 90px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Primary action (upgrade) takes more space */
.primary-action {
  flex: 3;
}

/* Square destroy button */
.destroy-btn {
  min-width: 36px !important;
  width: 36px !important;
  height: 36px !important;
  padding: 0 !important;
  margin-left: 8px !important;
}

.mt-2 {
  margin-top: 8px;
}

.mr-1 {
  margin-right: 4px;
}

.rotating-icon {
  animation: spin 2s linear infinite;
}

.destroy-icon {
  animation: pulse 1.5s ease-in-out infinite;
  color: #d32f2f !important; /* Dark red */
}

@keyframes pulse {
  0% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
  100% { opacity: 0.7; transform: scale(1); }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Enhancement for dialog visibility */
:deep(.confirmation-dialog) {
  position: fixed !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  z-index: 10000 !important;
}

/* Force dialog to be visible */
:deep(.v-dialog) {
  position: fixed !important;
  z-index: 10000 !important;
  max-height: 90vh;
  margin: 0 auto;
  width: 100%;
  max-width: 400px !important;
  display: flex !important;
  box-shadow: 0 11px 15px -7px rgba(0,0,0,.2), 0 24px 38px 3px rgba(0,0,0,.14), 0 9px 46px 8px rgba(0,0,0,.12) !important;
}

:deep(.v-overlay__scrim) {
  opacity: 0.7 !important;
  background-color: rgba(0, 0, 0, 0.7) !important;
}

:deep(.v-overlay--active) {
  z-index: 9999 !important;
  position: fixed !important;
  inset: 0px !important; 
}

.destroy-dialog {
  z-index: 9999 !important;
  position: relative;
  overflow: visible !important;
  border: 2px solid rgba(244, 67, 54, 0.3);
}

.destroying-panel {
  opacity: 0.9;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.destroying-panel .panel-header {
  background-color: rgba(244, 67, 54, 0.1);
}

/* Add CSS for the destruction message */
.destruction-message {
  display: flex;
  align-items: center;
  padding: 8px;
  margin-bottom: 8px;
  background-color: rgba(244, 67, 54, 0.08);
  border-radius: 4px;
}

.destruction-text {
  color: #d32f2f;
  font-weight: 500;
  font-size: 14px;
}
</style> 