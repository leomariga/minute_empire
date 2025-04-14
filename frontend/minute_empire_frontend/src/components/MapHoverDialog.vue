<template>
  <v-card
    v-if="show"
    class="map-hover-dialog"
    :style="dialogStyle"
    elevation="4"
  >
    <v-card-text class="pa-2">
      <!-- Village Info Header -->
      <div v-if="type === 'village'" class="village-header">
        <!-- Village Name -->
        <div class="village-name">
          {{ data.name }}
        </div>
        <!-- Color Accent -->
        <div class="color-accent" :style="accentStyle"></div>
      </div>

      <!-- Troop Info Header -->
      <div v-else-if="type === 'troop'" class="d-flex align-center mb-2">
        <v-icon
          :color="getTroopColor"
          class="mr-2"
          size="28"
        >
          {{ getTroopIcon }}
        </v-icon>
        <span class="text-subtitle-1 font-weight-bold">
          {{ getTroopTitle }}
        </span>
        <v-chip
          v-if="data.groupCount > 1"
          size="small"
          class="ml-2"
          color="primary"
          label
        >
          {{ data.groupCount }}
        </v-chip>
      </div>

      <!-- Resource/Building Info Header -->
      <div v-else class="d-flex align-center mb-2">
        <v-icon
          :color="getTypeColor"
          class="mr-2"
          size="20"
        >
          {{ getTypeIcon }}
        </v-icon>
        <span class="text-subtitle-2 font-weight-bold">
          {{ title }}
        </span>
      </div>

      <!-- Content -->
      <div class="d-flex flex-column">
        <!-- Village Info Content -->
        <template v-if="type === 'village'">
          <div class="family-info">
            <div class="family-name">
              <v-icon size="16" color="grey" class="mr-1">mdi-account-group</v-icon>
              {{ data.user_info.family_name }}
            </div>
            <div class="coordinates">
              <v-icon size="16" color="grey" class="mr-1">mdi-map-marker</v-icon>
              X: {{ data.location.x }}, Y: {{ data.location.y }}
            </div>
          </div>
        </template>

        <!-- Troop Info Content -->
        <template v-else-if="type === 'troop'">
          <div class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Quantity:</span>
            <span class="text-caption font-weight-medium">{{ data.quantity }}</span>
          </div>
          
          <div class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Home:</span>
            <span class="text-caption font-weight-medium">{{ data.homeVillageName }}</span>
          </div>
          
          <div class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Owner:</span>
            <span class="text-caption font-weight-medium">{{ data.ownerFamily }}</span>
          </div>
          
          <div v-if="data.totalTroops" class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Total troops:</span>
            <span class="text-caption font-weight-medium">{{ data.totalTroops }}</span>
          </div>
          
          <div v-if="data.mode" class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Mode:</span>
            <span class="text-caption font-weight-medium">{{ formatTroopMode(data.mode) }}</span>
          </div>
          
          <div v-if="data.backpack && hasResources(data.backpack)" class="d-flex flex-column mt-1">
            <span class="text-caption text-grey mb-1">Carrying:</span>
            <div class="d-flex flex-wrap">
              <div v-for="(amount, resource) in data.backpack" :key="resource" class="mr-2 mb-1" v-if="amount > 0">
                <v-chip size="x-small" :color="getResourceChipColor(resource)">
                  {{ resource }}: {{ amount }}
                </v-chip>
              </div>
            </div>
          </div>
        </template>

        <!-- Resource/Building Info Content -->
        <template v-else>
          <div class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Slot:</span>
            <span class="text-caption font-weight-medium">{{ data.slot }}</span>
          </div>
          
          <div v-if="!data.isEmpty" class="d-flex justify-space-between align-center mb-1">
            <span class="text-caption text-grey">Level:</span>
            <span class="text-caption font-weight-medium">{{ data.level }}</span>
          </div>
          
          <div v-else class="d-flex align-center">
            <v-icon size="16" color="grey" class="mr-1">mdi-information</v-icon>
            <span class="text-caption text-grey">Empty slot</span>
          </div>
        </template>
        
        <!-- Dynamic content slots for future expansion -->
        <slot name="additional-info"></slot>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { getResourceColor, getResourceIcon, getBuildingColor, getBuildingIcon, getTroopIcon, getTroopInfo, UI_COLORS } from '@/constants/gameElements';

// Troop Mode Mapping
const TROOP_MODES = {
  IDLE: 'Idle',
  DEFENDING: 'Defending',
  TRAVELING: 'Traveling',
  ATTACKING: 'Attacking',
  RETURNING: 'Returning',
  SCOUTING: 'Scouting',
  GATHERING: 'Gathering',
  SETTLING: 'Settling'
};

export default {
  name: 'MapHoverDialog',
  
  props: {
    show: {
      type: Boolean,
      required: true
    },
    position: {
      type: Object,
      required: true
    },
    data: {
      type: Object,
      required: true
    },
    type: {
      type: String,
      required: true,
      validator: value => ['resource', 'building', 'village', 'troop'].includes(value)
    }
  },
  
  computed: {
    dialogStyle() {
      return {
        position: 'absolute',
        left: `${this.position.x}px`,
        top: `${this.position.y}px`,
        zIndex: 1000,
        maxWidth: '250px',
        backgroundColor: UI_COLORS.BACKGROUND.PRIMARY,
        backdropFilter: 'blur(4px)',
        transform: 'translate3d(0, 0, 0)',
        willChange: 'transform'
      }
    },
    
    title() {
      if (this.type === 'village') return '';
      
      if (this.data.isEmpty) {
        return this.type === 'resource' ? 'Empty Resource Field' : 'Empty Building Slot'
      }
      
      if (this.type === 'resource') {
        return this.data.type.charAt(0).toUpperCase() + this.data.type.slice(1) + ' Field'
      } else {
        return this.data.type.split('_').map(word => 
          word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ')
      }
    },
    
    getTypeColor() {
      if (this.data.isEmpty) {
        return UI_COLORS.DIALOG.EMPTY_ICON;
      }
      
      if (this.type === 'resource') {
        return getResourceColor(this.data.type);
      } else {
        return getBuildingColor(this.data.type);
      }
    },
    
    getTypeIcon() {
      if (this.data.isEmpty) {
        return 'mdi-help-circle';
      }
      
      if (this.type === 'resource') {
        return getResourceIcon(this.data.type);
      } else {
        return getBuildingIcon(this.data.type);
      }
    },
    
    // Troop-specific computed properties
    getTroopTitle() {
      if (!this.data.type) return 'Unknown Troop';
      
      // Try to get the name from our troop info definitions
      const troopInfo = getTroopInfo(this.data.type);
      return troopInfo ? troopInfo.name : this.data.type.charAt(0).toUpperCase() + this.data.type.slice(1).toLowerCase();
    },
    
    getTroopIcon() {
      if (!this.data.type) return 'mdi-help-circle';
      return getTroopIcon(this.data.type);
    },
    
    getTroopColor() {
      return this.data.isOwned ? 'rgba(0, 0, 0, 0.8)' : 'rgba(244, 67, 54, 0.8)';
    },

    accentStyle() {
      if (this.type === 'village' && this.data.user_info?.color) {
        return {
          backgroundColor: this.data.user_info.color
        }
      }
      return {}
    }
  },

  methods: {
    formatTroopMode(mode) {
      if (!mode) return 'Unknown';
      const upperMode = mode.toUpperCase();
      return TROOP_MODES[upperMode] || mode;
    },
    
    hasResources(backpack) {
      if (!backpack) return false;
      return Object.values(backpack).some(amount => amount > 0);
    },
    
    getResourceChipColor(resource) {
      switch (resource.toLowerCase()) {
        case 'wood': return 'green';
        case 'food': return 'amber';
        case 'stone': return 'grey';
        case 'iron': return 'blue-grey';
        default: return 'primary';
      }
    }
  },

  beforeUpdate() {
    if (!this.show) {
      return false;
    }
    return true;
  }
}
</script>

<style scoped>
.map-hover-dialog {
  border-radius: 4px;
  transition: transform 0.2s ease-out;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  contain: content;
  backface-visibility: hidden;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.map-hover-dialog:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.village-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  position: relative;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.color-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
}

.village-name {
  font-size: 1.1em;
  font-weight: 600;
  color: #2c3e50;
  letter-spacing: 0.5px;
}

.family-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
  padding: 0 12px;
}

.family-name {
  display: flex;
  align-items: center;
  font-size: 0.9em;
  color: #34495e;
  font-weight: 500;
}

.family-name .v-icon {
  color: var(--player-color);
}

.coordinates {
  display: flex;
  align-items: center;
  font-size: 0.9em;
  color: #7f8c8d;
}

.coordinates .v-icon {
  color: var(--player-color);
}
</style> 