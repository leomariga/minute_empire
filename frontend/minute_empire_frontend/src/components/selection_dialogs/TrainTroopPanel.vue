<template>
  <div>
    <!-- Title Section -->
    <div class="section-title mb-2">
      <span class="text-subtitle-1">{{ isTrainingInProgress ? 'Training in Progress' : 'Available Troops' }}</span>
    </div>
    
    <!-- Training in Progress -->
    <div v-if="isTrainingInProgress" class="construction-panel" :style="{ backgroundColor: trainingTypeColor + '10' }">
      <div class="construction-header" :style="{ backgroundColor: trainingTypeColor + '15' }">
        <v-icon :color="trainingTypeColor" size="20" class="mr-2">{{ trainingTypeIcon }}</v-icon>
        <span class="construction-title">Training {{ trainingTypeName }}</span>
      </div>
      
      <div class="construction-content">
        <div class="construction-icon-container" :style="{ backgroundColor: trainingTypeColor + '20' }">
          <v-icon :color="trainingTypeColor" size="48">{{ trainingTypeIcon }}</v-icon>
        </div>
        
        <div class="construction-info">
          <div class="construction-name">{{ trainingTypeName }}</div>
          <v-progress-linear indeterminate :color="trainingTypeColor" class="mb-2 mt-2"></v-progress-linear>
          <div class="construction-time" v-if="trainingTimeRemaining">
            <v-icon size="14" :color="trainingTypeColor" class="mr-1 rotating-icon">mdi-refresh</v-icon>
            {{ trainingTimeRemaining }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Available Troops Grid (hidden when training is in progress) -->
    <div v-else>
      <div class="options-grid-container">
        <div class="options-grid">
          <v-card
            v-for="troop in availableTroops"
            :key="troop.type"
            :ripple="true"
            class="option-card"
            :class="{'selected-option': selectedTroop === troop.type}"
            @click="selectTroop(troop.type)"
          >
            <v-card-item class="pa-3">
              <div class="d-flex align-center">
                <v-icon
                  :color="getTroopColor(troop)"
                  class="mr-2"
                  size="24"
                >
                  {{ getTroopIcon(troop) }}
                </v-icon>
                <span class="text-subtitle-2 font-weight-medium">{{ troop.name }}</span>
              </div>
              
              <!-- Resource requirements -->
              <div class="option-costs mt-2">
                <div class="mini-requirements-compact">
                  <!-- Display all resource types -->
                  <div v-for="resourceType in ['wood', 'food', 'stone', 'iron']" 
                       :key="resourceType" 
                       class="mini-resource-cost-compact"
                       :class="{'insufficient': !hasEnoughResources(resourceType, getCost(troop, resourceType)), 'hidden': !hasCost(troop, resourceType)}">
                    <v-icon size="14" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
                    <span>{{ formatNumber(getCost(troop, resourceType)) }}</span>
                  </div>
                  
                  <!-- Training time -->
                  <div class="mini-time-compact">
                    <v-icon size="14" color="grey-darken-1">mdi-clock-outline</v-icon>
                    <span>{{ formatTime(troop.training_time || 0) }}</span>
                  </div>
                </div>
              </div>
            </v-card-item>
          </v-card>
        </div>
      </div>
      
      <!-- Quantity Input -->
      <div class="quantity-control mt-3 mb-3" v-if="selectedTroop">
        <div class="d-flex align-center">
          <span class="text-body-2 mr-2">Quantity:</span>
          <v-btn density="compact" icon="mdi-minus" variant="text" @click="decreaseQuantity" :disabled="quantity <= 1"></v-btn>
          <v-text-field
            v-model="quantity"
            type="number"
            min="1"
            max="100"
            density="compact"
            hide-details
            class="quantity-input"
            @input="validateQuantity"
          ></v-text-field>
          <v-btn density="compact" icon="mdi-plus" variant="text" @click="increaseQuantity" :disabled="quantity >= 100"></v-btn>
        </div>
        
        <!-- Total resources required -->
        <div class="total-resources mt-2" v-if="selectedTroop">
          <div class="d-flex align-center">
            <span class="text-body-2 mr-2">Total cost:</span>
            <div v-for="resourceType in ['wood', 'food', 'stone', 'iron']" 
                 :key="'total-' + resourceType" 
                 class="mini-resource-cost-compact ml-2"
                 :class="{'insufficient': !hasEnoughResources(resourceType, getTotalCost(resourceType)), 'hidden': !hasCost(getSelectedTroop(), resourceType)}">
              <v-icon size="14" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
              <span>{{ formatNumber(getTotalCost(resourceType)) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Button to train selected troop -->
      <div class="mt-3">
        <v-btn
          block
          color="primary"
          :disabled="!selectedTroop || !canTrainSelected"
          @click="trainSelected"
        >
          <v-icon size="16" class="mr-1">mdi-sword</v-icon>
          Train 
          <span v-if="selectedTroop" class="ml-1">{{ getSelectedTroopName() }} ({{ quantity }})</span>
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script>
import { getResourceColor, getResourceIcon, getTroopIcon, getTroopColor, getTroopTypeName, TROOP_TYPES, getBuildingInfo } from '@/constants/gameElements';

export default {
  name: 'TrainTroopPanel',
  
  props: {
    building: {
      type: Object,
      required: true
    },
    village: {
      type: Object,
      required: true
    },
    isTrainingInProgress: {
      type: Boolean,
      default: false
    },
    trainingTypeName: {
      type: String,
      default: ''
    },
    trainingTypeColor: {
      type: String,
      default: '#607D8B'
    },
    trainingTypeIcon: {
      type: String,
      default: 'mdi-sword'
    },
    trainingTimeRemaining: {
      type: String,
      default: ''
    }
  },
  
  data() {
    return {
      selectedTroop: null,
      quantity: 1
    }
  },
  
  computed: {
    availableTroops() {
      if (!this.village || !this.village.base_costs || !this.village.base_costs.troops) {
        return [];
      }
      
      // Get building info and check if it has troops
      const buildingInfo = getBuildingInfo(this.building.type);
      if (!buildingInfo || !buildingInfo.troops || buildingInfo.troops.length === 0) {
        return [];
      }
      
      // Get the troop type for this building - first one in the troops array
      const troopType = buildingInfo.troops[0]; // This is the lowercase troop type matching the API
      
      if (!this.village.base_costs.troops[troopType]) {
        return []; // No matching troop type found in API data
      }
      
      // Get cost and training time from the API
      const troopData = this.village.base_costs.troops[troopType];
      const trainingTime = this.village.base_creation_times.troops[troopType] || 0;
      
      return [{
        type: troopType.toUpperCase(), // Convert to uppercase for our internal use
        name: getTroopTypeName(troopType),
        cost: troopData,
        training_time: trainingTime
      }];
    },
    
    canTrainSelected() {
      if (!this.selectedTroop || this.quantity < 1) return false;
      
      const troop = this.getSelectedTroop();
      if (!troop) return false;
      
      // Check if we have enough resources for all costs
      for (const resourceType of ['wood', 'stone', 'iron', 'food']) {
        const totalCost = this.getTotalCost(resourceType);
        if (totalCost > 0 && !this.hasEnoughResources(resourceType, totalCost)) {
          return false;
        }
      }
      
      return true;
    }
  },
  
  methods: {
    selectTroop(troopType) {
      this.selectedTroop = troopType === this.selectedTroop ? null : troopType;
      this.quantity = 1; // Reset quantity when selecting a new troop
    },
    
    increaseQuantity() {
      this.quantity = Math.min(100, parseInt(this.quantity) + 1);
    },
    
    decreaseQuantity() {
      this.quantity = Math.max(1, parseInt(this.quantity) - 1);
    },
    
    validateQuantity() {
      let val = parseInt(this.quantity);
      if (isNaN(val) || val < 1) {
        this.quantity = 1;
      } else if (val > 100) {
        this.quantity = 100;
      } else {
        this.quantity = val;
      }
    },
    
    trainSelected() {
      if (!this.selectedTroop) return;
      
      this.$emit('train', {
        troopType: this.selectedTroop,
        quantity: this.quantity,
        buildingSlot: this.building.slot,
        buildingType: this.building.type
      });
    },
    
    getTroopName(troopType) {
      return getTroopTypeName(troopType);
    },
    
    getTroopColor(troop) {
      return getTroopColor(troop.type);
    },
    
    getTroopIcon(troop) {
      return getTroopIcon(troop.type);
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
    
    hasCost(troop, resourceType) {
      if (!troop || !troop.cost) {
        return false;
      }
      
      return resourceType in troop.cost && troop.cost[resourceType] > 0;
    },
    
    getCost(troop, resourceType) {
      if (!troop || !troop.cost) {
        return 0;
      }
      
      return troop.cost[resourceType] || 0;
    },
    
    getTotalCost(resourceType) {
      const troop = this.getSelectedTroop();
      if (!troop || !troop.cost) {
        return 0;
      }
      
      return (troop.cost[resourceType] || 0) * this.quantity;
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
    
    getSelectedTroop() {
      if (!this.selectedTroop) return null;
      return this.availableTroops.find(troop => troop.type === this.selectedTroop);
    },
    
    getSelectedTroopName() {
      const troop = this.getSelectedTroop();
      return troop ? troop.name : '';
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
  max-height: 220px;
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

.quantity-control {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.02);
}

.quantity-input {
  width: 70px;
  margin: 0 8px;
}

.total-resources {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding-top: 8px;
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

.ml-2 {
  margin-left: 8px;
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

.mb-3 {
  margin-bottom: 12px;
}

.gap-2 {
  gap: 8px;
}
</style> 