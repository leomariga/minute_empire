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
import { getResourceColor, getResourceIcon, getBuildingColor, getBuildingIcon, UI_COLORS } from '@/constants/gameElements';

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
      validator: value => ['resource', 'building', 'village'].includes(value)
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

    accentStyle() {
      if (this.type === 'village' && this.data.user_info?.color) {
        return {
          backgroundColor: this.data.user_info.color
        }
      }
      return {}
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