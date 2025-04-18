<template>
  <div v-if="show && activeTasks.length > 0" class="tasks-container">
    <div class="tasks-table">
      <table>
        <thead>
          <tr>
            <th>Troop Type</th>
            <th class="family-col">Owner</th>
            <th class="location-col">Target</th>
            <th class="action-col">Action</th>
            <th class="time-col">Remaining</th>
            <th class="hide-on-mobile">Completion</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in activeTasks" :key="task.id">
            <td class="troop-type">
              <v-icon size="18" :color="getTroopOwnershipColor(task)">{{ getTroopTypeIcon(task) }}</v-icon>
              <span class="troop-name" :style="{ color: getTroopOwnershipTextColor(task) }">{{ getTroopTypeName(task) }}</span>
            </td>
            <td class="family-col">
              <span class="family-name" :style="{ color: getTroopOwnershipTextColor(task) }">
                {{ getTroopOwnerFamilyName(task) }}
              </span>
            </td>
            <td class="location-col">
              {{ formatLocation(task.target_location) }}
            </td>
            <td class="action-col">
              <div class="action-wrapper">
                <v-icon size="16" :color="getActionColor(task)">{{ getActionIcon(task) }}</v-icon>
              </div>
            </td>
            <td class="time-col">
              <div class="progress-wrapper">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{
                    width: `${calculateProgress(task)}%`,
                    backgroundColor: getActionColor(task) 
                  }"></div>
                </div>
                <span class="time-text countdown">{{ currentTimes[task.id] }}</span>
              </div>
            </td>
            <td class="hide-on-mobile">{{ formatLocalTime(task.completion_time) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  <div v-else-if="show" class="no-tasks-message">
    No active troop movements at this location
  </div>
</template>

<script>
import { TROOP_STATUS, TROOP_TYPES, FRIENDLY_STATUS, getTroopInfo, getTroopTypeName, getTroopStatusInfo, getTroopStatusIcon, getTroopStatusColor, getFriendlyStatusColor, getFriendlyStatusTextColor } from '../constants/gameElements';

export default {
  name: 'TroopActionTaskDisplay',
  
  props: {
    show: {
      type: Boolean,
      required: true
    },
    tasks: {
      type: Array,
      required: false,
      default: () => []
    },
    troops: {
      type: Array,
      required: false,
      default: () => []
    },
    villages: {
      type: Array,
      required: false,
      default: () => [],
      description: "Array of village objects, needed to determine if a troop belongs to the player (for icon color)"
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
      animationFrameId: null,
      serverClientTimeDiff: 0,
      completedTasks: [],
      secondTimer: null,
      currentTimes: {},
      forceUpdate: 0
    };
  },

  computed: {
    // Force-update every time forceUpdate changes
    currentTimestamp() {
      return this.forceUpdate;
    },
    
    // Filter only active tasks (not yet completed)
    activeTasks() {
      // Use current timestamp to force updates
      const _ = this.currentTimestamp;
      
      const active = this.tasks.filter(task => {
        if (!task) return false;
        
        // Calculate remaining time
        const remainingTime = this.calculateRemainingTime(task);
        return remainingTime > 0;
      });

      return active;
    }
  },

  watch: {
    show(newValue) {
      if (newValue) {
        this.startAnimation();
        this.startSecondTimer();
        this.updateAllTimes();
      } else {
        this.stopAnimation();
        this.stopSecondTimer();
      }
    },
    
    serverTime: {
      immediate: true,
      handler(newServerTime) {
        if (newServerTime) {
          this.syncWithServerTime(newServerTime);
          this.updateAllTimes();
        }
      }
    },
    
    tasks: {
      immediate: true,
      deep: true,
      handler(newTasks) {
        // Log the first task for debugging
        if (newTasks && newTasks.length > 0) {
          console.log('TROOP ACTION TASK STRUCTURE:', JSON.stringify(newTasks[0], null, 2));
        }
        
        // Reset completed tasks and update times
        this.completedTasks = [];
        this.updateAllTimes();
      }
    }
  },

  mounted() {
    console.log("TroopActionTaskDisplay mounted");
    this.updateAllTimes();
    
    if (this.show) {
      this.startAnimation();
      this.startSecondTimer();
    }
    
    if (this.serverTime) {
      this.syncWithServerTime(this.serverTime);
    }
  },

  beforeDestroy() {
    this.stopAnimation();
    this.stopSecondTimer();
  },

  methods: {
    updateAllTimes() {
      if (!this.tasks || this.tasks.length === 0) return;
      
      console.log("Updating all times for troop actions:", this.tasks.length);
      
      this.tasks.forEach(task => {
        if (!task || !task.id) return;
        
        const remainingTime = this.calculateRemainingTime(task);
        this.currentTimes[task.id] = this.formatTime(remainingTime);
      });
    },
    
    startSecondTimer() {
      // Clear any existing timer
      this.stopSecondTimer();
      
      console.log("Starting second timer");
      
      // Create a timer that triggers every second
      this.secondTimer = setInterval(() => {
        // Increment force update to trigger reactivity
        this.forceUpdate++;
        
        // Update all times
        this.updateAllTimes();
        
        // Check for completed tasks
        if (this.tasks && this.tasks.length > 0) {
          this.tasks.forEach(task => {
            if (!task || !task.id) return;
            
            const remainingTime = this.calculateRemainingTime(task);
            
            // If task is just completed and not already in completedTasks
            if (remainingTime <= 0 && !this.completedTasks.includes(task.id)) {
              console.log("Troop action completed:", task.id);
              this.completedTasks.push(task.id);
              this.$emit('task-completed', task);
            }
          });
        }
      }, 1000);
    },
    
    stopSecondTimer() {
      if (this.secondTimer) {
        clearInterval(this.secondTimer);
        this.secondTimer = null;
      }
    },
  
    syncWithServerTime(serverTimeStr) {
      try {
        // Parse server time
        const serverTime = new Date(serverTimeStr).getTime();
        
        // Use the client response time if available, otherwise use current time
        const clientTime = this.clientResponseTime || Date.now();
        
        // Calculate difference (server - client)
        this.serverClientTimeDiff = serverTime - clientTime;
        
      } catch (error) {
        console.error('Error syncing with server time:', error);
        this.serverClientTimeDiff = 0;
      }
    },
    
    getCurrentServerTime() {
      // Return current time adjusted for server-client difference
      return Date.now() + this.serverClientTimeDiff;
    },

    startAnimation() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
      }
      
      this.updateAnimation();
    },

    stopAnimation() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    },

    updateAnimation() {
      // Only use animation frame for progress bar updates
      this.animationFrameId = requestAnimationFrame(this.updateAnimation);
    },

    calculateRemainingTime(task) {
      if (!task || !task.completion_time) return 0;
      
      const now = this.getCurrentServerTime();
      const endTime = new Date(task.completion_time).getTime();
      return Math.max(0, endTime - now);
    },

    calculateProgress(task) {
      if (!task || !task.started_at || !task.completion_time) return 0;
      
      const now = this.getCurrentServerTime();
      const startTime = new Date(task.started_at).getTime();
      const endTime = new Date(task.completion_time).getTime();
      const total = endTime - startTime;
      const elapsed = now - startTime;
      
      if (total <= 0) return 100;
      return Math.min(100, Math.max(0, (elapsed / total) * 100));
    },

    formatTime(ms) {
      if (ms <= 0) return 'Complete';
      
      const seconds = Math.floor((ms / 1000) % 60);
      const minutes = Math.floor((ms / (1000 * 60)) % 60);
      const hours = Math.floor((ms / (1000 * 60 * 60)) % 24);
      
      if (hours > 0) {
        return `${hours}h ${minutes.toString().padStart(2, '0')}m`;
      } else if (minutes > 0) {
        return `${minutes}m ${seconds.toString().padStart(2, '0')}s`;
      } else {
        return `${seconds}s`;
      }
    },
    
    formatLocation(location) {
      if (!location || location.x === undefined || location.y === undefined) {
        return 'Unknown';
      }
      return `(${location.x}, ${location.y})`;
    },

    getTroopForTask(task) {
      if (!task || !task.troop_id || !this.troops) return null;
      return this.troops.find(troop => troop.id === task.troop_id);
    },
    
    getTroopTypeIcon(task) {
      const troop = this.getTroopForTask(task);
      if (!troop) return 'mdi-army';
      
      const troopInfo = getTroopInfo(troop.type);
      return troopInfo ? troopInfo.icon : 'mdi-army';
    },
    
    getTroopTypeName(task) {
      const troop = this.getTroopForTask(task);
      if (!troop) return 'Unknown Troop';
      
      return getTroopTypeName(troop.type);
    },
    
    getActionIcon(task) {
      if (!task || !task.action_type) return 'mdi-map-marker-path';
      
      // Use getTroopStatusIcon to get the icon based on action type
      return getTroopStatusIcon(task.action_type);
    },
    
    getActionColor(task) {
      if (!task || !task.action_type) return '#2196f3'; // Default blue
      
      // Use getTroopStatusColor to get the color based on action type
      return getTroopStatusColor(task.action_type);
    },

    formatLocalTime(timeString) {
      try {
        if (!timeString) return 'Unknown';
        
        // First convert server time to client time by adjusting for server-client difference
        const serverTime = new Date(timeString).getTime();
        const clientTime = serverTime - this.serverClientTimeDiff;
        const date = new Date(clientTime);
        
        // Create a more descriptive format showing today's date or "Today"
        const now = new Date();
        let formattedDate;
        
        // Check if it's today
        if (date.toDateString() === now.toDateString()) {
          formattedDate = 'Today';
        } else {
          // Otherwise show MM/DD format
          formattedDate = `${date.getMonth() + 1}/${date.getDate()}`;
        }
        
        // Get time in client's locale format
        const formattedTime = date.toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit'
        });
        
        // Combine date and time
        return `${formattedDate} ${formattedTime}`;
      } catch (e) {
        console.error('Error formatting time:', e);
        return timeString || 'Unknown';
      }
    },

    getTroopOwnershipColor(task) {
      const troop = this.getTroopForTask(task);
      if (!troop) return '#757575'; // Default gray
      
      // Determine if the troop belongs to the user
      const homeVillage = this.villages.find(v => v.id === troop.home_id);
      const isOwned = homeVillage ? homeVillage.is_owned : false;
      
      // Return appropriate color based on ownership status
      if (isOwned) {
        return getFriendlyStatusColor('MYSELF');
      } else {
        return getFriendlyStatusColor('ENEMY');
      }
    },

    getTroopOwnershipTextColor(task) {
      const troop = this.getTroopForTask(task);
      if (!troop) return '#666'; // Default gray
      
      // Determine if the troop belongs to the user
      const homeVillage = this.villages.find(v => v.id === troop.home_id);
      const isOwned = homeVillage ? homeVillage.is_owned : false;
      
      // Return appropriate text color based on ownership status
      if (isOwned) {
        return getFriendlyStatusTextColor('MYSELF');
      } else {
        return getFriendlyStatusTextColor('ENEMY');
      }
    },

    getTroopOwnerFamilyName(task) {
      const troop = this.getTroopForTask(task);
      if (!troop) return 'Unknown';
      
      // Get home village to find owner info
      const homeVillage = this.villages.find(v => v.id === troop.home_id);
      if (!homeVillage) return 'Unknown';
      
      // Return family name from user_info if available
      return homeVillage.user_info && homeVillage.user_info.family_name 
        ? homeVillage.user_info.family_name 
        : (homeVillage.is_owned ? 'You' : 'Enemy');
    }
  }
};
</script>

<style scoped>
.tasks-container {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99; /* Keep lower z-index than ConstructionTasksDisplay */
  width: 720px;
  max-width: 90vw;
}

.tasks-table {
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  font-size: 13px;
  max-height: 180px;
}

.no-tasks-message {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(255, 255, 255, 0.95);
  padding: 10px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  font-size: 13px;
  color: #666;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background-color: #f5f5f5;
  position: sticky;
  top: 0;
  z-index: 1;
}

thead tr {
  display: table;
  width: 100%;
  table-layout: fixed;
}

tbody {
  display: block;
  max-height: 140px;
  overflow-y: auto;
}

tbody tr {
  display: table;
  width: 100%;
  table-layout: fixed;
}

th {
  padding: 6px 12px;
  text-align: left;
  font-weight: 600;
  color: #666;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

td {
  padding: 6px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  white-space: nowrap;
}

tbody tr:last-child td {
  border-bottom: none;
}

.troop-type {
  display: flex;
  align-items: center;
  max-width: 180px;
  width: 180px;
}

.troop-name {
  margin-left: 6px;
  color: #333;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.family-col {
  width: 100px;
  text-align: center;
}

.family-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 90px;
  display: inline-block;
}

.location-col {
  width: 80px;
  text-align: center;
  color: #555;
}

.action-col {
  width: 80px;
  text-align: center;
}

.action-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.time-col {
  width: 100px;
}

.progress-wrapper {
  display: flex;
  flex-direction: column;
}

.progress-bar {
  height: 4px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 1s linear;
}

.time-text {
  font-size: 11px;
  font-weight: 500;
  color: #444;
}

.countdown {
  animation: pulse 1s infinite alternate;
}

@keyframes pulse {
  from {
    opacity: 0.8;
    color: #555;
  }
  to {
    opacity: 1;
    color: #000;
  }
}

/* Mobile optimizations */
@media (max-width: 600px) {
  .tasks-container {
    width: 95vw;
    max-width: 95vw;
    bottom: 70px;
  }
  
  .troop-type {
    max-width: 120px;
    width: 120px;
  }
  
  .troop-name {
    max-width: 80px;
    font-size: 12px;
  }
  
  .family-col {
    width: 70px;
  }
  
  .family-name {
    max-width: 60px;
    font-size: 12px;
  }
  
  .location-col {
    width: 60px;
  }
  
  .time-col {
    width: 70px;
  }
  
  .hide-on-mobile {
    display: none;
  }
  
  th, td {
    padding: 5px 4px;
    font-size: 11px;
  }
  
  .progress-wrapper .time-text {
    font-size: 10px;
  }
}
</style> 