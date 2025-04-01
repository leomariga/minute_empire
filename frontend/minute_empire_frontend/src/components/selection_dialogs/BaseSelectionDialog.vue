<template>
  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    :max-width="isMobile ? '100%' : '450'"
    :fullscreen="isMobile"
    transition="dialog-bottom-transition"
    @click:outside="$emit('close')"
  >
    <v-card class="selection-dialog">
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-4">
        <v-icon
          :color="typeColor"
          class="mr-2"
          size="24"
        >
          {{ typeIcon }}
        </v-icon>
        <span class="text-h6 font-weight-bold">
          {{ title }}
        </span>
        <v-spacer></v-spacer>
        <slot name="header-actions"></slot>
        <v-btn
          icon
          @click="$emit('close')"
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
                <div class="image-fallback" :style="`background-color: ${typeColor}15`">
                  <v-icon :color="typeColor" size="64">{{ typeIcon }}</v-icon>
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
            <slot name="image-badges"></slot>
          </div>
        </div>

        <!-- Description -->
        <div class="description mb-4">
          <p class="text-body-1">
            {{ description }}
          </p>
        </div>

        <!-- Main slot for specialized content -->
        <slot name="content"></slot>
        
        <!-- Actions slot for buttons/controls -->
        <slot name="actions"></slot>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'BaseSelectionDialog',
  
  props: {
    show: {
      type: Boolean,
      required: true
    },
    slotId: {
      type: Number,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    description: {
      type: String,
      default: ''
    },
    typeColor: {
      type: String,
      default: 'grey'
    },
    typeIcon: {
      type: String,
      default: 'mdi-help-circle'
    },
    imageUrl: {
      type: String,
      default: ''
    }
  },

  emits: ['update:show', 'close'],
  
  data() {
    return {
      windowWidth: window.innerWidth
    }
  },
  
  computed: {
    isMobile() {
      return this.windowWidth < 600
    }
  },
  
  mounted() {
    window.addEventListener('resize', this.handleResize)
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
  },
  
  methods: {
    handleResize() {
      this.windowWidth = window.innerWidth
    }
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

.description {
  line-height: 1.5;
  font-size: 14px;
  margin-bottom: 12px;
}

@media (max-width: 600px) {
  .selection-dialog {
    border-radius: 0;
  }
}
</style> 