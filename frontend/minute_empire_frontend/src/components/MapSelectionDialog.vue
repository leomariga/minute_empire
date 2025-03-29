<template>
  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    :max-width="isMobile ? '100%' : '400'"
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
        <v-btn
          icon
          @click="closeDialog"
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
          </v-img>
        </div>

        <!-- Description -->
        <div class="description mb-4">
          <p class="text-body-1">
            {{ description }}
          </p>
        </div>

        <!-- Info Grid -->
        <v-row class="info-grid mb-4">
          <v-col cols="6">
            <div class="info-item">
              <span class="text-caption text-grey">Slot</span>
              <span class="text-subtitle-1 font-weight-medium">{{ data.slot }}</span>
            </div>
          </v-col>
          <v-col cols="6">
            <div class="info-item">
              <span class="text-caption text-grey">Level</span>
              <span class="text-subtitle-1 font-weight-medium">{{ data.level || 0 }}</span>
            </div>
          </v-col>
        </v-row>

        <!-- Future expansion slots -->
        <slot name="additional-info"></slot>

        <!-- Action Buttons -->
        <v-card-actions class="pa-0">
          <v-btn
            block
            color="primary"
            :disabled="!canUpgrade"
            @click="handleUpgrade"
          >
            <v-icon left>mdi-arrow-up</v-icon>
            Upgrade
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'MapSelectionDialog',
  
  props: {
    show: {
      type: Boolean,
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
  
  data() {
    return {
      windowWidth: window.innerWidth
    }
  },
  
  computed: {
    isMobile() {
      return this.windowWidth < 600
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
        return '#9E9E9E'
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
        return '#795548'
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
    },

    description() {
      if (this.data.isEmpty) {
        return this.type === 'resource' 
          ? 'An empty resource field. Build a resource production building here to gather resources.'
          : 'An empty building slot. Construct a building here to improve your village.'
      }

      if (this.type === 'resource') {
        const descriptions = {
          food: 'Produces food for your village. Higher levels increase production.',
          wood: 'Produces wood for construction and upgrades. Higher levels increase production.',
          stone: 'Produces stone for construction and upgrades. Higher levels increase production.',
          iron: 'Produces iron for military units and upgrades. Higher levels increase production.'
        }
        return descriptions[this.data.type] || 'Resource production field.'
      } else {
        const descriptions = {
          city_center: 'The heart of your village. Higher levels unlock more building slots.',
          rally_point: 'Command center for your military. Higher levels allow larger armies.',
          barraks: 'Train infantry units here. Higher levels unlock more unit types.',
          archery: 'Train archer units here. Higher levels unlock more unit types.',
          stable: 'Train cavalry units here. Higher levels unlock more unit types.',
          warehouse: 'Store resources safely. Higher levels increase storage capacity.',
          granary: 'Store food safely. Higher levels increase storage capacity.',
          hide_spot: 'Hide resources from enemies. Higher levels increase hiding capacity.'
        }
        return descriptions[this.data.type] || 'Building description.'
      }
    },

    imageUrl() {
      // Placeholder for future image implementation
      return this.type === 'resource' 
        ? `/images/resources/${this.data.type}.png`
        : `/images/buildings/${this.data.type}.png`
    },

    canUpgrade() {
      // This will be expanded in the future to check resources and other conditions
      return !this.data.isEmpty && this.data.level < 10
    }
  },

  methods: {
    closeDialog() {
      this.$emit('update:show', false)
    },

    handleUpgrade() {
      this.$emit('upgrade', {
        type: this.type,
        slot: this.data.slot,
        currentLevel: this.data.level
      });
      this.closeDialog();
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

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
}

@media (max-width: 600px) {
  .selection-dialog {
    border-radius: 0;
  }
}
</style> 