<template>
  <div>
    <!-- Title Section -->
    <div class="section-title mb-2">
      <span class="text-subtitle-1">{{ isBeingCreated ? 'Construction in Progress' : 'Available Options' }}</span>
    </div>
    
    <!-- Construction in Progress -->
    <div v-if="isBeingCreated" class="construction-panel" :style="{ backgroundColor: creationTypeColor + '10' }">
      <div class="construction-header" :style="{ backgroundColor: creationTypeColor + '15' }">
        <v-icon :color="creationTypeColor" size="20" class="mr-2">{{ creationTypeIcon }}</v-icon>
        <span class="construction-title">Creating {{ creationTypeName }}</span>
      </div>
      
      <div class="construction-content">
        <div class="construction-icon-container" :style="{ backgroundColor: creationTypeColor + '20' }">
          <v-icon :color="creationTypeColor" size="48">{{ creationTypeIcon }}</v-icon>
        </div>
        
        <div class="construction-info">
          <div class="construction-name">{{ creationTypeName }}</div>
          <v-progress-linear indeterminate :color="creationTypeColor" class="mb-2 mt-2"></v-progress-linear>
          <div class="construction-time" v-if="creationTimeRemaining">
            <v-icon size="14" :color="creationTypeColor" class="mr-1 rotating-icon">mdi-refresh</v-icon>
            {{ creationTimeRemaining }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Available Options Grid (hidden when construction is in progress) -->
    <div v-else>
      <div class="options-grid-container">
        <div class="options-grid">
          <v-card
            v-for="option in availableOptions"
            :key="option.type"
            :ripple="true"
            class="option-card"
            :class="{'selected-option': selectedOption === option.type}"
            @click="selectOption(option.type)"
          >
            <v-card-item class="pa-3">
              <div class="d-flex align-center">
                <v-icon
                  :color="getOptionColor(option)"
                  class="mr-2"
                  size="24"
                >
                  {{ getOptionIcon(option) }}
                </v-icon>
                <span class="text-subtitle-2 font-weight-medium">{{ option.name }}</span>
              </div>
              
              <!-- Resource requirements -->
              <div class="option-costs mt-2">
                <div class="mini-requirements-compact">
                  <!-- Display all resource types -->
                  <div v-for="resourceType in ['wood', 'food', 'stone', 'iron']" 
                       :key="resourceType" 
                       class="mini-resource-cost-compact"
                       :class="{'insufficient': !hasEnoughResources(resourceType, getCost(option, resourceType)), 'hidden': !hasCost(option, resourceType)}">
                    <v-icon size="14" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
                    <span>{{ formatNumber(getCost(option, resourceType)) }}</span>
                  </div>
                  
                  <!-- Creation time -->
                  <div class="mini-time-compact">
                    <v-icon size="14" color="grey-darken-1">mdi-clock-outline</v-icon>
                    <span>{{ formatTime(option.creation_time || 0) }}</span>
                  </div>
                </div>
              </div>
            </v-card-item>
          </v-card>
        </div>
      </div>
      
      <!-- Button to build selected option -->
      <div class="mt-3">
        <v-btn
          block
          color="primary"
          :disabled="!selectedOption || !canBuildSelected"
          @click="buildSelected"
        >
          <v-icon size="16" class="mr-1">mdi-hammer-wrench</v-icon>
          Create 
          <span v-if="selectedOption" class="ml-1">{{ getSelectedOptionName() }}</span>
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script>
import { getResourceColor, getResourceIcon, getBuildingColor, getBuildingIcon } from '@/constants/gameElements';

export default {
  name: 'CreationPanel',
  
  props: {
    type: {
      type: String,
      required: true,
      validator: value => ['resource', 'building'].includes(value)
    },
    slotId: {
      type: Number,
      required: true
    },
    availableOptions: {
      type: Array,
      required: true
    },
    village: {
      type: Object,
      required: true
    },
    isBeingCreated: {
      type: Boolean,
      default: false
    },
    creationTypeName: {
      type: String,
      default: ''
    },
    creationTypeColor: {
      type: String,
      default: '#607D8B'
    },
    creationTypeIcon: {
      type: String,
      default: 'mdi-hammer-wrench'
    },
    creationTimeRemaining: {
      type: String,
      default: ''
    }
  },
  
  data() {
    return {
      selectedOption: null
    }
  },
  
  computed: {
    canBuildSelected() {
      if (!this.selectedOption) return false;
      
      const option = this.availableOptions.find(opt => opt.type === this.selectedOption);
      if (!option) return false;
      
      // Check if we have enough resources for all costs
      for (const [resourceType, cost] of Object.entries(option.cost || {})) {
        if (!this.hasEnoughResources(resourceType, cost)) {
          return false;
        }
      }
      
      return true;
    }
  },
  
  methods: {
    selectOption(optionType) {
      this.selectedOption = optionType === this.selectedOption ? null : optionType;
    },
    
    buildSelected() {
      if (!this.selectedOption) return;
      
      // Emit complete data with type, slot, and buildingType
      this.$emit('create', {
        type: this.type,
        slot: this.slotId,
        buildingType: this.selectedOption
      });
    },
    
    getOptionColor(option) {
      if (this.type === 'resource') {
        return getResourceColor(option.type);
      } else {
        return getBuildingColor(option.type);
      }
    },
    
    getOptionIcon(option) {
      if (this.type === 'resource') {
        return getResourceIcon(option.type);
      } else {
        return getBuildingIcon(option.type);
      }
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
    
    hasCost(option, resourceType) {
      if (!option || !option.cost) {
        return false;
      }
      
      return resourceType in option.cost && option.cost[resourceType] > 0;
    },
    
    getCost(option, resourceType) {
      if (!option || !option.cost) {
        return 0;
      }
      
      return option.cost[resourceType] || 0;
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
    
    getSelectedOptionName() {
      const option = this.availableOptions.find(opt => opt.type === this.selectedOption);
      return option ? option.name : '';
    }
  }
}
</script>

<style scoped>
.section-title {
  font-weight: 600;
  color: #424242;
}

.options-grid-container {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 8px;
  margin-bottom: 12px;
}

.options-grid-container::-webkit-scrollbar {
  width: 8px;
}

.options-grid-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.options-grid-container::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.options-grid-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  padding-right: 4px;
}

.option-card {
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.option-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
}

.selected-option {
  border: 2px solid #1976d2;
  background-color: rgba(25, 118, 210, 0.05);
}

.option-costs {
  font-size: 12px;
}

/* Construction Panel Styles */
.construction-panel {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background-color: white;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.construction-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.construction-title {
  flex-grow: 1;
}

.construction-content {
  display: flex;
  padding: 16px;
  align-items: center;
}

.construction-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 90px;
  border-radius: 8px;
  margin-right: 18px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.construction-info {
  flex-grow: 1;
}

.construction-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.construction-time {
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
  margin-top: 6px;
}

.rotating-icon {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Existing Styles */
.mini-requirements-compact {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 2px;
}

.mini-resource-cost-compact {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
}

.mini-time-compact {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  color: #757575;
  margin-left: auto;
}

.insufficient {
  color: #f44336;
}

.hidden {
  display: none;
}

.mr-1 {
  margin-right: 4px;
}

.mr-2 {
  margin-right: 8px;
}

.ml-1 {
  margin-left: 4px;
}

.mt-1 {
  margin-top: 4px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-3 {
  margin-top: 12px;
}

.mb-2 {
  margin-bottom: 8px;
}

.gap-2 {
  gap: 8px;
}
</style> 