<template>
  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    :max-width="isMobile ? '100%' : '450'"
    :fullscreen="isMobile"
    transition="dialog-bottom-transition"
    @click:outside="closeDialog"
  >
    <v-card class="selection-dialog">
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-4">
        <v-icon
          :color="getTypeColor"
          class="mr-2"
          size="24"
        >
          {{ getTypeIcon }}
        </v-icon>
        <span class="text-h6 font-weight-bold">
          {{ title }}
        </span>
        <v-spacer></v-spacer>
        <div v-if="!isEmpty && fieldOrBuilding" class="current-level">
          Level {{ fieldOrBuilding?.level || 0 }}
        </div>
        <v-btn
          icon
          @click="closeDialog"
          class="ml-2"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <!-- Content -->
      <v-card-text class="pa-4">
        <!-- Image placeholder -->
        <div class="image-container mb-4">
          <v-img
            :src="imageUrl"
            :aspect-ratio="16/9"
            cover
            class="rounded-lg"
          >
            <template v-slot:placeholder>
              <v-row
                class="fill-height ma-0"
                align="center"
                justify="center"
              >
                <v-progress-circular
                  indeterminate
                  color="primary"
                ></v-progress-circular>
              </v-row>
            </template>
            
            <!-- Fallback content if image doesn't load -->
            <template v-slot:error>
              <v-row class="fill-height ma-0" align="center" justify="center">
                <div class="image-fallback" :style="`background-color: ${getTypeColor}15`">
                  <v-icon :color="getTypeColor" size="64">{{ getTypeIcon }}</v-icon>
                  <div class="text-subtitle-1 mt-2">{{ title }}</div>
                </div>
              </v-row>
            </template>
          </v-img>
          
          <!-- Badges overlaid on image -->
          <div class="badges-overlay">
            <div class="badge slot-badge">
              <v-icon size="14" color="white">mdi-map-marker</v-icon>
              <span>Slot {{ slotId }}</span>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="description mb-4">
          <p class="text-body-1">
            {{ description }}
          </p>
        </div>

        <!-- Production Stats & Upgrade Requirements -->
        <template v-if="!isEmpty && fieldOrBuilding">
          <!-- Production Rates / Bonuses -->
          <div class="game-panel mb-3">
            <div class="panel-header" :style="`background-color: ${getTypeColor}20`">
              <v-icon size="18" :color="getTypeColor" class="mr-2">{{ getProductionIcon }}</v-icon>
              <span>{{ getProductionTitle }}</span>
            </div>
            
            <div class="panel-content">
              <!-- Resource Fields - show production rates -->
              <template v-if="type === 'resource'">
                <div class="mini-display">
                  <div class="d-flex flex-column w-100">
                    <!-- Current production rates -->
                    <div class="production-row">
                      <div class="production-header d-flex mb-0">
                        <div class="production-labels">
                          <div class="production-label">Production:</div>
                          <div v-if="!isBeingUpgraded && fieldOrBuilding.next_level_production_rate" class="next-level-main-label">
                            in level {{ (fieldOrBuilding?.level || 0) + 1 }}
                          </div>
                        </div>
                        <div class="d-flex flex-wrap production-values">
                          <template v-for="resourceType in ['wood', 'food', 'stone', 'iron']" :key="resourceType">
                            <div v-if="hasProduction(resourceType)" class="mini-resource-production">
                              <v-icon size="16" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
                              <div class="d-flex flex-column" style="line-height: 1.1">
                                <span>{{ formatNumber(getCurrentProductionRate(fieldOrBuilding, resourceType)) }}/h</span>
                                <div v-if="!isBeingUpgraded && hasNextLevelProduction(resourceType)" class="next-level-row">
                                  <span class="next-level-rate">{{ formatNumber(getNextLevelProductionRate(fieldOrBuilding, resourceType)) }}/h</span>
                                </div>
                              </div>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- Buildings - show production bonuses -->
              <template v-else>
                <div class="mini-display">
                  <div class="d-flex flex-column w-100">
                    <!-- Current production bonuses -->
                    <div class="production-row">
                      <div class="production-header d-flex mb-0">
                        <div class="production-labels">
                          <div class="production-label">Bonus:</div>
                          <div v-if="!isBeingUpgraded && hasNextLevelBonuses" class="next-level-main-label">
                            in level {{ (fieldOrBuilding?.level || 0) + 1 }}
                          </div>
                        </div>
                        <div class="d-flex flex-wrap production-values">
                          <template v-for="resourceType in ['wood', 'food', 'stone', 'iron']" :key="resourceType">
                            <div v-if="hasBonus(resourceType)" class="mini-resource-production">
                              <v-icon size="16" :color="resourceColor(resourceType)">{{ resourceIcon(resourceType) }}</v-icon>
                              <div class="d-flex flex-column" style="line-height: 1.1">
                                <span>+{{ formatPercent(getCurrentBonus(resourceType)) }}</span>
                                <div v-if="!isBeingUpgraded && hasNextLevelBonus(resourceType)" class="next-level-row">
                                  <span class="next-level-rate">+{{ formatPercent(getNextLevelBonus(resourceType)) }}</span>
                                </div>
                              </div>
                            </div>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- If no bonuses -->
                <div v-if="!hasAnyProductionBonus" class="mini-empty">No bonuses</div>
              </template>
            </div>
          </div>

          <!-- Upgrade Requirements -->
          <div class="game-panel" :class="{'disabled-panel': isBeingUpgraded}">
            <div class="panel-header">
              <v-icon size="16" color="amber-darken-3" class="mr-2">mdi-hammer</v-icon>
              <span>Upgrade</span>
              <div class="level-indicator ml-1">→ Lv.{{ (fieldOrBuilding?.level || 0) + 1 }}</div>
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
                  <span>{{ formatTime(fieldOrBuilding.upgrade_time) }}</span>
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
        
        <!-- Empty State -->
        <div v-if="isEmpty" class="mini-empty-slot">
          <v-icon :color="getTypeColor" size="32">{{ getTypeIcon }}</v-icon>
          <div>{{ type.charAt(0).toUpperCase() + type.slice(1) }} Slot</div>
        </div>

        <!-- Future expansion slots -->
        <slot name="additional-info"></slot>

        <!-- DEBUG INFO - Hidden
        <div class="debug-info mb-2" style="border: 1px dashed red; padding: 8px; font-size: 11px;">
          <div>Has field: {{ !!fieldOrBuilding }}</div>
          <div>Has current_production_rate: {{ !!fieldOrBuilding?.current_production_rate }}</div>
          <div>Resource Types: {{ fieldOrBuilding?.current_production_rate ? Object.keys(fieldOrBuilding.current_production_rate).join(', ') : 'none' }}</div>
          <div>Wood: {{ getCurrentProductionRate(fieldOrBuilding, 'wood') }}</div>
          <div>Food: {{ getCurrentProductionRate(fieldOrBuilding, 'food') }}</div>
          <div>Stone: {{ getCurrentProductionRate(fieldOrBuilding, 'stone') }}</div>
          <div>Iron: {{ getCurrentProductionRate(fieldOrBuilding, 'iron') }}</div>
        </div> -->
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { getResourceColor, getResourceIcon, getBuildingColor, getBuildingIcon, getResourceInfo, getBuildingInfo, UI_COLORS, getResourceFieldImageRef, getBuildingImageRef } from '@/constants/gameElements';

export default {
  name: 'MapSelectionDialog',
  
  props: {
    show: {
      type: Boolean,
      required: true
    },
    slotId: {
      type: Number,
      required: true
    },
    type: {
      type: String,
      required: true,
      validator: value => ['resource', 'building'].includes(value)
    },
    isEmpty: {
      type: Boolean,
      default: false
    },
    village: {
      type: Object,
      required: false,
      default: null
    }
  },
  
  data() {
    return {
      windowWidth: window.innerWidth
    }
  },
  
  computed: {
    fieldOrBuilding() {
      if (this.isEmpty || !this.village) return null;
      
      try {
        if (this.type === 'resource') {
          return this.village.resource_fields?.find(field => field && field.slot === this.slotId) || null;
        } else if (this.type === 'building') {
          return this.village.city?.constructions?.find(c => c && c.slot === this.slotId) || null;
        }
      } catch (error) {
        console.error('Error finding field or building:', error);
      }
      
      return null;
    },

    isMobile() {
      return this.windowWidth < 600
    },
    
    title() {
      if (this.isEmpty) {
        return this.type === 'resource' ? 'Empty Resource Field' : 'Empty Building Slot'
      }
      
      if (this.type === 'resource' && this.fieldOrBuilding) {
        const resourceInfo = this.getResourceInfo(this.fieldOrBuilding.type);
        return resourceInfo ? `${resourceInfo.name} Field` : `${this.fieldOrBuilding.type.charAt(0).toUpperCase() + this.fieldOrBuilding.type.slice(1)} Field`;
      } else if (this.fieldOrBuilding) {
        const buildingInfo = this.getBuildingInfo(this.fieldOrBuilding.type);
        return buildingInfo ? buildingInfo.name : this.fieldOrBuilding.type.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
      }
      
      return '';
    },
    
    getTypeColor() {
      if (this.isEmpty) {
        return UI_COLORS.DIALOG.EMPTY_ICON;
      }
      
      if (!this.fieldOrBuilding) return UI_COLORS.DIALOG.EMPTY_ICON;
      
      if (this.type === 'resource') {
        return this.resourceColor(this.fieldOrBuilding.type);
      } else {
        return this.buildingColor(this.fieldOrBuilding.type);
      }
    },
    
    getTypeIcon() {
      if (this.isEmpty) {
        return 'mdi-help-circle';
      }
      
      if (!this.fieldOrBuilding) return 'mdi-help-circle';
      
      if (this.type === 'resource') {
        return this.resourceIcon(this.fieldOrBuilding.type);
      } else {
        return this.buildingIcon(this.fieldOrBuilding.type);
      }
    },

    getProductionIcon() {
      return this.type === 'resource' ? 'mdi-factory' : 'mdi-percent';
    },

    getProductionTitle() {
      return this.type === 'resource' ? 'Production Rate' : 'Production Bonus';
    },

    description() {
      if (this.isEmpty) {
        return this.type === 'resource' 
          ? 'An empty resource field. Build a resource production building here to gather resources.'
          : 'An empty building slot. Construct a building here to improve your village.'
      }

      if (!this.fieldOrBuilding) return '';

      if (this.type === 'resource') {
        const resourceInfo = this.getResourceInfo(this.fieldOrBuilding.type);
        return resourceInfo ? resourceInfo.description : 'Resource production field.';
      } else {
        const buildingInfo = this.getBuildingInfo(this.fieldOrBuilding.type);
        return buildingInfo ? buildingInfo.description : 'Building description.';
      }
    },

    imageUrl() {
      if (!this.fieldOrBuilding && !this.isEmpty) return '';
      
      if (this.type === 'resource' && this.fieldOrBuilding) {
        return getResourceFieldImageRef(this.fieldOrBuilding.type);
      } else if (this.type === 'building' && this.fieldOrBuilding) {
        return getBuildingImageRef(this.fieldOrBuilding.type);
      } else {
        // Default for empty state or fallback
        return getBuildingImageRef('');
      }
    },

    hasAnyProductionBonus() {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.production_bonus) {
        return false;
      }
      
      return Object.values(this.fieldOrBuilding.production_bonus).some(bonus => bonus > 0);
    },

    canUpgrade() {
      if (!this.fieldOrBuilding) return false;
      return !this.isEmpty && this.fieldOrBuilding.level < 10 && !this.isBeingUpgraded;
    },

    isBeingUpgraded() {
      if (!this.village || !this.village.construction_tasks) {
        return false;
      }

      return this.village.construction_tasks.some(task => {
        // Check if this is a task for the current building/field
        return task.slot === this.slotId && 
               ((this.type === 'resource' && (task.task_type === 'upgrade_field' || task.task_type === 'create_field')) ||
                (this.type === 'building' && (task.task_type === 'upgrade_building' || task.task_type === 'create_building')));
      });
    },

    getUpgradeTask() {
      if (!this.village || !this.village.construction_tasks) {
        return null;
      }

      return this.village.construction_tasks.find(task => {
        return task.slot === this.slotId && 
               ((this.type === 'resource' && (task.task_type === 'upgrade_field' || task.task_type === 'create_field')) ||
                (this.type === 'building' && (task.task_type === 'upgrade_building' || task.task_type === 'create_building')));
      });
    },

    hasNextLevelBonuses() {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.next_level_bonus) {
        return false;
      }
      
      return Object.values(this.fieldOrBuilding.next_level_bonus).some(bonus => bonus > 0);
    },

    hasSufficientResources() {
      // If no upgrade costs are available, or no resources data, we can't determine if sufficient
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.upgrade_cost || !this.village || !this.village.resources) {
        return false;
      }
      
      try {
        for (const [resource, cost] of Object.entries(this.fieldOrBuilding.upgrade_cost)) {
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
    closeDialog() {
      this.$emit('update:show', false)
    },

    handleUpgrade() {
      this.$emit('upgrade', {
        type: this.type,
        slot: this.slotId,
        currentLevel: this.fieldOrBuilding?.level || 0
      });
      this.closeDialog();
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

    formatPercent(value) {
      return (value * 100).toFixed(0) + '%';
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

    formatTimeLeft(timestamp) {
      if (!timestamp) return 'unknown';
      
      const now = new Date().getTime();
      const completion = new Date(timestamp).getTime();
      const diff = Math.max(0, completion - now);
      
      // Convert milliseconds to minutes
      const totalMinutes = Math.ceil(diff / (1000 * 60));
      return this.formatTime(totalMinutes);
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
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.upgrade_cost) {
        return false;
      }
      
      return resourceType in this.fieldOrBuilding.upgrade_cost && this.fieldOrBuilding.upgrade_cost[resourceType] > 0;
    },
    
    getCost(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.upgrade_cost) {
        return 0;
      }
      
      return this.fieldOrBuilding.upgrade_cost[resourceType] || 0;
    },

    getCurrentProductionRate(field, resourceType) {
      if (!field || !field.current_production_rate || !field.current_production_rate[resourceType]) return 0;
      return field.current_production_rate[resourceType];
    },

    getNextLevelProductionRate(field, resourceType) {
      if (!field || !field.next_level_production_rate || !field.next_level_production_rate[resourceType]) return 0;
      return field.next_level_production_rate[resourceType];
    },

    // Wrapper methods for imported functions
    resourceColor(resourceType) {
      return getResourceColor(resourceType);
    },
    
    resourceIcon(resourceType) {
      return getResourceIcon(resourceType);
    },
    
    buildingColor(buildingType) {
      return getBuildingColor(buildingType);
    },
    
    buildingIcon(buildingType) {
      return getBuildingIcon(buildingType);
    },
    
    getResourceInfo(resourceType) {
      return getResourceInfo(resourceType);
    },
    
    getBuildingInfo(buildingType) {
      return getBuildingInfo(buildingType);
    },

    getResourceFieldImageRef(resourceType) {
      return getResourceFieldImageRef(resourceType);
    },
    
    getBuildingImageRef(buildingType) {
      return getBuildingImageRef(buildingType);
    },

    hasProduction(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.current_production_rate) {
        return false;
      }
      // First check if the property exists at all
      if (!(resourceType in this.fieldOrBuilding.current_production_rate)) {
        return false;
      }
      // Then check if it has a value greater than 0
      const value = this.fieldOrBuilding.current_production_rate[resourceType];
      return value && parseFloat(value) > 0;
    },

    hasNextLevelProduction(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.next_level_production_rate) {
        return false;
      }
      // First check if the property exists at all
      if (!(resourceType in this.fieldOrBuilding.next_level_production_rate)) {
        return false;
      }
      // Then check if it has a value greater than 0
      const value = this.fieldOrBuilding.next_level_production_rate[resourceType];
      return value && parseFloat(value) > 0;
    },

    hasBonus(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.production_bonus) {
        return false;
      }
      // First check if the property exists at all
      if (!(resourceType in this.fieldOrBuilding.production_bonus)) {
        return false;
      }
      // Then check if it has a value greater than 0
      const value = this.fieldOrBuilding.production_bonus[resourceType];
      return value && parseFloat(value) > 0;
    },

    getCurrentBonus(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.production_bonus) {
        return 0;
      }
      return this.fieldOrBuilding.production_bonus[resourceType] || 0;
    },

    getNextLevelBonus(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.next_level_bonus) {
        return 0;
      }
      return this.fieldOrBuilding.next_level_bonus[resourceType] || 0;
    },
    
    hasNextLevelBonus(resourceType) {
      if (!this.fieldOrBuilding || !this.fieldOrBuilding.next_level_bonus) {
        return false;
      }
      // First check if the property exists at all
      if (!(resourceType in this.fieldOrBuilding.next_level_bonus)) {
        return false;
      }
      // Then check if it has a value greater than 0
      const value = this.fieldOrBuilding.next_level_bonus[resourceType];
      return value && parseFloat(value) > 0;
    }
  },

  mounted() {
    window.addEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  },

  beforeDestroy() {
    window.removeEventListener('resize', () => {
      this.windowWidth = window.innerWidth
    })
  }
}
</script>

<style scoped>
.selection-dialog {
  border-radius: 12px;
}

.image-container {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 24px;
  text-align: center;
}

.badges-overlay {
  position: absolute;
  bottom: 8px;
  left: 8px;
  display: flex;
  gap: 8px;
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

.slot-badge {
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
}

.level-badge {
  background-color: rgba(33, 150, 243, 0.8);
  color: white;
}

.current-level {
  background-color: rgba(33, 150, 243, 0.15);
  color: #1976d2;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
}

.description {
  line-height: 1.5;
  font-size: 14px;
  margin-bottom: 12px;
}

/* Game Panels */
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

.align-items-center {
  align-items: center;
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

.upgrade-label {
  color: #4caf50;
}

.current-production, .next-production {
  width: 100%;
  padding: 3px 6px;
  border-radius: 4px;
}

.next-production {
  background-color: rgba(76, 175, 80, 0.05);
}

.mini-value {
  font-weight: 600;
  font-size: 14px;
}

/* Mini Bonus List */
.mini-bonus-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mini-bonus-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 0;
}

.mini-resource {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mini-empty {
  color: #9e9e9e;
  font-style: italic;
  font-size: 12px;
  text-align: center;
  padding: 4px 0;
}

/* Mini Progress */
.mini-progress {
  display: flex;
  align-items: center;
  background-color: rgba(33, 150, 243, 0.08);
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
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

.level-indicator {
  font-weight: 600;
  font-size: 12px;
  color: #757575;
}

/* Mini Empty Slot */
.mini-empty-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  gap: 8px;
  color: #757575;
}

/* DEBUG INFO - Hidden
.debug-info {
  margin-top: 16px;
  padding: 8px;
  border: 1px dashed red;
  font-size: 11px;
}
*/

@media (max-width: 600px) {
  .selection-dialog {
    border-radius: 0;
  }
  
  .panel-content {
    padding: 8px;
  }
}

/* Add new CSS for the next level rate */
.next-level-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-top: 1px;
}

.next-level-rate {
  font-size: 11px;
  color: #4caf50;
  font-weight: 500;
  line-height: 1;
}

.next-level-label {
  font-size: 8px;
  color: #757575;
  font-style: italic;
  line-height: 1;
  margin-top: -1px;
}

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