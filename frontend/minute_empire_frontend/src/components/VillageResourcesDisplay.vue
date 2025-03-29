<template>
  <div v-if="resources" class="resources-arc">
    <div class="resource-bar">
      <div
        v-for="resource in resourcesArray"
        :key="resource.name"
        class="resource-section"
      >
        <div class="resource-content">
          <div class="resource-icon" :class="resource.name">
            <v-icon size="26" :color="getResourceColor(resource.name)">{{ getResourceIcon(resource.name) }}</v-icon>
          </div>
          <div class="resource-details">
            <div class="resource-amount">
              <span class="amount-value">{{ resource.amount.toFixed(0) }}</span>
              <span class="capacity-value hide-on-mobile">/{{ getCapacity(resource.name).toFixed(0) }}</span>
            </div>
            <div class="capacity-bar">
              <div class="capacity-fill" :style="{
                width: `${Math.min(100, (resource.amount / getCapacity(resource.name)) * 100)}%`,
                backgroundColor: getResourceColor(resource.name, 0.7)
              }"></div>
            </div>
            <div class="resource-rate">+{{ resource.rate.toFixed(1) }}/h</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VillageResourcesDisplay',
  
  props: {
    show: {
      type: Boolean,
      required: true
    },
    village: {
      type: Object,
      required: false,
      default: null
    },
    serverTime: {
      type: String,
      required: false,
      default: null
    },
    clientResponseTime: {
      type: Number,
      required: false,
      default: null
    }
  },

  data() {
    return {
      resourceTypes: ['wood', 'food', 'stone', 'iron'],
      resourceAmounts: {},
      lastUpdateTime: null,
      animationFrameId: null,
      serverClientTimeDiff: 0, // Time difference between server and client in milliseconds
      dataReceiveTime: null // When we received the data from server
    };
  },

  computed: {
    hasResources() {
      return this.village && this.village.resources;
    },
    resources() {
      return this.village ? this.village.resources : null;
    },
    resourcesArray() {
      return this.resourceTypes.map(type => ({
        name: type,
        amount: this.resourceAmounts[type] || 0,
        rate: this.getRate(type)
      }));
    }
  },

  watch: {
    village: {
      immediate: true,
      handler(newVillage, oldVillage) {
        // Only reinitialize if it's a different village or first initialization
        if (newVillage && newVillage.resources && 
            (!oldVillage || newVillage.id !== oldVillage.id)) {
          this.initializeResourceAmounts();
        }
      }
    },
    show(newValue) {
      if (newValue) {
        this.startResourceAnimation();
      } else {
        this.stopResourceAnimation();
      }
    },
    serverTime: {
      immediate: true,
      handler(newServerTime) {
        if (newServerTime) {
          this.syncWithServerTime(newServerTime);
        }
      }
    },
    clientResponseTime: {
      immediate: true,
      handler(newTime) {
        if (newTime) {
          this.dataReceiveTime = newTime;
        }
      }
    }
  },

  mounted() {
    if (this.show && this.village) {
      this.initializeResourceAmounts();
      this.startResourceAnimation();
    }
    
    if (this.serverTime) {
      this.syncWithServerTime(this.serverTime);
    }
  },

  beforeDestroy() {
    this.stopResourceAnimation();
  },

  methods: {
    syncWithServerTime(serverTimeStr) {
      try {
        // Parse server time
        const serverTime = new Date(serverTimeStr).getTime();
        // Get current client time
        const clientTime = Date.now();
        // Calculate difference (server - client)
        this.serverClientTimeDiff = serverTime - clientTime;
        
        console.log(`Synced with server time. Difference: ${this.serverClientTimeDiff}ms`);
      } catch (error) {
        console.error('Error syncing with server time:', error);
        this.serverClientTimeDiff = 0;
      }
    },
    
    getCurrentServerTime() {
      // Return current time adjusted for server-client difference
      return Date.now() + this.serverClientTimeDiff;
    },

    getResourceColor(type, opacity = 1) {
      const colors = {
        wood: `rgba(139, 195, 74, ${opacity})`, // Green
        food: `rgba(255, 193, 7, ${opacity})`, // Amber
        stone: `rgba(158, 158, 158, ${opacity})`, // Gray
        iron: `rgba(66, 165, 245, ${opacity})`  // Blue
      };
      return colors[type] || `rgba(255, 255, 255, ${opacity})`;
    },
    
    getResourceIcon(type) {
      const icons = {
        food: 'mdi-food',
        wood: 'mdi-tree',
        stone: 'mdi-mountain',
        iron: 'mdi-pickaxe'
      };
      return icons[type] || 'mdi-help-circle';
    },

    initializeResourceAmounts() {
      // Use server-adjusted time
      const now = this.getCurrentServerTime();
      this.lastUpdateTime = now;

      if (!this.hasResources) return;

      // Calculate how much time has passed since the server sent this data
      let elapsedSinceDataReceive = 0;
      if (this.dataReceiveTime) {
        // Time passed since we received the data from the server
        elapsedSinceDataReceive = (Date.now() - this.dataReceiveTime) / 1000; // in seconds
        console.log(`Elapsed since data receive: ${elapsedSinceDataReceive}s`);
      }

      // Initialize with current resource amounts from server, adjusted for time passed
      this.resourceTypes.forEach(type => {
        if (this.village.resources[type]) {
          const resourceInfo = this.village.resources[type];
          let adjustedAmount = resourceInfo.current;
          
          // Add resources that would have been produced since we received the data
          if (elapsedSinceDataReceive > 0) {
            const additionalAmount = (resourceInfo.rate / 3600) * elapsedSinceDataReceive;
            adjustedAmount = Math.min(adjustedAmount + additionalAmount, resourceInfo.capacity);
          }
          
          this.resourceAmounts[type] = adjustedAmount;
        } else {
          this.resourceAmounts[type] = 0;
        }
      });
    },

    startResourceAnimation() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
      }
      
      // Use server-adjusted time
      this.lastUpdateTime = this.getCurrentServerTime();
      this.updateResourceAmounts();
    },

    stopResourceAnimation() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    },

    updateResourceAmounts() {
      // Use server-adjusted time for calculations
      const now = this.getCurrentServerTime();
      const elapsed = (now - this.lastUpdateTime) / 1000; // seconds
      this.lastUpdateTime = now;

      if (this.hasResources) {
        this.resourceTypes.forEach(type => {
          if (this.village.resources[type]) {
            const rate = this.village.resources[type].rate;
            const capacity = this.village.resources[type].capacity;
            
            // Calculate new amount (convert rate from per hour to per second)
            let newAmount = this.resourceAmounts[type] + (rate / 3600) * elapsed;
            
            // Cap at capacity
            if (newAmount > capacity) {
              newAmount = capacity;
            }
            
            this.resourceAmounts[type] = newAmount;
          }
        });
      }

      // Continue animation if component is still visible
      if (this.show) {
        this.animationFrameId = requestAnimationFrame(this.updateResourceAmounts);
      }
    },

    getCurrentAmount(type) {
      return this.resourceAmounts[type] || 0;
    },

    getRate(type) {
      if (!this.hasResources || !this.village.resources[type]) return 0;
      return this.village.resources[type].rate;
    },

    getCapacity(type) {
      if (!this.hasResources || !this.village.resources[type]) return 0;
      return this.village.resources[type].capacity;
    },

    formatNumber(value) {
      if (value === undefined || value === null) return 0;
      if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
      } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
      }
      return Math.floor(value);
    },

    getResourceIconPath(type) {
      // Implement the logic to return the correct icon path based on the resource type
      // This is a placeholder and should be replaced with the actual implementation
      return this.getResourceIcon(type);
    }
  }
};
</script>

<style scoped>
.resources-arc {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 720px;
}

.resource-bar {
  display: flex;
  justify-content: space-between;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 14px;
  padding: 18px 24px;
  height: 80px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.resource-section {
  display: flex;
  align-items: center;
  padding: 0 12px;
  position: relative;
  flex: 1;
}

.resource-section::after {
  content: "";
  position: absolute;
  right: 0;
  top: 15%;
  height: 70%;
  width: 1px;
  background: rgba(0, 0, 0, 0.08);
}

.resource-section:last-child::after {
  display: none;
}

.resource-content {
  display: flex;
  align-items: center;
}

.resource-icon {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  border-radius: 50%;
}

.resource-icon.wood {
  background: rgba(139, 195, 74, 0.15);
}

.resource-icon.food {
  background: rgba(255, 193, 7, 0.15);
}

.resource-icon.stone {
  background: rgba(158, 158, 158, 0.15);
}

.resource-icon.iron {
  background: rgba(66, 165, 245, 0.15);
}

.resource-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 80px;
  width: 100%;
}

.resource-amount {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: baseline;
  margin-bottom: 2px;
}

.amount-value {
  margin-right: 2px;
}

.capacity-value {
  font-size: 15px;
  color: #777;
  font-weight: 500;
}

.capacity-bar {
  width: 100%;
  height: 4px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 2px;
  margin: 3px 0;
  overflow: hidden;
}

.capacity-fill {
  height: 100%;
  border-radius: 2px;
}

.resource-rate {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

@media (max-width: 600px) {
  .resources-arc {
    width: 420px;
    top: 48px;
  }
  
  .resource-bar {
    padding: 12px 16px;
    height: 56px;
  }
  
  .resource-icon {
    width: 28px;
    height: 28px;
    margin-right: 6px;
  }
  
  .resource-details {
    min-width: 52px;
  }
  
  .resource-amount {
    font-size: 16px;
  }
  
  .hide-on-mobile {
    display: none;
  }
  
  .resource-rate {
    font-size: 10px;
    margin-top: 2px;
  }
  
  .resource-section {
    padding: 0 6px;
  }
}
</style> 