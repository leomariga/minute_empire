<template>
  <div class="game-panel mb-3">
    <div class="panel-header" :style="`background-color: ${getTypeColor}20`">
      <v-icon size="18" :color="getTypeColor" class="mr-2">mdi-factory</v-icon>
      <span>Production Rate</span>
    </div>
    
    <div class="panel-content">
      <div class="mini-display">
        <div class="d-flex flex-column w-100">
          <!-- Current production rates -->
          <div class="production-row">
            <div class="production-header d-flex mb-0">
              <div class="production-labels">
                <div class="production-label">Production:</div>
                <div v-if="!isBeingUpgraded && hasNextLevelProduction" class="next-level-main-label">
                  in level {{ (field?.level || 0) + 1 }}
                </div>
              </div>
              <div class="d-flex flex-wrap production-values">
                <template v-for="resourceType in ['wood', 'food', 'stone', 'iron']" :key="resourceType">
                  <div v-if="hasProduction(resourceType)" class="mini-resource-production">
                    <v-icon size="16" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
                    <div class="d-flex flex-column" style="line-height: 1.1">
                      <span>{{ formatNumber(getCurrentProductionRate(resourceType)) }}/h</span>
                      <div v-if="!isBeingUpgraded && hasNextLevelProductionForType(resourceType)" class="next-level-row">
                        <span class="next-level-rate">{{ formatNumber(getNextLevelProductionRate(resourceType)) }}/h</span>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- If no production -->
      <div v-if="!hasAnyProduction" class="mini-empty">No production</div>
    </div>
  </div>
</template>

<script>
import { getResourceColor, getResourceIcon, UI_COLORS } from '@/constants/gameElements';

export default {
  name: 'ResourceProductionPanel',
  
  props: {
    field: {
      type: Object,
      required: true
    },
    isBeingUpgraded: {
      type: Boolean,
      default: false
    }
  },
  
  computed: {
    getTypeColor() {
      return this.field && this.field.type ? 
        getResourceColor(this.field.type) : 
        UI_COLORS.DIALOG.EMPTY_ICON;
    },
    
    hasNextLevelProduction() {
      if (!this.field || !this.field.next_level_production_rate) {
        return false;
      }
      
      return Object.values(this.field.next_level_production_rate).some(rate => rate > 0);
    },
    
    hasAnyProduction() {
      if (!this.field || !this.field.current_production_rate) {
        return false;
      }
      
      return Object.values(this.field.current_production_rate).some(rate => rate > 0);
    }
  },
  
  methods: {
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
    
    hasProduction(resourceType) {
      if (!this.field || !this.field.current_production_rate) {
        return false;
      }
      
      if (!(resourceType in this.field.current_production_rate)) {
        return false;
      }
      
      const value = this.field.current_production_rate[resourceType];
      return value && parseFloat(value) > 0;
    },
    
    getCurrentProductionRate(resourceType) {
      if (!this.field || !this.field.current_production_rate || !this.field.current_production_rate[resourceType]) return 0;
      return this.field.current_production_rate[resourceType];
    },
    
    hasNextLevelProductionForType(resourceType) {
      if (!this.field || !this.field.next_level_production_rate) {
        return false;
      }
      
      if (!(resourceType in this.field.next_level_production_rate)) {
        return false;
      }
      
      const value = this.field.next_level_production_rate[resourceType];
      return value && parseFloat(value) > 0;
    },
    
    getNextLevelProductionRate(resourceType) {
      if (!this.field || !this.field.next_level_production_rate || !this.field.next_level_production_rate[resourceType]) return 0;
      return this.field.next_level_production_rate[resourceType];
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

/* Production Display */
.mini-display {
  display: flex;
  align-items: center;
  width: 100%;
}

.production-row {
  display: flex;
  flex-direction: column;
  padding: 4px 6px;
  border-radius: 4px;
}

.production-header {
  display: flex;
  width: 100%;
}

.production-labels {
  min-width: 80px;
  display: flex;
  flex-direction: column;
}

.production-values {
  flex: 1;
  gap: 8px;
}

.production-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.mr-2 {
  margin-right: 8px;
}

.mb-1 {
  margin-bottom: 4px;
}

.mini-resource-production {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
  margin-right: 8px;
  margin-bottom: 2px;
}

.mini-empty {
  color: #9e9e9e;
  font-style: italic;
  font-size: 12px;
  text-align: center;
  padding: 4px 0;
}

/* Next level styling */
.next-level-main-label {
  font-size: 9px;
  color: #4caf50;
  font-style: italic;
  margin-right: 4px;
  white-space: nowrap;
}

.next-level-row {
  display: flex;
  align-items: center;
  margin-top: 1px;
}

.next-level-rate {
  font-size: 11px;
  color: #4caf50;
  font-weight: 500;
  line-height: 1;
}
</style> 