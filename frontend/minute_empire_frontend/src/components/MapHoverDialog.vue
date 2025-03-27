<template>
  <v-card
    v-if="show"
    class="map-hover-dialog"
    :style="dialogStyle"
    elevation="4"
  >
    <v-card-text class="pa-2">
      <!-- Header -->
      <div class="d-flex align-center mb-2">
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
        <div class="d-flex justify-space-between align-center mb-1">
          <span class="text-caption text-grey">Slot:</span>
          <span class="text-caption font-weight-medium">{{ data.slot }}</span>
        </div>
        
        <!-- Show level only if not empty -->
        <div v-if="!data.isEmpty" class="d-flex justify-space-between align-center mb-1">
          <span class="text-caption text-grey">Level:</span>
          <span class="text-caption font-weight-medium">{{ data.level }}</span>
        </div>
        
        <!-- Show empty message if empty -->
        <div v-else class="d-flex align-center">
          <v-icon size="16" color="grey" class="mr-1">mdi-information</v-icon>
          <span class="text-caption text-grey">Empty slot</span>
        </div>
        
        <!-- Dynamic content slots for future expansion -->
        <slot name="additional-info"></slot>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
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
      validator: value => ['resource', 'building'].includes(value)
    }
  },
  
  computed: {
    dialogStyle() {
      return {
        position: 'absolute',
        left: `${this.position.x}px`,
        top: `${this.position.y}px`,
        zIndex: 1000,
        maxWidth: '200px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(4px)'
      }
    },
    
    title() {
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
        return '#9E9E9E' // Grey for empty slots
      }
      
      if (this.type === 'resource') {
        const colors = {
          food: '#FFEB3B',
          wood: '#8BC34A',
          stone: '#9E9E9E',
          iron: '#607D8B'
        }
        return colors[this.data.type] || '#FFFFFF'
      } else {
        return '#795548' // Default brown for buildings
      }
    },
    
    getTypeIcon() {
      if (this.data.isEmpty) {
        return 'mdi-help-circle'
      }
      
      if (this.type === 'resource') {
        const icons = {
          food: 'mdi-food',
          wood: 'mdi-tree',
          stone: 'mdi-mountain',
          iron: 'mdi-pickaxe'
        }
        return icons[this.data.type] || 'mdi-help-circle'
      } else {
        return 'mdi-office-building'
      }
    }
  }
}
</script>

<style scoped>
.map-hover-dialog {
  border-radius: 8px;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.map-hover-dialog:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}
</style> 