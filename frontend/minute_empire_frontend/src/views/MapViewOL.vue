<template>
  <v-container fluid class="map-container pa-0 ma-0" style="height: 100vh; width: 100%;">
    <!-- Error message -->
    <v-alert v-if="error" type="error" class="map-error" dismissible>
      {{ error }}
    </v-alert>
    
    <!-- Loading overlay -->
    <v-overlay :value="loading" absolute>
      <v-progress-circular indeterminate size="64" color="primary"></v-progress-circular>
      <div class="mt-4">Loading map data...</div>
    </v-overlay>

    <!-- The map container -->
    <div ref="mapContainer" class="map-wrapper"></div>
    
    <!-- Coordinates display -->
    <div class="coords-display" v-if="currentCoords">
      X: {{ currentCoords.x }}, Y: {{ currentCoords.y }}
    </div>
    
    <!-- Zoom level indicator -->
    <div class="zoom-indicator">
      Zoom: {{ zoomLevel }}
    </div>
    
    <!-- Focused Village Name -->
    <div class="focused-village-name" v-if="focusedVillage">
      {{ focusedVillage.name }}
    </div>

    <!-- Village Resources Display -->
    <village-resources-display
      :show="!!focusedVillage"
      :village="focusedVillage"
      :server-time="mapData?.server_time"
      :client-response-time="mapData?.client_response_time"
    />

    <!-- Construction Tasks Display -->
    <construction-tasks-display
      :show="!!focusedVillage"
      :tasks="focusedVillage?.construction_tasks || []"
      :villages="villages"
      :focused-village="focusedVillage"
      :server-time="mapData?.server_time"
      :client-response-time="mapData?.client_response_time"
      @task-completed="handleTaskCompleted"
    />

    <!-- Error Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      position="top"
    >
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Hover Dialog -->
    <map-hover-dialog
      :show="hoverDialog.show"
      :position="hoverDialog.position"
      :data="hoverDialog.data"
      :type="hoverDialog.type"
    >
      <template #additional-info>
        <!-- Future expansion slot for additional information -->
      </template>
    </map-hover-dialog>

    <!-- Selection Dialog -->
    <map-selection-dialog
      v-model:show="selectionDialog.show"
      :slot-id="selectionDialog.slotId"
      :type="selectionDialog.type"
      :is-empty="selectionDialog.isEmpty"
      :is-owned="selectionDialog.village ? selectionDialog.village.is_owned : false"
      :village="selectionDialog.village"
      :map-data="mapData"
      @upgrade="handleUpgrade"
      @create="handleCreate"
    >
      <template #additional-info>
        <!-- Future expansion slot for additional information -->
      </template>
    </map-selection-dialog>
  </v-container>
</template>

<script>
import apiService from '@/services/apiService';
import authService from '@/services/authService';
import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { fromLonLat, useGeographic } from 'ol/proj';
import { Feature } from 'ol';
import { Point, Polygon } from 'ol/geom';
import { Style, Fill, Stroke, Text, Circle, Icon } from 'ol/style';
import { defaults as defaultControls } from 'ol/control';
import MapHoverDialog from '@/components/MapHoverDialog.vue'
import MapSelectionDialog from '@/components/selection_dialogs/MapSelectionDialog.vue'
import VillageResourcesDisplay from '@/components/VillageResourcesDisplay.vue'
import ConstructionTasksDisplay from '@/components/ConstructionTasksDisplay.vue'
import { getResourceColor, getBuildingColor, getResourceIcon, getBuildingIcon, getResourceInfo, getBuildingInfo, TASK_TYPES } from '@/constants/gameElements';

// Set up geographic coordinates
useGeographic();

export default {
  name: 'MapViewOL',
  components: {
    MapHoverDialog,
    MapSelectionDialog,
    VillageResourcesDisplay,
    ConstructionTasksDisplay
  },
  
  data() {
    return {
      loading: true,
      error: null,
      map: null,
      mapData: null,
      mapBounds: {
        x_min: -15,
        x_max: 15,
        y_min: -15,
        y_max: 15
      },
      mapSize: 31,
      villages: [],
      currentCoords: null,
      zoomLevel: 1,
      windowWidth: window.innerWidth,
      gridLayer: null,
      villageLayer: null,
      subgridLayer: null,
      cityLayer: null,
      currentSubgridCell: null,
      currentCityCell: null,
      resourceIcons: {
        wood: new URL('@/assets/wood.svg', import.meta.url).href,
        food: new URL('@/assets/food.svg', import.meta.url).href,
        stone: new URL('@/assets/stone.svg', import.meta.url).href,
        iron: new URL('@/assets/iron.svg', import.meta.url).href
      },
      hoverDialog: {
        show: false,
        position: { x: 0, y: 0 },
        data: null,
        type: null
      },
      snackbar: {
        show: false,
        text: '',
        color: 'error',
        timeout: 3000
      },
      pointerMoveTimeout: null,
      lastPointerPosition: null,
      lastVillageCheck: null,
      styleCache: {},
      lastZoomLevel: null,
      lastUpdateTime: 0,
      updateThrottle: 100,
      selectionDialog: {
        show: false,
        slotId: null,
        type: null,
        isEmpty: true,
        village: null
      },
      lastClickEvent: null,
      focusedVillage: null,
      focusCheckTimer: null,
      villageRefreshTimer: null,
      lastVillageRefresh: 0,
      taskCompletionTimer: null,
      iconCache: {}
    };
  },
  
  computed: {
    isMobile() {
      return this.windowWidth < 600;
    }
  },
  
  async created() {
    console.log('Component created');
    if (!authService.isAuthenticated()) {
      this.$router.push('/login');
      return;
    }
    
    await this.fetchMapData();
    
    // Add window resize handler
    window.addEventListener('resize', this.handleResize);
    this.checkWindowSize();
  },
  
  mounted() {
    console.log('Component mounted');
    this.initializeMap();
    
    // Start checking for focused village
    this.startFocusCheck();
  },
  
  beforeDestroy() {
    console.log('Component beforeDestroy');
    window.removeEventListener('resize', this.handleResize);
    
    // Clear all timers
    if (this.focusCheckTimer) {
      clearInterval(this.focusCheckTimer);
    }
    
    if (this.villageRefreshTimer) {
      clearTimeout(this.villageRefreshTimer);
    }
    
    if (this.taskCompletionTimer) {
      clearTimeout(this.taskCompletionTimer);
    }
    
    if (this.map) {
      this.map.setTarget(null);
      this.map = null;
    }
  },
  
  methods: {
    startFocusCheck() {
      // Check for focused village every 500ms
      this.focusCheckTimer = setInterval(() => {
        this.checkFocusedVillage();
      }, 500);
      
      // Start village refresh timer
      this.scheduleVillageRefresh();
    },
    
    scheduleVillageRefresh() {
      // Refresh village data every 60 seconds
      this.villageRefreshTimer = setTimeout(() => {
        this.refreshFocusedVillage();
      }, 60000);
    },
    
    async refreshFocusedVillage(forceRefresh = false) {
      if (this.focusedVillage) {
        try {
          // Only refresh if it's been at least 55 seconds since last complete refresh or if forced
          const now = Date.now();
          if (forceRefresh || now - this.lastVillageRefresh > 55000) {
            console.log('Refreshing village data...');
            
            // Get fresh map data
            const data = await apiService.getMapInfo();
            this.mapData = data;
            
            // Update the villages array
            this.villages = data.villages.map(village => ({
              ...village,
              resource_fields: village.resource_fields || Array(20).fill(null)
            }));
            
            // Update the focused village with fresh data
            const updatedVillage = this.villages.find(v => v.id === this.focusedVillage.id);
            if (updatedVillage) {
              this.focusedVillage = updatedVillage;
              
              // Also update the selection dialog if it's open and related to this village
              if (this.selectionDialog.show && this.selectionDialog.village && this.selectionDialog.village.id === updatedVillage.id) {
                this.selectionDialog.village = updatedVillage;
              }
            }
            
            this.lastVillageRefresh = now;
          }
        } catch (error) {
          console.error('Error refreshing village data:', error);
        }
      }
      
      // Schedule next refresh
      this.scheduleVillageRefresh();
    },
    
    checkFocusedVillage() {
      if (!this.map) return;
      
      const zoom = this.map.getView().getZoom();
      
      // Only check for focused village if zoom is high enough
      if (zoom <= 9) {
        if (this.focusedVillage) {
          this.focusedVillage = null;
        }
        return;
      }
      
      // Get center coordinates of the viewport
      const center = this.map.getView().getCenter();
      
      // Find the closest village to the center
      let closestVillage = null;
      let minDistance = Infinity;
      
      this.villages.forEach(village => {
        if (village.is_owned) {
          const villageX = village.location.x + 0.5; // Center of the cell
          const villageY = village.location.y + 0.5;
          
          // Calculate Euclidean distance
          const distance = Math.sqrt(
            Math.pow(villageX - center[0], 2) + 
            Math.pow(villageY - center[1], 2)
          );
          
          // Update closest village if this one is closer
          if (distance < minDistance) {
            minDistance = distance;
            closestVillage = village;
          }
        }
      });
      
      // Check if the village is within 4 tiles
      if (closestVillage && minDistance <= 4) {
        // Only update if it's a different village to avoid unnecessary renders
        if (!this.focusedVillage || this.focusedVillage.id !== closestVillage.id) {
          console.log(`Focus changed to village: ${closestVillage.name}`);
          this.focusedVillage = closestVillage;
          
          // Log construction tasks for debugging
          if (this.focusedVillage.construction_tasks && this.focusedVillage.construction_tasks.length > 0) {
            console.log('Construction tasks found:', this.focusedVillage.construction_tasks);
            // Log first task's full object to see all properties
            console.log('First task details:', this.focusedVillage.construction_tasks[0]);
            // Log all property names in the first task
            console.log('First task property names:', Object.keys(this.focusedVillage.construction_tasks[0]));
          } else {
            console.log('No construction tasks for this village');
          }
          
          // Since village focus changed, update last refresh time
          this.lastVillageRefresh = Date.now();
        }
      } else if (this.focusedVillage) {
        console.log('Focus lost from village');
        this.focusedVillage = null;
      }
    },
    
    async fetchMapData() {
      try {
        console.log('Fetching map data...');
        this.loading = true;
        const data = await apiService.getMapInfo();
        
        // Set map data
        this.mapData = data;
        this.mapBounds = data.map_bounds;
        this.mapSize = data.map_size;
        
        // Ensure each village has a resource_fields array
        this.villages = data.villages.map(village => ({
          ...village,
          resource_fields: village.resource_fields || Array(20).fill(null) // Initialize with 20 null slots if not present
        }));
        
        console.log('Map data fetched:', {
          bounds: this.mapBounds,
          size: this.mapSize,
          villages: this.villages.length,
          sampleVillage: this.villages[0] // Log first village for debugging
        });
        
        return data; // Return the data to allow promise chaining
      } catch (error) {
        console.error('Error fetching map data:', error);
        this.error = 'Failed to load map data. Please try again later.';
        throw error; // Re-throw to allow error handling in promise chain
      } finally {
        this.loading = false;
      }
    },
    
    initializeMap() {
      console.log('Starting map initialization...');
      
      if (!this.$refs.mapContainer) {
        console.error('Map container not found!');
        return;
      }
      
      // Create separate layers for different features
      this.gridLayer = new VectorLayer({
        source: new VectorSource(),
        style: this.getDefaultStyle()
      });
      
      this.villageLayer = new VectorLayer({
        source: new VectorSource(),
        style: this.getDefaultStyle()
      });
      
      this.subgridLayer = new VectorLayer({
        source: new VectorSource(),
        style: this.getDefaultStyle()
      });
      
      this.cityLayer = new VectorLayer({
        source: new VectorSource(),
        style: this.getDefaultStyle()
      });
      
      // Create the map with adjusted view settings
      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [this.gridLayer, this.villageLayer, this.subgridLayer, this.cityLayer],
        view: new View({
          center: [0, 0],
          zoom: 1,
          maxZoom: 15,
          minZoom: 0.5,
          extent: [-20, -20, 20, 20],
          multiWorld: false
        }),
        controls: defaultControls({
          zoom: true,
          rotate: false,
          attribution: false
        })
      });
      
      // Add event listeners
      this.map.on('pointermove', this.handlePointerMove);
      this.map.on('click', this.handleMapClick);
      this.map.on('moveend', this.handleMoveEnd);
      
      // Draw the initial grid
      this.drawGrid();
      
      // Force a redraw
      this.map.updateSize();
    },
    
    drawGrid() {
      if (!this.map) return;
      
      // Clear all layers
      this.gridLayer.getSource().clear();
      this.villageLayer.getSource().clear();
      this.subgridLayer.getSource().clear();
      this.cityLayer.getSource().clear();
      
      // Draw the main grid
      for (let x = this.mapBounds.x_min; x <= this.mapBounds.x_max; x++) {
        for (let y = this.mapBounds.y_min; y <= this.mapBounds.y_max; y++) {
          this.drawGridCell(x, y);
        }
      }
      
      // Draw villages
      this.villages.forEach(village => {
        this.drawVillage(village);
      });
      
      // Update subgrids and city grids based on zoom level
      this.updateSubgrids();
    },
    
    drawGridCell(x, y) {
      const coordinates = [
        [x, y],
        [x + 1, y],
        [x + 1, y + 1],
        [x, y + 1],
        [x, y]
      ];
      
      const cellFeature = new Feature({
        geometry: new Polygon([coordinates]),
        type: 'grid_cell',
        x: x,
        y: y
      });
      
      cellFeature.setStyle(new Style({
        fill: new Fill({
          color: 'rgba(255, 255, 255, 0.3)'
        }),
        stroke: new Stroke({
          color: '#000000',
          width: 1
        })
      }));
      
      this.gridLayer.getSource().addFeature(cellFeature);
    },
    
    drawVillage(village) {
      const villageFeature = new Feature({
        geometry: new Point([village.location.x + 0.5, village.location.y + 0.5]),
        type: 'village',
        village: village
      });
      
      villageFeature.setStyle(new Style({
        image: new Circle({
          radius: 8,
          fill: new Fill({
            color: village.is_owned ? 'rgba(76, 175, 80, 0.8)' : 'rgba(244, 67, 54, 0.8)'
          }),
          stroke: new Stroke({
            color: village.is_owned ? '#4CAF50' : '#F44336',
            width: 2
          })
        }),
        text: new Text({
          text: village.name,
          offsetY: -12,
          fill: new Fill({
            color: '#000'
          }),
          stroke: new Stroke({
            color: '#fff',
            width: 3
          })
        })
      }));
      
      this.villageLayer.getSource().addFeature(villageFeature);
    },
    
    updateSubgrids() {
      const now = Date.now();
      if (now - this.lastUpdateTime < this.updateThrottle) {
        return;
      }
      this.lastUpdateTime = now;

      const zoom = this.map.getView().getZoom();
      const cellSize = this.calculateCellSize();
      
      // Only update if zoom level has changed significantly
      // DO NOT DELET THIS COMMENT
      // if (this.lastZoomLevel && Math.abs(zoom - this.lastZoomLevel) < 0.5) {
      //   return;
      // }
      this.lastZoomLevel = zoom;

      // Clear all layers first
      this.subgridLayer.getSource().clear();
      this.cityLayer.getSource().clear();
      
      // Only draw subgrids if zoom level is appropriate
      if (zoom > 3) {
        this.villages.forEach(village => {
          this.drawVillageSubgrid(village, cellSize);
        });
      }
      
      // Only draw city grid if zoom level is appropriate
      if (zoom > 3) {
        this.villages.forEach(village => {
          this.drawCityGrid(village);
        });
      }
    },
    
    calculateCellSize() {
      // Get the view's resolution (meters per pixel)
      const resolution = this.map.getView().getResolution();
      // Get the viewport size in pixels
      const viewportSize = this.map.getSize();
      // Calculate the size of a subgrid cell (0.2 units) in pixels
      const size = (0.2 * viewportSize[0]) / (this.mapBounds.x_max - this.mapBounds.x_min + 1);
      return size;
    },
    
    drawVillageSubgrid(village, cellSize) {
      const x = village.location.x;
      const y = village.location.y;
      const zoom = this.map.getView().getZoom();
      
      // Only draw subgrids if zoom level is appropriate
      if (zoom <= 3) return;
      
      for (let sx = 0; sx < 5; sx++) {
        for (let sy = 0; sy < 5; sy++) {
          const isCurrentCell = this.currentSubgridCell && 
            this.currentSubgridCell.village === village &&
            this.currentSubgridCell.x === sx &&
            this.currentSubgridCell.y === sy;

          const subgridFeature = new Feature({
            geometry: new Polygon([[
              [x + sx * 0.2, y + sy * 0.2],
              [x + (sx + 1) * 0.2, y + sy * 0.2],
              [x + (sx + 1) * 0.2, y + (sy + 1) * 0.2],
              [x + sx * 0.2, y + (sy + 1) * 0.2],
              [x + sx * 0.2, y + sy * 0.2]
            ]]),
            type: 'subgrid',
            village: village,
            subgridX: sx,
            subgridY: sy
          });
          
          // Get the slot number and resource field
          const slotNumber = this.getSlotFromPosition(sx, sy);
          const resourceField = village.resource_fields?.find(field => field && field.slot === slotNumber);
          
          // Create base style with dynamic opacity based on zoom
          const baseOpacity = Math.min(1, (zoom - 2) / 2); // Fade in between zoom 2-4
          const baseStyle = new Style({
            fill: new Fill({
              color: this.getSubgridColor(sx, sy, village, baseOpacity)
            }),
            stroke: new Stroke({
              color: isCurrentCell ? 'rgba(0, 0, 0, 0.8)' : 'rgba(0, 0, 0, 0.5)',
              width: isCurrentCell ? 2 : 0.5
            })
          });
          
          subgridFeature.setStyle(baseStyle);
          this.subgridLayer.getSource().addFeature(subgridFeature);
          
          // Check for creation task on empty slots
          const creationTask = this.focusedVillage && 
            this.focusedVillage.construction_tasks && 
            slotNumber !== null &&
            this.focusedVillage.construction_tasks.find(task => 
              task.task_type === 'create_field' && 
              Number(task.slot) === slotNumber);
              
          // Only show resource details at higher zoom levels
          if (zoom > 3 && (resourceField || creationTask)) {
            const detailOpacity = Math.min(1, (zoom - 3) / 2); // Fade in between zoom 3-5
            
            // If there's a resource field, use it; otherwise create a dummy one for creation task
            const fieldToDisplay = resourceField || {
              slot: slotNumber,
              level: 0,
              type: creationTask ? creationTask.target_type : 'unknown'
            };
            
            // Create a more professional visual style for resource fields
            const resourceStyle = this.createResourceFieldStyle(fieldToDisplay, x + sx * 0.2, y + sy * 0.2, detailOpacity);
            
            // Add resource field details as separate features
            const resourceFeature = new Feature({
              geometry: new Point([
                x + sx * 0.2 + 0.1,
                y + sy * 0.2 + 0.1
              ]),
              type: 'resource_field',
              resource: fieldToDisplay
            });
            
            if (resourceStyle) {
              resourceFeature.setStyle(resourceStyle);
              this.subgridLayer.getSource().addFeature(resourceFeature);
            }
          }
        }
      }
    },
    
    createIconDataURL(iconName, size = 24, color = '#ffffff') {
      // Create a unique cache key based on icon, size and color
      const cacheKey = `${iconName}_${size}_${color}`;
      
      // Return from cache if exists
      if (this.iconCache[cacheKey]) {
        return this.iconCache[cacheKey];
      }
      
      // Create canvas element
      const canvas = document.createElement('canvas');
      const padding = 4; // Padding around the icon
      canvas.width = size + padding * 2;
      canvas.height = size + padding * 2;
      const ctx = canvas.getContext('2d');
      
      // Set up temporary div to measure icon dimensions
      const tempDiv = document.createElement('div');
      tempDiv.style.position = 'absolute';
      tempDiv.style.visibility = 'hidden';
      tempDiv.style.fontSize = `${size}px`;
      
      // Create icon element
      const iconElement = document.createElement('i');
      iconElement.className = `mdi ${iconName}`;
      iconElement.style.color = color;
      iconElement.style.fontSize = `${size}px`;
      
      // Add to DOM temporarily to get measurements
      tempDiv.appendChild(iconElement);
      document.body.appendChild(tempDiv);
      
      // Get material design icon content
      const iconStyle = window.getComputedStyle(iconElement, ':before');
      const iconContent = iconStyle.getPropertyValue('content').replace(/"/g, '');
      const iconFont = iconStyle.getPropertyValue('font-family');
      
      // Set up canvas context
      ctx.font = `${size}px ${iconFont}`;
      ctx.fillStyle = color;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Draw icon on canvas
      ctx.fillText(iconContent, canvas.width / 2, canvas.height / 2);
      
      // Clean up
      document.body.removeChild(tempDiv);
      
      // Convert canvas to data URL
      const dataURL = canvas.toDataURL('image/png');
      
      // Cache the result
      this.iconCache[cacheKey] = dataURL;
      
      return dataURL;
    },
    
    createResourceFieldStyle(resourceField, x, y, opacity) {


      const baseSize = 11;
      const level = resourceField.level;
      const zoom = this.map.getView().getZoom();

      if (zoom > 9) {
        // Check for field upgrades - ensure we're comparing numbers
        const upgradeTask = this.focusedVillage && 
          this.focusedVillage.construction_tasks && 
          this.focusedVillage.construction_tasks.find(task => 
            task.task_type === 'upgrade_field' && 
            Number(task.slot) === Number(resourceField.slot));
            
        // Check for field creation - ensure we're comparing numbers
        const creationTask = this.focusedVillage && 
          this.focusedVillage.construction_tasks && 
          this.focusedVillage.construction_tasks.find(task => 
            task.task_type === 'create_field' && 
            Number(task.slot) === Number(resourceField.slot));
            
        const cacheKey = `resource_${resourceField.type}_${resourceField.level}_${opacity}_${upgradeTask ? 'upgrade' : creationTask ? 'create' : 'normal'}`;
        if (this.styleCache[cacheKey] !== undefined) {
          return this.styleCache[cacheKey];
        }
        // Get resource icon name and colors
        const iconName = getResourceIcon(resourceField.type);
        const circleColor = this.getResourceColor(resourceField.type, 0.8);
        

        
        let displayIconName;
        let iconColor;
        
        if (upgradeTask) {
          // For upgrades: use green up arrow
          displayIconName = 'mdi-arrow-up-bold';
          iconColor = 'rgba(0, 0, 0, 0.3)'; // Green for upgrades
        } else if (creationTask) {
          // For creation: use shovel/hammer icon from TASK_TYPES
          displayIconName = TASK_TYPES.CREATE_FIELD.icon;
          iconColor = 'rgba(0, 0, 0, 0.3)';
        } else {
          // Normal resource icon
          displayIconName = iconName;
          iconColor = 'rgba(0, 0, 0, 0.3)';
        }
        
        // Larger icon size for better visibility of task icons
        const iconSize = (upgradeTask || creationTask) ? 32 : Math.min(12 + level * 2, 28);
        
        // Debug log
        if (upgradeTask || creationTask) {
          console.log(`Found ${upgradeTask ? 'upgrading' : 'creating'} field at slot ${resourceField.slot}`);
        }
        
        try {
          // Create icon data URL
          const iconDataURL = this.createIconDataURL(displayIconName, iconSize, iconColor);
          
          // Create style with both circle and icon
          const style = new Style({
            image: new Circle({
              radius: (upgradeTask || creationTask) ? baseSize * 2 : (baseSize + level*2),
              fill: new Fill({
                color: circleColor
              })
              // DO NOT REMOVE
              // stroke: new Stroke({
              //   color: (upgradeTask || creationTask) ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.5)',
              //   width: (upgradeTask || creationTask) ? 0 : 0
              // })
            })
          });
          
          // Add icon on top of circle
          const iconStyle = new Style({
            image: new Icon({
              src: iconDataURL,
              scale: 1,
              opacity: 1
            })
          });
          
          this.styleCache[cacheKey] = [style, iconStyle];
          return [style, iconStyle];
        } catch (error) {
          console.error('Error creating resource field style:', error);
          
          // Fallback to text style if icon creation fails
          const style = new Style({
            image: new Circle({
              radius: baseSize * 1.5,
              fill: new Fill({
                color: circleColor
              }),
              stroke: new Stroke({
                color: (upgradeTask || creationTask) ? 'rgba(76, 175, 80, 0.8)' : 'rgba(0, 0, 0, 0.5)',
                width: 2
              })
            }),
            text: new Text({
              text: resourceField.level.toString(),
              fill: new Fill({
                color: 'rgba(255, 255, 255, 0.9)'
              }),
              stroke: new Stroke({
                color: 'rgba(0, 0, 0, 0.8)',
                width: 1
              }),
              scale: [2, 2],
              offsetY: 0
            })
          });
          
          this.styleCache[cacheKey] = style;
          return style;
        }
      }
      return null;
    },

    getResourceColor(type, opacity) {
      return getResourceColor(type, opacity);
    },

    getSubgridColor(sx, sy, village, opacity) {
      // If it's not the player's village, use the owner's color
      if (!village.is_owned) {
        // Skip top corners and center
        if ((sx === 0 && sy === 0) || (sx === 4 && sy === 0) || 
            (sx === 0 && sy === 4) || (sx === 4 && sy === 4)) {
          // For corners, use transparent
          return 'rgba(255, 255, 255, 0)';
        }
        // For main slots, use a lighter version of the user's color
        const hex = village.user_info.color;
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, 0.9)`;
      }

      // Skip top corners and center
      if ((sx === 0 && sy === 0) || (sx === 4 && sy === 0) || 
          (sx === 0 && sy === 4) || (sx === 4 && sy === 4) || (sx === 2 && sy === 2)) {
        return 'rgba(255, 255, 255, 0)';
      }

      // Calculate slot number based on spiral pattern
      const slotNumber = this.getSlotFromPosition(sx, sy);
      
      // If resource_fields array doesn't exist or slot is invalid, return default color
      if (!village.resource_fields || !Array.isArray(village.resource_fields) || slotNumber === null || slotNumber === undefined) {
        return `rgba(255, 255, 255, ${opacity * 0.2})`;
      }
      
      // Find the resource field for this slot
      const resourceField = village.resource_fields.find(field => field && field.slot === slotNumber);
      if (!resourceField) {
        return `rgba(255, 255, 255, ${opacity * 0.2})`;
      }
      
      // Return color based on resource type with opacity
      return this.getResourceColor(resourceField.type, opacity * 0.6);
    },

    getSlotFromPosition(sx, sy) {
      // Define spiral pattern mapping
      const spiralPattern = [
        [null,  8,    9,    10,   null],
        [19,    7,    0,     1,     11],
        [18,    6,   null,   2,     12],
        [17,    5,    4,     3,     13],
        [null, 16,   15,    14,   null]
      ];
      
      return spiralPattern[sy][sx];
    },

    getCitySlotFromPosition(cx, cy) {
      // Define spiral pattern mapping for city buildings
      // Buildings spiral outward from the center
      const cityPattern = [
        [22,  10,    11,     12,    23],
        [21,    9,    2,     3,     13],
        [20,    8,    1,     4,     14],
        [19,    7,    6,     5,     15],
        [25,  18,    17,     16,    24]
      ];
      
      // Add bounds checking
      if (cy < 0 || cy >= cityPattern.length || cx < 0 || cx >= cityPattern[0].length) {
        return null;
      }
      
      return cityPattern[cy][cx];
    },

    drawCityGrid(village) {
      const x = village.location.x + 0.4;
      const y = village.location.y + 0.4;
      const zoom = this.map.getView().getZoom();
      
      // DO NOT REMOVE THIS COMMENT
      // // Only show city grid at high zoom levels
      // if (zoom <= 7){
      //   return;
      // }
      const cityOpacity = 1;
      
      for (let cx = 0; cx < 5; cx++) {
        for (let cy = 0; cy < 5; cy++) {
          const isCurrentCell = this.currentCityCell && 
            this.currentCityCell.village === village &&
            this.currentCityCell.x === cx &&
            this.currentCityCell.y === cy;

          const cityFeature = new Feature({
            geometry: new Polygon([[
              [x + cx * 0.04, y + cy * 0.04],
              [x + (cx + 1) * 0.04, y + cy * 0.04],
              [x + (cx + 1) * 0.04, y + (cy + 1) * 0.04],
              [x + cx * 0.04, y + (cy + 1) * 0.04],
              [x + cx * 0.04, y + cy * 0.04]
            ]]),
            type: 'city_grid',
            village: village,
            cityX: cx,
            cityY: cy
          });
          
          cityFeature.setStyle(new Style({
            fill: new Fill({
              color: this.getCityGridColor(cx, cy, village, cityOpacity)
            }),
            stroke: new Stroke({
              color: isCurrentCell ? 'rgba(0, 0, 0, 0.8)' : 'rgba(0, 0, 0, 0.5)',
              width: isCurrentCell ? 2 : 0.5
            })
          }));
          
          this.cityLayer.getSource().addFeature(cityFeature);

          // Get the slot number for this position
          const slot = this.getCitySlotFromPosition(cx, cy);
          
          // Check for construction in this slot
          const construction = village.city?.constructions?.find(c => c.slot === slot);
          
          // Check for building creation task on empty slots
          const creationTask = this.focusedVillage && 
            this.focusedVillage.construction_tasks && 
            slot !== null &&
            this.focusedVillage.construction_tasks.find(task => 
              task.task_type === 'create_building' && 
              Number(task.slot) === slot);

          // Add building details if there's a construction or creation task
          if (slot !== null && (construction || creationTask)) {
            // If there's a building, use it; otherwise create a dummy one for creation task
            const buildingToDisplay = construction || {
              slot: slot,
              level: 0,
              type: creationTask ? creationTask.target_type : 'unknown'
            };
            
            const buildingStyle = this.createBuildingStyle(buildingToDisplay, x + cx * 0.04, y + cy * 0.04, cityOpacity);
            if (buildingStyle) {
              const buildingFeature = new Feature({
                geometry: new Point([
                  x + cx * 0.04 + 0.02,
                  y + cy * 0.04 + 0.02
                ]),
                type: 'building',
                building: buildingToDisplay
              });
              buildingFeature.setStyle(buildingStyle);
              this.cityLayer.getSource().addFeature(buildingFeature);
            }
          }
        }
      }
    },

    getCityGridColor(cx, cy, village, opacity) {
      // If it's not the player's village, show everything in black
      if (!village.is_owned) {
        return `rgba(0, 0, 0, ${opacity * 0.4})`; // Black for enemy cities
      }

      // Check if city data exists
      if (!village.city) {
        return `rgba(255, 255, 255, ${opacity * 0.2})`; // Default color if no city data
      }

      // Get the slot number from the position
      const slot = this.getCitySlotFromPosition(cx, cy);
      
      // If no slot is assigned to this position, return transparent
      if (slot === null) {
        return `rgba(255, 255, 255, ${opacity * 0.2})`;
      }

      // Check if there's a construction in this slot
      const construction = village.city.constructions.find(c => c.slot === slot);
      if (construction) {
        return this.getBuildingColor(construction.type, opacity * 0.7);
      }

      // Empty buildable slots
      return `rgba(255, 255, 255, ${opacity * 0.2})`;
    },
    
    handlePointerMove(event) {
      // Debounce the pointer move handler
      if (this.pointerMoveTimeout) {
        clearTimeout(this.pointerMoveTimeout);
      }

      this.pointerMoveTimeout = setTimeout(() => {
        const coords = this.map.getEventCoordinate(event.originalEvent);
        const pixel = this.map.getEventPixel(event.originalEvent);
        
        // Convert coordinates to grid position with floating point precision
        const gridX = Math.round(coords[0] * 100) / 100;
        const gridY = Math.round(coords[1] * 100) / 100;
        
        // Only update if coordinates are within bounds and have changed
        if (gridX >= this.mapBounds.x_min && gridX <= this.mapBounds.x_max &&
            gridY >= this.mapBounds.y_min && gridY <= this.mapBounds.y_max &&
            (!this.lastPointerPosition || 
             this.lastPointerPosition.x !== gridX || 
             this.lastPointerPosition.y !== gridY)) {
          
          this.lastPointerPosition = { x: gridX, y: gridY };
          this.currentCoords = { x: gridX, y: gridY };

          // Find the village at the current position using cached positions
          const village = this.findVillageAtPosition(gridX, gridY);

          if (village) {
            if (!village.is_owned) {
              // For enemy villages, just show the village info
              this.showHoverDialog(pixel, village, 'village');
              this.currentSubgridCell = null;
              this.currentCityCell = null;
            } else {
              // For owned villages, calculate positions and show resource/building info
              const positions = this.calculatePositions(gridX, gridY, village);
              
              // Update current cells only if they've changed
              if (this.shouldUpdateCells(positions)) {
                this.currentSubgridCell = positions.subgrid;
                this.currentCityCell = positions.city;
                this.updateHoverDialog(pixel, positions, village);
                this.updateSubgrids();
              }
            }
          } else {
            // Clear highlighting if not over a village
            this.clearHighlighting();
          }
        }
      }, 16); // ~60fps
    },
    
    findVillageAtPosition(gridX, gridY) {
      // Always search in the current villages data to get most up-to-date results
      return this.villages.find(v => 
        Math.floor(gridX) === v.location.x && 
        Math.floor(gridY) === v.location.y
      );
    },

    calculatePositions(gridX, gridY, village) {
      const subgridX = Math.floor((gridX - village.location.x) * 5);
      const subgridY = Math.floor((gridY - village.location.y) * 5);
      const cityX = Math.floor((gridX - (village.location.x + 0.4)) * 25);
      const cityY = Math.floor((gridY - (village.location.y + 0.4)) * 25);

      return {
        subgrid: { village, x: subgridX, y: subgridY },
        city: { village, x: cityX, y: cityY }
      };
    },

    shouldUpdateCells(positions) {
      return !this.currentSubgridCell || 
             !this.currentCityCell ||
             this.currentSubgridCell.village !== positions.subgrid.village ||
             this.currentSubgridCell.x !== positions.subgrid.x ||
             this.currentSubgridCell.y !== positions.subgrid.y ||
             this.currentCityCell.village !== positions.city.village ||
             this.currentCityCell.x !== positions.city.x ||
             this.currentCityCell.y !== positions.city.y;
    },

    updateHoverDialog(pixel, positions, village) {
      const { subgrid, city } = positions;
      const zoom = this.map.getView().getZoom();

      // Check for resource field or building at current position
      const slot = this.getSlotFromPosition(subgrid.x, subgrid.y);
      const resourceField = village.resource_fields?.find(field => field && field.slot === slot);
      
      if (resourceField && zoom > 8) {
        this.showHoverDialog(pixel, {
          type: resourceField.type,
          slot: resourceField.slot,
          level: resourceField.level,
          isEmpty: false
        }, 'resource');
      } else if (slot !== null && zoom > 8) {
        this.showHoverDialog(pixel, {
          slot: slot,
          isEmpty: true
        }, 'resource');
      } else if (village.city && village.city.constructions) {
        const citySlot = this.getCitySlotFromPosition(city.x, city.y);
        const construction = village.city.constructions.find(c => c.slot === citySlot);
        
        if (construction && zoom > 10) {
          this.showHoverDialog(pixel, {
            type: construction.type,
            slot: construction.slot,
            level: construction.level,
            isEmpty: false
          }, 'building');
        } else if (citySlot !== null && zoom > 10) {
          this.showHoverDialog(pixel, {
            slot: citySlot,
            isEmpty: true
          }, 'building');
        } else {
          this.hideHoverDialog();
        }
      } else {
        this.hideHoverDialog();
      }
    },

    clearHighlighting() {
      this.currentSubgridCell = null;
      this.currentCityCell = null;
      this.hideHoverDialog();
      this.updateSubgrids();
    },
    
    handleMapClick(event) {
      // Store the click event for use in handleUpgrade
      this.lastClickEvent = event.originalEvent;
      
      const coords = this.map.getEventCoordinate(event.originalEvent);
      const pixel = this.map.getEventPixel(event.originalEvent);
      
      // Convert coordinates to grid position with floating point precision
      const gridX = Math.round(coords[0] * 100) / 100;
      const gridY = Math.round(coords[1] * 100) / 100;
      
      // Only update if coordinates are within bounds
      if (gridX >= this.mapBounds.x_min && gridX <= this.mapBounds.x_max &&
          gridY >= this.mapBounds.y_min && gridY <= this.mapBounds.y_max) {
        
        // Find the village at the current position
        const village = this.findVillageAtPosition(gridX, gridY);

        if (village && village.is_owned) {
          // Calculate subgrid and city positions
          const positions = this.calculatePositions(gridX, gridY, village);
          const { subgrid, city } = positions;
          const zoom = this.map.getView().getZoom();

          // Check for resource field or building at current position
          const slot = this.getSlotFromPosition(subgrid.x, subgrid.y);
          const resourceField = village.resource_fields?.find(field => field && field.slot === slot);
          
          // Check if the click is on a city building
          const citySlot = this.getCitySlotFromPosition(city.x, city.y);
          const construction = village.city?.constructions?.find(c => c && c.slot === citySlot);
          
          // Show building dialog if we're zoomed in enough and clicked on a valid building slot
          if (zoom > 10 && citySlot !== null) {
            this.showSelectionDialog(construction, 'building', village, citySlot);
          } else if (slot !== null) {
            // Otherwise show resource field dialog (either existing or empty)
            this.showSelectionDialog(resourceField, 'resource', village, slot);
          }
        }
      }
    },
    
    handleMoveEnd() {
      this.zoomLevel = this.map.getView().getZoom().toFixed(2);
      this.clearStyleCache(); // Clear style cache when zoom level changes
      this.updateSubgrids();
      
      // Check for focused village after the map finishes moving
      this.checkFocusedVillage();
    },
    
    zoomIn() {
      const view = this.map.getView();
      const currentZoom = view.getZoom();
      view.animate({
        zoom: currentZoom + 1,
        duration: 250
      });
    },
    
    zoomOut() {
      const view = this.map.getView();
      const currentZoom = view.getZoom();
      view.animate({
        zoom: currentZoom - 1,
        duration: 250
      });
    },
    
    resetView() {
      if (this.map) {
        const view = this.map.getView();
        view.animate({
          center: [0, 0],
          zoom: 1,
          duration: 500
        });
      }
    },
    
    handleResize() {
      this.checkWindowSize();
      if (this.map) {
        this.map.updateSize();
      }
    },
    
    checkWindowSize() {
      this.windowWidth = window.innerWidth;
    },
    
    getDefaultStyle() {
      return new Style({
        fill: new Fill({
          color: 'rgba(255, 255, 255, 0.3)'
        }),
        stroke: new Stroke({
          color: '#000000',
          width: 2
        })
      });
    },

    createBuildingStyle(building, x, y, opacity) {
      const baseSize = 11;
      const zoom = this.map.getView().getZoom();

      if (zoom > 11) {
        // Check for building upgrades
        const upgradeTask = this.focusedVillage && 
          this.focusedVillage.construction_tasks && 
          this.focusedVillage.construction_tasks.find(task => 
            task.task_type === 'upgrade_building' && 
            Number(task.slot) === Number(building.slot));
            
        // Check for building creation
        const creationTask = this.focusedVillage && 
          this.focusedVillage.construction_tasks && 
          this.focusedVillage.construction_tasks.find(task => 
            task.task_type === 'create_building' && 
            Number(task.slot) === Number(building.slot));
            
        const cacheKey = `building_${building.type}_${building.level}_${opacity}_${upgradeTask ? 'upgrade' : creationTask ? 'create' : 'normal'}`;
        if (this.styleCache[cacheKey] !== undefined) {
          return this.styleCache[cacheKey];
        }

        // Get building icon name and colors
        const iconName = getBuildingIcon(building.type);
        const circleColor = this.getBuildingColor(building.type, 0.6);
        
        let displayIconName;
        let iconColor;
        
        if (upgradeTask) {
          // For upgrades: use green up arrow
          displayIconName = 'mdi-arrow-up-bold';
          iconColor = 'rgba(0, 0, 0, 0.3)'; // Green for upgrades
        } else if (creationTask) {
          // For creation: use hammer icon from TASK_TYPES
          displayIconName = TASK_TYPES.CREATE_BUILDING.icon;
          
          // Use the color of the building type being created
          const buildingInfo = getBuildingInfo(building.type);
          iconColor = buildingInfo ? buildingInfo.color : 'rgba(0, 0, 0, 0.3)'; // Blue as fallback
        } else {
          // Normal building icon
          displayIconName = iconName;
          iconColor = 'rgba(0, 0, 0, 0.6)';
        }
        
        // Larger icon size for better visibility
        const iconSize = (upgradeTask || creationTask) ? 32 : Math.min(14 + building.level, 24);
        
        // Debug log
        if (upgradeTask || creationTask) {
          console.log(`Found ${upgradeTask ? 'upgrading' : 'creating'} building at slot ${building.slot}`);
        }
        
        try {
          // Create icon data URL
          const iconDataURL = this.createIconDataURL(displayIconName, iconSize, iconColor);
          
          // Create style with both circle and icon
          const style = new Style({
            image: new Circle({
              radius: (upgradeTask || creationTask) ? baseSize * 2 : (baseSize + building.level*2),
              fill: new Fill({
                color: circleColor
              }),
              // DO NOT REMOVE
              // stroke: new Stroke({
              //   color: (upgradeTask || creationTask) ? 'rgba(76, 175, 80, 0.9)' : 'rgba(0, 0, 0, 0.5)',
              //   width: (upgradeTask || creationTask) ? 3 : 2
              // })
            })
          });
          
          // Add icon on top of circle
          const iconStyle = new Style({
            image: new Icon({
              src: iconDataURL,
              scale: 1,
              opacity: 1
            })
          });
          
          this.styleCache[cacheKey] = [style, iconStyle];
          return [style, iconStyle];
        } catch (error) {
          console.error('Error creating building style:', error);
          
          // Fallback to text style if icon creation fails
          const style = new Style({
            image: new Circle({
              radius: baseSize * 1.5,
              fill: new Fill({
                color: circleColor
              }),
              stroke: new Stroke({
                color: (upgradeTask || creationTask) ? 'rgba(76, 175, 80, 0.8)' : 'rgba(0, 0, 0, 0.5)',
                width: 2
              })
            }),
            text: new Text({
              text: building.level.toString(),
              fill: new Fill({
                color: 'rgba(255, 255, 255, 0.9)'
              }),
              stroke: new Stroke({
                color: 'rgba(0, 0, 0, 0.8)',
                width: 1
              }),
              scale: [2, 2],
              offsetY: 0
            })
          });
          
          this.styleCache[cacheKey] = style;
          return style;
        }
      }
      return null;
    },

    getBuildingColor(type, opacity) {
      return getBuildingColor(type, opacity);
    },

    getBuildingIcon(type) {
      return getBuildingIcon(type);
    },

    showHoverDialog(pixel, data, type) {
      this.hoverDialog = {
        show: true,
        position: {
          x: pixel[0] + 10, // Offset from cursor
          y: pixel[1] + 10
        },
        data,
        type
      };
    },

    hideHoverDialog() {
      this.hoverDialog.show = false;
    },

    clearStyleCache() {
      this.styleCache = {};
    },

    async showSelectionDialog(object, type, village, slotId) {
      try {
        // Fetch fresh map data
        const data = await apiService.getMapInfo();
        
        // Update the villages array with fresh data
        this.villages = data.villages.map(v => ({
          ...v,
          resource_fields: v.resource_fields || Array(20).fill(null)
        }));
        
        // Find the most up-to-date village data
        const updatedVillage = this.villages.find(v => v.id === village.id) || village;
        
        // Show the dialog with fresh data
        this.selectionDialog = {
          show: true,
          slotId: object?.slot || slotId,
          type,
          isEmpty: !object,
          village: updatedVillage
        };
      } catch (error) {
        console.error('Error fetching fresh village data:', error);
        this.showMessage('Failed to load village data', 'error');
      }
    },

    handleUpgrade(data) {
      this.handleConstructionAction(data, 'upgrade');
    },
    
    handleCreate(data) {
      this.handleConstructionAction(data, 'create');
    },
    
    handleConstructionAction(data, actionType) {
      // Use the focused village
      if (!this.focusedVillage) {
        console.error('No focused village available for construction action');
        this.showMessage('No village selected', 'error');
        return;
      }
      
      // Make sure the village is owned by the player
      if (!this.focusedVillage.is_owned) {
        console.error('Cannot perform action on village not owned by player');
        this.showMessage('You do not own this village', 'error');
        return;
      }

      // Format the command based on action type and element type
      let command;
      const { type, item_category, slot, buildingType } = data;
      
      if (actionType === 'upgrade') {
        // Use item_category to determine if it's a field or building
        if (item_category === 'resource') {
          command = `upgrade field in ${slot}`;
        } else {
          command = `upgrade building in ${slot}`;
        }
      } else if (actionType === 'create') {
        if (type === 'resource') {
          command = `create ${buildingType} field in ${slot}`;
        } else {
          command = `create ${buildingType} building in ${slot}`;
        }
      }
      
      // Execute the command
      apiService.executeCommand(this.focusedVillage.id, command)
        .then(response => {
          // Check if the command was successful
          if (response && response.success === false) {
            const errorMessage = response.message || `Failed to ${actionType}: ${command}`;
            this.showMessage(errorMessage, 'error');
            return;
          }
          
          // Show success message
          this.showMessage(`${actionType === 'upgrade' ? 'Upgrading' : 'Creating'} started!`, 'success');
          
          // Make sure the dialog is closed
          this.selectionDialog.show = false;
          
          // Immediately fetch fresh data and update the focused village
          this.fetchMapData().then(data => {
            // Update the villages array with fresh data
            this.villages = data.villages.map(village => ({
              ...village,
              resource_fields: village.resource_fields || Array(20).fill(null)
            }));
            
            // Update the focused village with fresh data
            const updatedVillage = this.villages.find(v => v.id === this.focusedVillage.id);
            if (updatedVillage) {
              // Create a new object to ensure Vue reactivity
              this.focusedVillage = {
                ...updatedVillage,
                resources: updatedVillage.resources || this.focusedVillage.resources // Preserve resources if not in update
              };
            }
            
            // Update last refresh time
            this.lastVillageRefresh = Date.now();
          });
          
        })
        .catch(error => {
          console.error(`Failed to execute ${actionType} command:`, error);
          this.showMessage(`Error: ${error.message || 'Failed to execute command'}`, 'error');
        });
    },

    showMessage(text, color = 'info') {
      this.snackbar = {
        show: true,
        text,
        color,
        timeout: color === 'error' ? 5000 : 3000  // Show errors longer
      };
    },

    handleTaskCompleted(task) {
      console.log('Task completed:', task);
      
      // Wait 1 second before refreshing the village data
      if (this.taskCompletionTimer) {
        clearTimeout(this.taskCompletionTimer);
      }
      
      this.taskCompletionTimer = setTimeout(() => {
        console.log('Refreshing village data after task completion');
        if (this.focusedVillage) {
          this.refreshFocusedVillage(true); // Force refresh
        }
      }, 1000);
    }
  }
};
</script>

<style scoped>
.map-container {
  position: relative;
  overflow: hidden;
}

.map-wrapper {
  width: 100%;
  height: 100%;
  background-color: #e9e2d0;
}

.map-error {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  max-width: 80%;
}

.coords-display {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.zoom-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.focused-village-name {
  position: absolute;
  top: 50px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(255, 255, 255, 0.9);
  color: #333;
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 14px;
  font-weight: 500;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 600px) {
  .coords-display {
    top: 10px;
    left: 10px;
    font-size: 12px;
    padding: 4px 8px;
  }
  
  .focused-village-name {
    font-size: 12px;
    padding: 3px 8px;
    top: 45px;
    max-width: 180px;
  }
}

.map-controls {
  display: none; /* Hide the controls instead of removing them entirely */
}
</style> 