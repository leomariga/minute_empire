<template>
  <div v-if="show && activeTasks.length > 0" class="tasks-container">
    <div class="tasks-table">
      <table>
        <thead>
          <tr>
            <th>Building/Field/Troop</th>
            <th class="slot-col">Slot/Qty</th>
            <th class="operation-col">Operation</th>
            <th class="time-col">Remaining</th>
            <th class="hide-on-mobile">Completion</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in activeTasks" :key="task.id">
            <td class="task-type">
              <v-icon size="18" :color="getTaskColor(task)">{{ getTaskIcon(task) }}</v-icon>
              <span class="task-name">{{ getTaskName(task) }}</span>
            </td>
            <td class="slot-col">{{ getTaskSlotOrQuantity(task) }}</td>
            <td class="operation-col">
              <div class="operation-wrapper">
                <template v-if="isUpgradeTask(task)">
                  <div class="upgrade-container">
                    <v-icon size="16" :color="getOperationColor(task)">{{ getOperationIcon(task) }}</v-icon>
                    <span class="upgrade-level">{{ task.level }}</span>
                  </div>
                </template>
                <template v-else-if="isTroopTrainingTask(task)">
                  <v-icon size="16" :color="getTroopColor(task.troop_type)">mdi-shield-account</v-icon>
                </template>
                <template v-else>
                  <v-icon size="16" :color="getOperationColor(task)">{{ getOperationIcon(task) }}</v-icon>
                </template>
              </div>
            </td>
            <td class="time-col">
              <div class="progress-wrapper">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{
                    width: `${calculateProgress(task)}%`,
                    backgroundColor: getTaskColor(task) 
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
    No active construction or training tasks
  </div>
</template>

<script>
import { TASK_TYPES, formatTargetTypeName, TROOP_TYPES, getTroopTypeName, getTroopInfo, getTroopColor } from '../constants/gameElements';

export default {
  name: 'ConstructionTasksDisplay',
  
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
    troopTrainingTasks: {
      type: Array,
      required: false,
      default: () => []
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
    },
    villages: {
      type: Array,
      required: false,
      default: () => []
    },
    focusedVillage: {
      type: Object,
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
    
    // Combine construction tasks and troop training tasks
    allTasks() {
      const constructionTasks = this.tasks || [];
      const troopTasks = this.troopTrainingTasks || [];
      
      // Mark troop training tasks to identify them later
      const markedTroopTasks = troopTasks.map(task => ({
        ...task,
        isTroopTraining: true
      }));
      
      return [...constructionTasks, ...markedTroopTasks];
    },
    
    // Filter only active tasks (not yet completed)
    activeTasks() {
      // Use current timestamp to force updates
      const _ = this.currentTimestamp;
      
      const active = this.allTasks.filter(task => {
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
    
    allTasks: {
      immediate: true,
      deep: true,
      handler(newTasks) {
        // Log the first task for debugging
        if (newTasks && newTasks.length > 0) {
          console.log('TASK STRUCTURE:', JSON.stringify(newTasks[0], null, 2));
        }
        
        // Reset completed tasks and update times
        this.completedTasks = [];
        this.updateAllTimes();
      }
    }
  },

  mounted() {
    console.log("ConstructionTasksDisplay mounted");
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
      if (!this.allTasks || this.allTasks.length === 0) return;
      
      console.log("Updating all times for tasks:", this.allTasks.length);
      
      this.allTasks.forEach(task => {
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
        if (this.allTasks && this.allTasks.length > 0) {
          this.allTasks.forEach(task => {
            if (!task || !task.id) return;
            
            const remainingTime = this.calculateRemainingTime(task);
            
            // If task is just completed and not already in completedTasks
            if (remainingTime <= 0 && !this.completedTasks.includes(task.id)) {
              console.log("Task completed:", task.id);
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

    getTaskTypeClass(type) {
      return type.toLowerCase().replace('_', '-');
    },

    // Determine if a task is a troop training task
    isTroopTrainingTask(task) {
      return task && task.isTroopTraining === true;
    },

    // Get the task color (works for both construction and troop tasks)
    getTaskColor(task) {
      if (this.isTroopTrainingTask(task)) {
        return this.getTroopColor(task.troop_type);
      } else {
        return this.getTaskTypeColor(task.task_type);
      }
    },

    // Get the task icon (works for both construction and troop tasks)
    getTaskIcon(task) {
      if (this.isTroopTrainingTask(task)) {
        return this.getTroopIcon(task.troop_type);
      } else {
        return this.getTaskTypeIcon(task.task_type);
      }
    },

    // Get the task name (works for both construction and troop tasks)
    getTaskName(task) {
      if (this.isTroopTrainingTask(task)) {
        return `${getTroopTypeName(task.troop_type)}`;
      } else {
        return this.getFormattedTargetName(task);
      }
    },

    // Get slot for construction tasks, quantity for troop tasks
    getTaskSlotOrQuantity(task) {
      if (this.isTroopTrainingTask(task)) {
        return task.quantity;
      } else {
        return task.slot;
      }
    },

    // Get the troop color
    getTroopColor(troopType, opacity = 1) {
      // Use helper from gameElements
      const troopInfo = getTroopInfo(troopType);
      if (!troopInfo) return `rgba(158, 158, 158, ${opacity})`;
      
      // Convert hex to rgba
      const hex = troopInfo.color;
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    },

    // Get the troop icon
    getTroopIcon(troopType) {
      const troopInfo = getTroopInfo(troopType);
      return troopInfo ? troopInfo.icon : 'mdi-help-circle';
    },

    getTaskTypeColor(type, opacity = 1) {
      // Normalize type to uppercase for consistency
      const normalizedType = type?.toUpperCase() || 'DEFAULT';
      const taskInfo = TASK_TYPES[normalizedType];
      
      return taskInfo ? taskInfo.color.replace(')', `, ${opacity})`) : `rgba(158, 158, 158, ${opacity})`;
    },
    
    getTaskTypeIcon(type) {
      // Normalize type to uppercase for consistency
      const normalizedType = type?.toUpperCase() || 'DEFAULT';
      const taskInfo = TASK_TYPES[normalizedType];
      
      return taskInfo ? taskInfo.icon : 'mdi-clock-outline';
    },
    
    getOperationIcon(task) {
      if (!task || !task.task_type) return 'mdi-hammer';
      
      // Normalize task type to uppercase for consistency
      const normalizedType = task.task_type.toUpperCase();
      const taskInfo = TASK_TYPES[normalizedType];
      
      return taskInfo ? taskInfo.operationIcon : 'mdi-hammer';
    },
    
    getOperationColor(task) {
      if (!task || !task.task_type) return '#3f51b5';
      
      // Normalize task type to uppercase for consistency
      const normalizedType = task.task_type.toUpperCase();
      const taskInfo = TASK_TYPES[normalizedType];
      
      return taskInfo ? taskInfo.operationColor : '#3f51b5';
    },
    
    isUpgradeTask(task) {
      if (!task || !task.task_type) return false;
      
      // Not upgrade task if it's a troop training task
      if (this.isTroopTrainingTask(task)) return false;
      
      // Normalize task type to uppercase for consistency
      const normalizedType = task.task_type.toUpperCase();
      return normalizedType === 'UPGRADE_FIELD' || normalizedType === 'UPGRADE_BUILDING';
    },
    
    getFormattedTargetName(task) {
      if (!task || !task.target_type) return 'Unknown';
      return formatTargetTypeName(task.target_type);
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
  z-index: 100;
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

.task-type {
  display: flex;
  align-items: center;
  max-width: 180px;
  width: 180px;
}

.task-name {
  margin-left: 6px;
  color: #333;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.slot-col {
  text-align: center;
  width: 60px;
  color: #555;
}

.operation-col {
  width: 70px;
  text-align: center;
}

.operation-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.level-text {
  font-size: 10px;
  font-weight: 500;
  margin-top: 2px;
  color: #666;
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
  
  .task-type {
    max-width: 120px;
    width: 120px;
  }
  
  .task-name {
    max-width: 80px;
    font-size: 12px;
  }
  
  .slot-col {
    width: 36px;
  }
  
  .operation-col {
    width: 42px;
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
  
  .level-text {
    font-size: 9px;
  }
  
  .progress-wrapper .time-text {
    font-size: 10px;
  }
}

.upgrade-container {
  display: flex;
  align-items: center;
  gap: 3px;
}

.upgrade-level {
  color: green;
  font-weight: 600;
  font-size: 16px;
}
</style> 