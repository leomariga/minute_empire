<template>
  <BaseSelectionDialog
    :show="show"
    @update:show="$emit('update:show', $event)"
    @close="closeDialog"
    :slot-id="slotId"
    :title="getTitle"
    :description="getDescription"
    :type-color="getTypeColor"
    :type-icon="getTypeIcon"
    :image-url="getImageUrl"
  >
    <!-- Header actions slot -->
    <template v-slot:header-actions>
      <div v-if="!isEmpty && fieldOrBuilding" class="current-level">
        Level {{ fieldOrBuilding?.level || 0 }}
      </div>
    </template>
    
    <!-- Main content -->
    <template v-slot:content>
      <!-- Empty slot - show creation panel or creating state -->
      <div v-if="isEmpty && isOwned">
        <CreationPanel
          :type="type"
          :slot-id="slotId"
          :available-options="getAvailableOptions"
          :village="village"
          :is-being-created="isBeingCreated"
          :creation-type-name="getCreationTypeName"
          :creation-type-color="getCreationTypeColor"
          :creation-type-icon="getCreationTypeIcon"
          :creation-time-remaining="getCreationTimeRemaining"
          @create="handleCreate"
        />
      </div>
      
      <!-- Resource field - show production info -->
      <ResourceProductionPanel
        v-else-if="type === 'resource' && fieldOrBuilding"
        :field="fieldOrBuilding"
        :is-being-upgraded="isBeingUpgraded"
      />
      
      <!-- Building - show bonus info -->
      <BuildingBonusPanel
        v-else-if="type === 'building' && fieldOrBuilding && !isMilitaryBuilding"
        :building="fieldOrBuilding"
        :is-being-upgraded="isBeingUpgraded"
      />
      
      <!-- Military Building - show troop training panel -->
      <TrainTroopPanel
        v-else-if="type === 'building' && fieldOrBuilding && isMilitaryBuilding"
        :building="fieldOrBuilding"
        :village="village"
        :is-training-in-progress="isTrainingInProgress"
        :training-type-name="getTrainingTypeName"
        :training-type-color="getTrainingTypeColor"
        :training-type-icon="getTrainingTypeIcon"
        :training-time-remaining="getTrainingTimeRemaining"
        @train="handleTrain"
      />
    </template>
    
    <!-- Actions slot - upgrade panel for existing buildings/fields -->
    <template v-slot:actions>
      <div v-if="!isEmpty && fieldOrBuilding" class="action-container">
        <div class="upgrade-panel-wrapper">
          <UpgradePanel
            :item="fieldOrBuilding"
            :is-being-upgraded="isBeingUpgraded"
            :village="village"
            @upgrade="handleUpgrade"
            @destroy="handleDestroy"
          />
        </div>
      </div>
    </template>
  </BaseSelectionDialog>
</template>

<script>
import { getResourceColor, getResourceIcon, getBuildingColor, getBuildingIcon, getResourceInfo, getBuildingInfo, getResourceFieldInfo, UI_COLORS, getResourceFieldImageRef, getBuildingImageRef, RESOURCE_FIELDS, BUILDINGS, getTroopTypeName, getTroopColor, getTroopIcon, MILITARY_BUILDINGS } from '@/constants/gameElements';
import BaseSelectionDialog from './BaseSelectionDialog.vue';
import ResourceProductionPanel from './ResourceProductionPanel.vue';
import BuildingBonusPanel from './BuildingBonusPanel.vue';
import UpgradePanel from './UpgradePanel.vue';
import CreationPanel from './CreationPanel.vue';
import TrainTroopPanel from './TrainTroopPanel.vue';
import apiService from '@/services/apiService';

export default {
  name: 'MapSelectionDialog',
  
  components: {
    BaseSelectionDialog,
    ResourceProductionPanel,
    BuildingBonusPanel,
    UpgradePanel,
    CreationPanel,
    TrainTroopPanel
  },
  
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
    },
    isOwned: {
      type: Boolean,
      default: true
    },
    dialogType: {
      type: String,
      default: ''
    },
    buildingOptions: {
      type: Array,
      default: () => []
    },
    mapData: {
      type: Object,
      default: null
    }
  },
  
  data() {
    return {
      // removed showConfirmDialog
    };
  },
  
  mounted() {
    console.log('MapSelectionDialog mounted, village:', this.village?.id);
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
    
    getTitle() {
      if (this.isEmpty) {
        // If the slot is being created, show a different title
        if (this.isBeingCreated) {
          return `Creating ${this.getCreationTypeName}`;
        }
        return this.type === 'resource' ? 'Empty Resource Field' : 'Empty Building Slot';
      }
      
      if (this.type === 'resource' && this.fieldOrBuilding) {
        const fieldInfo = getResourceFieldInfo(this.fieldOrBuilding.type);
        return fieldInfo ? fieldInfo.name : `${this.fieldOrBuilding.type.charAt(0).toUpperCase() + this.fieldOrBuilding.type.slice(1)} Field`;
      } else if (this.fieldOrBuilding) {
        const buildingInfo = getBuildingInfo(this.fieldOrBuilding.type);
        return buildingInfo ? buildingInfo.name : this.fieldOrBuilding.type.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
      }
      
      return '';
    },
    
    getDescription() {
      if (this.isEmpty) {
        // If the slot is being created, show construction message
        if (this.isBeingCreated) {
          return `A ${this.getCreationTypeName} is currently being constructed in this slot.`;
        }
        return this.type === 'resource' 
          ? 'An empty resource field. Build a resource production building here to gather resources.'
          : 'An empty building slot. Construct a building here to improve your village.';
      }

      if (!this.fieldOrBuilding) return '';

      if (this.type === 'resource') {
        const fieldInfo = getResourceFieldInfo(this.fieldOrBuilding.type);
        return fieldInfo ? fieldInfo.description : 'Resource production field.';
      } else {
        const buildingInfo = getBuildingInfo(this.fieldOrBuilding.type);
        return buildingInfo ? buildingInfo.description : 'Building description.';
      }
    },
    
    getTypeColor() {
      if (this.isEmpty) {
        return UI_COLORS.DIALOG.EMPTY_ICON;
      }
      
      if (!this.fieldOrBuilding) return UI_COLORS.DIALOG.EMPTY_ICON;
      
      if (this.type === 'resource') {
        return getResourceColor(this.fieldOrBuilding.type);
      } else {
        return getBuildingColor(this.fieldOrBuilding.type);
      }
    },
    
    getTypeIcon() {
      if (this.isEmpty) {
        return 'mdi-help-circle';
      }
      
      if (!this.fieldOrBuilding) return 'mdi-help-circle';
      
      if (this.type === 'resource') {
        return getResourceIcon(this.fieldOrBuilding.type);
      } else {
        return getBuildingIcon(this.fieldOrBuilding.type);
      }
    },
    
    getImageUrl() {
      if (!this.fieldOrBuilding && !this.isEmpty) return '';
      
      if (this.type === 'resource' && this.fieldOrBuilding) {
        return getResourceFieldImageRef(this.fieldOrBuilding.type);
      } else if (this.type === 'building' && this.fieldOrBuilding) {
        return getBuildingImageRef(this.fieldOrBuilding.type);
      } else {
        // Default for empty state or fallback
        return this.type === 'resource' ? 
          getResourceFieldImageRef('empty') : 
          getBuildingImageRef('empty');
      }
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
    
    getAvailableOptions() {
      if (!this.isEmpty) return [];
      
      // Check if base costs are available from the API
      const hasBaseCosts = this.village && this.village.base_costs;
      const hasCreationTimes = this.village && this.village.base_creation_times;

      if (this.type === 'resource') {
        // Get all resource field types from the constants
        const resourceFieldTypes = Object.keys(RESOURCE_FIELDS).map(key => RESOURCE_FIELDS[key].id);
        
        // Dynamically create options based on the available field types
        return resourceFieldTypes.map(fieldType => {
          const fieldInfo = getResourceFieldInfo(fieldType);
          
          return {
            type: fieldType,
            name: fieldInfo ? fieldInfo.name : fieldType,
            description: fieldInfo ? fieldInfo.description : '',
            // Use API data if available, otherwise default to empty cost object
            cost: hasBaseCosts && this.village.base_costs.fields[fieldType] ? 
              { ...this.village.base_costs.fields[fieldType] } : 
              { wood: 0, food: 0, stone: 0, iron: 0 },
            creation_time: hasCreationTimes ? this.village.base_creation_times.fields[fieldType] : 0
          };
        });
      } else {
        // For buildings, use the API data to determine which buildings are available
        let availableBuildingTypes = [];
        
        if (hasBaseCosts) {
          // Get building types from the API data
          availableBuildingTypes = Object.keys(this.village.base_costs.buildings);
        } else {
          // Fallback to all building types from constants if API data is not available
          availableBuildingTypes = Object.keys(BUILDINGS).map(key => BUILDINGS[key].id);
        }
        
        // Dynamically create options based on the available building types
        return availableBuildingTypes.map(buildingType => {
          const buildingInfo = getBuildingInfo(buildingType);
          
          return {
            type: buildingType,
            name: buildingInfo ? buildingInfo.name : buildingType.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
            description: buildingInfo ? buildingInfo.description : '',
            // Use API data if available, otherwise default to empty cost object
            cost: hasBaseCosts && this.village.base_costs.buildings[buildingType] ? 
              { ...this.village.base_costs.buildings[buildingType] } : 
              { wood: 0, food: 0, stone: 0, iron: 0 },
            creation_time: hasCreationTimes ? this.village.base_creation_times.buildings[buildingType] : 0
          };
        });
      }
    },
    
    isBeingCreated() {
      if (!this.isEmpty || !this.village || !this.village.construction_tasks) return false;
      
      return this.village.construction_tasks.some(task => {
        return task.slot === this.slotId && 
               ((this.type === 'resource' && task.task_type === 'create_field') ||
                (this.type === 'building' && task.task_type === 'create_building'));
      });
    },
    
    getCreationTypeName() {
      if (!this.village || !this.village.construction_tasks) {
        return this.type === 'resource' ? 'Resource Field' : 'Building';
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.slot === this.slotId && 
        ((this.type === 'resource' && task.task_type === 'create_field') ||
         (this.type === 'building' && task.task_type === 'create_building'))
      );
      
      if (!task) {
        return this.type === 'resource' ? 'Resource Field' : 'Building';
      }
      
      console.log('Construction task data:', JSON.stringify(task));
      
      if (this.type === 'resource') {
        // Use target_type from API (e.g., "wood", "food", etc.)
        const fieldType = task.target_type || task.field_type || task.type || 'resource';
        const fieldInfo = getResourceFieldInfo(fieldType);
        return fieldInfo ? fieldInfo.name : fieldType.charAt(0).toUpperCase() + fieldType.slice(1) + ' Field';
      } else {
        // Use target_type from API (e.g., "granary", "warehouse", etc.)
        const buildingType = task.target_type || task.building_type || task.type || 'building';
        const buildingInfo = getBuildingInfo(buildingType);
        return buildingInfo ? buildingInfo.name : buildingType.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
      }
    },
    
    getCreationTimeRemaining() {
      if (!this.isEmpty || !this.village || !this.village.construction_tasks || !this.mapData) return '';
      
      const task = this.village.construction_tasks.find(task => 
        task.slot === this.slotId && 
        ((this.type === 'resource' && task.task_type === 'create_field') ||
         (this.type === 'building' && task.task_type === 'create_building'))
      );
      
      if (!task || !task.completion_time) return '';
      
      try {
        console.log('Task completion time:', task.completion_time);
        console.log('Server time:', this.mapData.server_time);
        
        // Handle ISO 8601 format dates (2025-03-31T20:47:05.883000) or timestamps
        let completionTime, serverTime;
        
        // Check if the completion time is an ISO date string
        if (typeof task.completion_time === 'string' && task.completion_time.includes('T')) {
          completionTime = new Date(task.completion_time).getTime() / 1000;
        } else {
          // Fallback to parsing as a timestamp
          completionTime = parseInt(task.completion_time) || 0;
        }
        
        // Check if server time is an ISO date string
        if (typeof this.mapData.server_time === 'string' && this.mapData.server_time.includes('T')) {
          serverTime = new Date(this.mapData.server_time).getTime() / 1000;
        } else {
          // Fallback to parsing as a timestamp
          serverTime = parseInt(this.mapData.server_time) || 0;
        }
        
        console.log('Parsed completion time:', completionTime);
        console.log('Parsed server time:', serverTime);
        
        if (!serverTime || !completionTime) {
          return 'Time remaining unavailable';
        }
        
        // Calculate time difference
        const diffInSeconds = Math.max(0, completionTime - serverTime);
        if (diffInSeconds <= 0) return 'Completing...';
        
        // Format time remaining
        if (diffInSeconds >= 3600) {
          const hours = Math.floor(diffInSeconds / 3600);
          const minutes = Math.floor((diffInSeconds % 3600) / 60);
          return `${hours}h ${minutes}m remaining`;
        } else if (diffInSeconds >= 60) {
          const minutes = Math.floor(diffInSeconds / 60);
          const seconds = Math.floor(diffInSeconds % 60);
          return `${minutes}m ${seconds}s remaining`;
        } else {
          return `${Math.floor(diffInSeconds)}s remaining`;
        }
      } catch (error) {
        console.error('Error calculating remaining time:', error, task);
        return 'Time calculation error';
      }
    },
    
    getCreationTypeColor() {
      if (!this.village || !this.village.construction_tasks) {
        return UI_COLORS.DIALOG.EMPTY_ICON;
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.slot === this.slotId && 
        ((this.type === 'resource' && task.task_type === 'create_field') ||
         (this.type === 'building' && task.task_type === 'create_building'))
      );
      
      if (!task) {
        return UI_COLORS.DIALOG.EMPTY_ICON;
      }
      
      if (this.type === 'resource') {
        // Use target_type from API
        const fieldType = task.target_type || task.field_type || task.type || 'resource';
        return getResourceColor(fieldType);
      } else {
        // Use target_type from API
        const buildingType = task.target_type || task.building_type || task.type || 'building';
        return getBuildingColor(buildingType);
      }
    },
    
    getCreationTypeIcon() {
      if (!this.village || !this.village.construction_tasks) {
        return this.type === 'resource' ? 'mdi-tree' : 'mdi-home';
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.slot === this.slotId && 
        ((this.type === 'resource' && task.task_type === 'create_field') ||
         (this.type === 'building' && task.task_type === 'create_building'))
      );
      
      if (!task) {
        return this.type === 'resource' ? 'mdi-tree' : 'mdi-home';
      }
      
      if (this.type === 'resource') {
        // Use target_type from API
        const fieldType = task.target_type || task.field_type || task.type || 'resource';
        return getResourceIcon(fieldType);
      } else {
        // Use target_type from API
        const buildingType = task.target_type || task.building_type || task.type || 'building';
        return getBuildingIcon(buildingType);
      }
    },
    
    isMilitaryBuilding() {
      if (!this.fieldOrBuilding) return false;
      
      // Get the building info
      const buildingInfo = getBuildingInfo(this.fieldOrBuilding.type);
      
      // Check if this building has troop_training in its buildingTypes
      return buildingInfo && 
        buildingInfo.buildingTypes && 
        buildingInfo.buildingTypes.includes('troop_training');
    },
    
    isTrainingInProgress() {
      if (!this.village || !this.village.construction_tasks) {
        return false;
      }

      return this.village.construction_tasks.some(task => {
        // Check if this is a troop training task for the current building
        return task.task_type === 'train_troops' && 
               task.building_slot === this.fieldOrBuilding?.slot;
      });
    },
    
    getTrainingTypeName() {
      if (!this.village || !this.village.construction_tasks || !this.fieldOrBuilding) {
        return 'Troops';
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.task_type === 'train_troops' && 
        task.building_slot === this.fieldOrBuilding.slot
      );
      
      if (!task) return 'Troops';
      
      // Get troop type name based on the task
      const troopType = task.troop_type || '';
      return getTroopTypeName(troopType);
    },
    
    getTrainingTypeColor() {
      if (!this.village || !this.village.construction_tasks || !this.fieldOrBuilding) {
        return '#607D8B';
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.task_type === 'train_troops' && 
        task.building_slot === this.fieldOrBuilding.slot
      );
      
      if (!task) return '#607D8B';
      
      // Get color based on troop type
      const troopType = task.troop_type || '';
      return getTroopColor(troopType);
    },
    
    getTrainingTypeIcon() {
      if (!this.village || !this.village.construction_tasks || !this.fieldOrBuilding) {
        return 'mdi-sword';
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.task_type === 'train_troops' && 
        task.building_slot === this.fieldOrBuilding.slot
      );
      
      if (!task) return 'mdi-sword';
      
      // Get icon based on troop type
      const troopType = task.troop_type || '';
      return getTroopIcon(troopType);
    },
    
    getTrainingTimeRemaining() {
      if (!this.village || !this.village.construction_tasks || !this.fieldOrBuilding || !this.mapData) {
        return '';
      }
      
      const task = this.village.construction_tasks.find(task => 
        task.task_type === 'train_troops' && 
        task.building_slot === this.fieldOrBuilding.slot
      );
      
      if (!task || !task.completion_time) return '';
      
      try {
        // Handle ISO 8601 format dates (2025-03-31T20:47:05.883000) or timestamps
        let completionTime, serverTime;
        
        // Check if the completion time is an ISO date string
        if (typeof task.completion_time === 'string' && task.completion_time.includes('T')) {
          completionTime = new Date(task.completion_time).getTime() / 1000;
        } else {
          // Fallback to parsing as a timestamp
          completionTime = parseInt(task.completion_time) || 0;
        }
        
        // Check if server time is an ISO date string
        if (typeof this.mapData.server_time === 'string' && this.mapData.server_time.includes('T')) {
          serverTime = new Date(this.mapData.server_time).getTime() / 1000;
        } else {
          // Fallback to parsing as a timestamp
          serverTime = parseInt(this.mapData.server_time) || 0;
        }
        
        if (!serverTime || !completionTime) {
          return 'Time remaining unavailable';
        }
        
        // Calculate time difference
        const diffInSeconds = Math.max(0, completionTime - serverTime);
        if (diffInSeconds <= 0) return 'Completing...';
        
        // Format time remaining
        if (diffInSeconds >= 3600) {
          const hours = Math.floor(diffInSeconds / 3600);
          const minutes = Math.floor((diffInSeconds % 3600) / 60);
          return `${hours}h ${minutes}m remaining`;
        } else if (diffInSeconds >= 60) {
          const minutes = Math.floor(diffInSeconds / 60);
          const seconds = Math.floor(diffInSeconds % 60);
          return `${minutes}m ${seconds}s remaining`;
        } else {
          return `${Math.floor(diffInSeconds)}s remaining`;
        }
      } catch (error) {
        console.error('Error calculating remaining time:', error, task);
        return 'Time calculation error';
      }
    }
  },
  
  methods: {
    closeDialog() {
      this.$emit('update:show', false);
    },
    
    handleUpgrade(data) {
      // Add the dialog's type as item_category - this is already 'resource' or 'building'
      this.$emit('upgrade', {
        ...data,
        item_category: this.type
      });
      this.closeDialog();
    },
    
    handleCreate(data) {
      // Pass complete data through to parent
      this.$emit('create', data);
      this.closeDialog();
    },
    
    handleTrain(data) {
      // Pass complete data through to parent
      this.$emit('train', data);
      this.closeDialog();
    },
    
    handleDestroy(data) {
      // Pass complete data through to parent as a construction action
      this.$emit('destroy', {
        ...data,
        item_category: this.type
      });
      this.closeDialog();
    }
  }
}
</script>

<style scoped>
.current-level {
  background-color: rgba(33, 150, 243, 0.15);
  color: #1976d2;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
}

.action-container {
  display: flex;
  width: 100%;
}

.upgrade-panel-wrapper {
  flex-grow: 1;
  width: 100%;
}

/* Remove all the dialog-related styles and destroy button styles */
.mr-1 {
  margin-right: 4px;
}

.mr-2 {
  margin-right: 8px;
}

.mt-2 {
  margin-top: 8px;
}
</style> 