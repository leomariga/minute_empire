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
import { Style, Fill, Stroke, Text, Circle } from 'ol/style';
import { defaults as defaultControls } from 'ol/control';

// Set up geographic coordinates
useGeographic();

export default {
  name: 'MapViewOL',
  
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
      cityLayer: null
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
      const zoom = this.map.getView().getZoom();
      this.subgridLayer.getSource().clear();
      this.cityLayer.getSource().clear();
      
      if (zoom > 3) {
        this.villages.forEach(village => {
          this.drawVillageSubgrid(village);
        });
      }
      
      if (zoom > 6) {
        this.villages.forEach(village => {
          this.drawCityGrid(village);
        });
      }
    },
    
    drawVillageSubgrid(village) {
      const x = village.location.x;
      const y = village.location.y;
      
      for (let sx = 0; sx < 5; sx++) {
        for (let sy = 0; sy < 5; sy++) {
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
          
          subgridFeature.setStyle(new Style({
            fill: new Fill({
              color: this.getSubgridColor(sx, sy, village)
            }),
            stroke: new Stroke({
              color: 'rgba(0, 0, 0, 0.5)',
              width: 0.5
            })
          }));
          
          this.subgridLayer.getSource().addFeature(subgridFeature);
        }
      }
    },
    
    drawCityGrid(village) {
      const x = village.location.x + 0.4;
      const y = village.location.y + 0.4;
      
      for (let cx = 0; cx < 5; cx++) {
        for (let cy = 0; cy < 5; cy++) {
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
              color: this.getCityGridColor(cx, cy, village)
            }),
            stroke: new Stroke({
              color: 'rgba(0, 0, 0, 0.5)',
              width: 0.5
            })
          }));
          
          this.cityLayer.getSource().addFeature(cityFeature);
        }
      }
    },
    
    getSubgridColor(sx, sy, village) {
      // If it's not the player's village, show everything in gray
      if (!village.is_owned) {
        return 'rgba(158, 158, 158, 0.6)'; // Gray for enemy villages
      }

      // Skip top corners and center
      if ((sx === 0 && sy === 0) || (sx === 4 && sy === 0) || (sx === 2 && sy === 2)) {
        return 'rgba(255, 255, 255, 0.2)';
      }

      // Calculate slot number based on spiral pattern
      const slotNumber = this.getSlotFromPosition(sx, sy);
      
      // Debug logging
      console.log('Village data:', {
        name: village.name,
        resource_fields: village.resource_fields,
        slotNumber: slotNumber
      });
      
      // If resource_fields array doesn't exist or slot is invalid, return default color
      if (!village.resource_fields || !Array.isArray(village.resource_fields) || slotNumber === null || slotNumber === undefined) {
        return 'rgba(255, 255, 255, 0.2)';
      }
      
      // Find the resource field for this slot
      const resourceField = village.resource_fields.find(field => field && field.slot === slotNumber);
      if (!resourceField) {
        return 'rgba(255, 255, 255, 0.2)';
      }
      
      // Return color based on resource type
      switch (resourceField.type) {
        case 'food':
          return 'rgba(255, 235, 59, 0.6)'; // Yellow for food
        case 'wood':
          return 'rgba(139, 195, 74, 0.6)'; // Green for wood
        case 'stone':
          return 'rgba(158, 158, 158, 0.6)'; // Gray for stone
        case 'iron':
          return 'rgba(96, 125, 139, 0.6)'; // Blue-gray for iron
        default:
          return 'rgba(255, 255, 255, 0.2)';
      }
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
      // Center is slot 12 (city center)
      // Buildings spiral outward from the center
      const cityPattern = [
        [22,  10,    11,     12,    23],
        [21,    9,    2,     3,  13],
        [20,    8,    1,     4,  14],
        [19,     7,    6,     5,   15],
        [25,  18,    17,     16,    24]
      ];
      
      return cityPattern[cy][cx];
    },

    getCityGridColor(cx, cy, village) {
      // If it's not the player's village, show everything in black
      if (!village.is_owned) {
        return 'rgba(0, 0, 0, 0.8)'; // Black for enemy cities
      }

      // Check if city data exists
      if (!village.city) {
        return 'rgba(255, 255, 255, 0.2)'; // Default color if no city data
      }

      // Get the slot number from the position
      const slot = this.getCitySlotFromPosition(cx, cy);
      
      // If no slot is assigned to this position, return transparent
      if (slot === null) {
        return 'rgba(255, 255, 255, 0.2)';
      }

      // City center is always slot 12
      if (slot === 12) {
        const centerBuilding = village.city.constructions.find(c => c.type === 'city_center');
        return centerBuilding ? 'rgba(139, 69, 19, 0.8)' : 'rgba(205, 133, 63, 0.6)';
      }

      // Check if there's a construction in this slot
      const construction = village.city.constructions.find(c => c.slot === slot);
      if (construction) {
        switch (construction.type) {
          case 'city_center':
            return 'rgba(0, 0, 0, 0.8)'; // Default brown
          case 'rally_point':
            return 'rgba(100, 0, 0, 0.7)'; // Default brown
          case 'barraks':
            return 'rgba(220, 20, 60, 0.7)'; // Military buildings - Crimson red
          case 'archery':
            return 'rgba(178, 34, 34, 0.7)'; // Military buildings - Fire brick red
          case 'stable':
            return 'rgba(139, 0, 0, 0.7)'; // Military buildings - Dark red
          case 'warehouse':
            return 'rgba(0, 128, 128, 0.6)'; // Resource buildings - Teal
          case 'granary':
            return 'rgba(0, 100, 0, 0.6)'; // Resource buildings - Dark green
          case 'hide_spot':
            return 'rgba(128, 128, 0, 0.6)'; // Resource buildings - Olive
          default:
            return 'rgba(139, 69, 19, 0.6)'; // Default brown
        }
      }

      // Empty buildable slots
      return 'rgba(255, 255, 255, 0.2)';
    },
    
    handlePointerMove(event) {
      const coords = this.map.getEventCoordinate(event.originalEvent);
      
      // Convert coordinates to grid position with floating point precision
      const gridX = Math.round(coords[0] * 100) / 100;
      const gridY = Math.round(coords[1] * 100) / 100;
      
      // Only update if coordinates are within bounds
      if (gridX >= this.mapBounds.x_min && gridX <= this.mapBounds.x_max &&
          gridY >= this.mapBounds.y_min && gridY <= this.mapBounds.y_max) {
        this.currentCoords = {
          x: gridX,
          y: gridY
        };
      }
    },
    
    handleMapClick(event) {
      const coords = this.map.getEventCoordinate(event.originalEvent);
      const x = Math.round(coords[0]);
      const y = Math.round(coords[1]);
      
      // Find village at clicked location
      const village = this.villages.find(v => 
        v.location.x === x && 
        v.location.y === y
      );
      
      if (village) {
        this.onVillageClick(village);
      }
    },
    
    handleMoveEnd() {
      this.zoomLevel = this.map.getView().getZoom().toFixed(2);
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
    
    onVillageClick(village) {
      // Handle village click (show dialog, etc.)
      console.log('Village clicked:', village);
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