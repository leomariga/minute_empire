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
    
    <!-- Mobile-friendly controls -->
    <div class="map-controls">
      <v-btn fab small color="primary" class="mb-2" @click="zoomIn" aria-label="Zoom in">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <v-btn fab small color="primary" class="mb-2" @click="zoomOut" aria-label="Zoom out">
        <v-icon>mdi-minus</v-icon>
      </v-btn>
      <v-btn fab small color="primary" @click="resetView" aria-label="Reset view">
        <v-icon>mdi-home</v-icon>
      </v-btn>
    </div>

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
      :data="selectionDialog.data"
      :type="selectionDialog.type"
      @upgrade="handleUpgrade"
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
import MapSelectionDialog from '@/components/MapSelectionDialog.vue'

// Set up geographic coordinates
useGeographic();

export default {
  name: 'MapViewOL',
  components: {
    MapHoverDialog,
    MapSelectionDialog
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
      pointerMoveTimeout: null,
      lastPointerPosition: null,
      lastVillageCheck: null,
      cachedVillagePositions: {},
      styleCache: {},
      lastZoomLevel: null,
      lastUpdateTime: 0,
      updateThrottle: 100,
      selectionDialog: {
        show: false,
        data: null,
        type: null
      },
      lastClickEvent: null
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
  },
  
  beforeDestroy() {
    console.log('Component beforeDestroy');
    window.removeEventListener('resize', this.handleResize);
    if (this.map) {
      this.map.setTarget(null);
      this.map = null;
    }
  },
  
  methods: {
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
        
        // Center the map
        this.resetView();
      } catch (error) {
        console.error('Error fetching map data:', error);
        this.error = 'Failed to load map data. Please try again later.';
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
          
          // Only show resource details at higher zoom levels
          if (resourceField && zoom > 3) {
            const detailOpacity = Math.min(1, (zoom - 3) / 2); // Fade in between zoom 3-5
            
            // Create a more professional visual style for resource fields
            const resourceStyle = this.createResourceFieldStyle(resourceField, x + sx * 0.2, y + sy * 0.2, detailOpacity);
            
            // Add resource field details as separate features
            const resourceFeature = new Feature({
              geometry: new Point([
                x + sx * 0.2 + 0.1,
                y + sy * 0.2 + 0.1
              ]),
              type: 'resource_field',
              resource: resourceField
            });
            
            resourceFeature.setStyle(resourceStyle);
            this.subgridLayer.getSource().addFeature(resourceFeature);
          }
        }
      }
    },
    
    createResourceFieldStyle(resourceField, x, y, opacity) {
      const cacheKey = `resource_${resourceField.type}_${resourceField.level}_${opacity}`;
      if (this.styleCache[cacheKey] !== undefined) {
        return this.styleCache[cacheKey];
      }

      const baseSize = 5;
      const level = resourceField.level;
      const zoom = this.map.getView().getZoom();

      if (zoom > 9) {
        const style = new Style({
          image: new Circle({
            radius: baseSize * (1 + level),
            fill: new Fill({
              color: this.getResourceColor(resourceField.type, 0.8)
            }),
            stroke: new Stroke({
              color: 'rgba(0, 0, 0, 0.5)',
              width: 2
            })
          })
        });

        style.setText(new Text({
          text: level.toString(),
          fill: new Fill({
            color: 'rgba(255, 255, 255, 0.9)'
          }),
          stroke: new Stroke({
            color: 'rgba(0, 0, 0, 0.8)',
            width: 1
          }),
          scale: [2, 2],
          offsetY: 0
        }));

        this.styleCache[cacheKey] = style;
        return style;
      }
      return null;
    },

    getResourceColor(type, opacity) {
      const colors = {
        food: `rgba(255, 235, 59, ${opacity})`, // Yellow
        wood: `rgba(139, 195, 74, ${opacity})`, // Green
        stone: `rgba(158, 158, 158, ${opacity})`, // Gray
        iron: `rgba(96, 125, 139, ${opacity})` // Blue-gray
      };
      return colors[type] || `rgba(255, 255, 255, ${opacity})`;
    },

    getSubgridColor(sx, sy, village, opacity) {
      // If it's not the player's village, show everything in gray
      if (!village.is_owned) {
        return `rgba(158, 158, 158, ${opacity * 0.6})`; // Gray for enemy villages
      }

      // Skip top corners and center
      if ((sx === 0 && sy === 0) || (sx === 4 && sy === 0) || (sx === 2 && sy === 2)) {
        return `rgba(255, 255, 255, ${opacity * 0.2})`;
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

          // Add building details if there's a construction in this slot
          if (village.city && village.city.constructions) {
            const slot = this.getCitySlotFromPosition(cx, cy);
            const construction = village.city.constructions.find(c => c.slot === slot);
            
            if (construction) {
              const buildingStyle = this.createBuildingStyle(construction, x + cx * 0.04, y + cy * 0.04, cityOpacity);
              if (buildingStyle) {
                const buildingFeature = new Feature({
                  geometry: new Point([
                    x + cx * 0.04 + 0.02,
                    y + cy * 0.04 + 0.02
                  ]),
                  type: 'building',
                  building: construction
                });
                buildingFeature.setStyle(buildingStyle);
                this.cityLayer.getSource().addFeature(buildingFeature);
              }
            }
          }
        }
      }
    },

    getCityGridColor(cx, cy, village, opacity) {
      // If it's not the player's village, show everything in black
      if (!village.is_owned) {
        return `rgba(0, 0, 0, ${opacity * 0.8})`; // Black for enemy cities
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
        switch (construction.type) {
          case 'city_center':
            return `rgba(0, 0, 0, ${opacity * 0.8})`; // Default brown
          case 'rally_point':
            return `rgba(100, 0, 0, ${opacity * 0.7})`; // Default brown
          case 'barraks':
            return `rgba(220, 20, 60, ${opacity * 0.7})`; // Military buildings - Crimson red
          case 'archery':
            return `rgba(178, 34, 34, ${opacity * 0.7})`; // Military buildings - Fire brick red
          case 'stable':
            return `rgba(139, 0, 0, ${opacity * 0.7})`; // Military buildings - Dark red
          case 'warehouse':
            return `rgba(0, 128, 128, ${opacity * 0.6})`; // Resource buildings - Teal
          case 'granary':
            return `rgba(0, 100, 0, ${opacity * 0.6})`; // Resource buildings - Dark green
          case 'hide_spot':
            return `rgba(128, 128, 0, ${opacity * 0.6})`; // Resource buildings - Olive
          default:
            return `rgba(139, 69, 19, ${opacity * 0.6})`; // Default brown
        }
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

          if (village && village.is_owned) {
            // Calculate subgrid and city positions only if needed
            const positions = this.calculatePositions(gridX, gridY, village);
            
            // Update current cells only if they've changed
            if (this.shouldUpdateCells(positions)) {
              this.currentSubgridCell = positions.subgrid;
              this.currentCityCell = positions.city;
              this.updateHoverDialog(pixel, positions, village);
              this.updateSubgrids();
            }
          } else {
            // Clear highlighting if not over a village
            this.clearHighlighting();
          }
        }
      }, 16); // ~60fps
    },
    
    findVillageAtPosition(gridX, gridY) {
      const key = `${Math.floor(gridX)},${Math.floor(gridY)}`;
      if (this.cachedVillagePositions[key] !== undefined) {
        return this.cachedVillagePositions[key];
      }

      const village = this.villages.find(v => 
        Math.floor(gridX) === v.location.x && 
        Math.floor(gridY) === v.location.y
      );

      this.cachedVillagePositions[key] = village;
      return village;
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
          
          if (resourceField && zoom > 8) {
            this.showSelectionDialog({
              type: resourceField.type,
              slot: resourceField.slot,
              level: resourceField.level,
              isEmpty: false
            }, 'resource');
          } else if (slot !== null && zoom > 8) {
            this.showSelectionDialog({
              slot: slot,
              isEmpty: true
            }, 'resource');
          } else if (village.city && village.city.constructions) {
            const citySlot = this.getCitySlotFromPosition(city.x, city.y);
            const construction = village.city.constructions.find(c => c.slot === citySlot);
            
            if (construction && zoom > 10) {
              this.showSelectionDialog({
                type: construction.type,
                slot: construction.slot,
                level: construction.level,
                isEmpty: false
              }, 'building');
            } else if (citySlot !== null && zoom > 10) {
              this.showSelectionDialog({
                slot: citySlot,
                isEmpty: true
              }, 'building');
            }
          }
        }
      }
    },
    
    handleMoveEnd() {
      this.zoomLevel = this.map.getView().getZoom().toFixed(2);
      this.clearStyleCache(); // Clear style cache when zoom level changes
      this.updateSubgrids();
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
      const cacheKey = `building_${building.type}_${building.level}_${opacity}`;
      if (this.styleCache[cacheKey] !== undefined) {
        return this.styleCache[cacheKey];
      }

      const baseSize = 5;
      const zoom = this.map.getView().getZoom();

      if (zoom > 11) {
        const style = new Style({
          image: new Circle({
            radius: baseSize * 1.5,
            fill: new Fill({
              color: this.getBuildingColor(building.type, 0.8)
            }),
            stroke: new Stroke({
              color: 'rgba(0, 0, 0, 0.5)',
              width: 2
            })
          })
        });

        style.setText(new Text({
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
        }));

        this.styleCache[cacheKey] = style;
        return style;
      }
      return null;
    },

    getBuildingColor(type, opacity) {
      const colors = {
        city_center: `rgba(139, 69, 19, ${opacity})`, // Brown
        rally_point: `rgba(100, 0, 0, ${opacity})`, // Dark red
        barraks: `rgba(220, 20, 60, ${opacity})`, // Crimson red
        archery: `rgba(178, 34, 34, ${opacity})`, // Fire brick red
        stable: `rgba(139, 0, 0, ${opacity})`, // Dark red
        warehouse: `rgba(0, 128, 128, ${opacity})`, // Teal
        granary: `rgba(0, 100, 0, ${opacity})`, // Dark green
        hide_spot: `rgba(128, 128, 0, ${opacity})` // Olive
      };
      return colors[type] || `rgba(139, 69, 19, ${opacity})`; // Default brown
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

    showSelectionDialog(data, type) {
      this.selectionDialog = {
        show: true,
        data,
        type
      };
    },

    handleUpgrade({ type, slot, currentLevel }) {
      // Find the current village based on the last clicked position
      const coords = this.map.getEventCoordinate(this.lastClickEvent);
      const gridX = Math.round(coords[0] * 100) / 100;
      const gridY = Math.round(coords[1] * 100) / 100;
      
      const village = this.findVillageAtPosition(gridX, gridY);
      
      if (!village || !village.is_owned) {
        console.error('No owned village found at position');
        return;
      }

      // Format the command based on type
      // Convert 'resource' to 'field' for the command
      const commandType = type === 'resource' ? 'field' : type;
      const command = `upgrade ${commandType} in ${slot}`;
      
      // Execute the command
      apiService.executeCommand(village.id, command)
        .then(response => {
          console.log('Upgrade command executed:', response);
          // Refresh map data to show updated state
          this.fetchMapData();
        })
        .catch(error => {
          console.error('Failed to execute upgrade command:', error);
          // You might want to show an error message to the user here
        });
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

.map-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 8px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 100;
}

@media (max-width: 600px) {
  .map-controls {
    bottom: 15px;
    right: 15px;
  }
  
  .coords-display {
    top: 10px;
    left: 10px;
    font-size: 12px;
    padding: 4px 8px;
  }
}
</style> 