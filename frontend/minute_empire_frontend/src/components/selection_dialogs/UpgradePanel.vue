<template>
  <div class="game-panel" :class="{'disabled-panel': isBeingUpgraded}">
    <div class="panel-header">
      <v-icon size="16" color="amber-darken-3" class="mr-2">mdi-hammer</v-icon>
      <span>Upgrade</span>
      <div class="level-indicator ml-1">→ Lv.{{ (item?.level || 0) + 1 }}</div>
    </div>
    
    <div class="panel-content mini-padding">
      <!-- Resources and Time (only when not upgrading) -->
      <div v-if="!isBeingUpgraded" class="mini-requirements">
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
      
      <!-- Upgrade Button -->
      <v-btn
        block
        class="mt-2 mini-btn"
        :color="isBeingUpgraded ? 'info' : 'primary'"
        :disabled="!canUpgrade || !hasSufficientResources || isBeingUpgraded"
        @click="handleUpgrade"
      >
        <v-icon v-if="isBeingUpgraded" size="16" class="mr-1 rotating-icon">mdi-refresh</v-icon>
        <v-icon v-else size="16" class="mr-1">mdi-arrow-up</v-icon>
        <span>{{ isBeingUpgraded ? 'Upgrading' : 'Upgrade' }}</span>
      </v-btn>
    </div>
  </div>
</template>

<script>
import { getResourceColor, getResourceIcon } from '@/constants/gameElements';

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
  
  computed: {
    canUpgrade() {
      if (!this.item) return false;
      return this.item.level < 10 && !this.isBeingUpgraded;
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

/* Mini Button */
.mini-btn {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 13px;
  height: 32px;
}

.rotating-icon {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style> 