<template>
  <v-container fluid class="map-container pa-0 ma-0" style="height: 100vh; width: 100%;">
    <div 
      ref="mapContainer" 
      class="map-wrapper" 
      @wheel="handleZoom"
      @mousedown="startDrag"
      @touchstart.prevent="startTouch"
      @mousemove="onDrag"
      @touchmove.prevent="onTouch"
      @mouseup="endDrag"
      @touchend.prevent="endTouch"
      @mouseleave="endDrag"
    >
      <!-- Error message -->
      <v-alert v-if="error" type="error" class="map-error" dismissible>
        {{ error }}
      </v-alert>
      
      <!-- Loading overlay -->
      <v-overlay :value="loading" absolute>
        <v-progress-circular indeterminate size="64" color="primary"></v-progress-circular>
        <div class="mt-4">Loading map data...</div>
      </v-overlay>
      
      <!-- The actual map grid -->
      <div class="map-grid-container" :style="mapGridStyle">
        <!-- Map background with grid pattern -->
        <div class="map-background"></div>
        
        <!-- Map grid cells -->
        <div v-for="y in mapSize" :key="`row-${y}`" class="map-row">
          <div 
            v-for="x in mapSize" 
            :key="`cell-${x}-${y}`" 
            class="map-cell"
            :class="{
              'map-cell-highlight': highlightedCoords.x === (x - 1 - mapBounds.x_max) && 
                                    highlightedCoords.y === (mapBounds.y_max - (y - 1))
            }"
            :style="getCellStyle(x - 1 - mapBounds.x_max, mapBounds.y_max - (y - 1))"
            @mouseenter="highlightCell(x - 1 - mapBounds.x_max, mapBounds.y_max - (y - 1))"
            @mouseleave="unhighlightCell()"
            @click="onCellClick(x - 1 - mapBounds.x_max, mapBounds.y_max - (y - 1))"
          >
            <!-- Cell coordinates (only visible when zoomed in) -->
            <div class="cell-coords" v-if="zoom > 1.4">
              {{ x - 1 - mapBounds.x_max }},{{ mapBounds.y_max - (y - 1) }}
            </div>
            
            <!-- Village marker if exists -->
            <template v-if="getVillageAt(x - 1 - mapBounds.x_max, mapBounds.y_max - (y - 1))">
              <!-- Full village view with nested grids that's always visible -->
              <div class="village-full-view" 
                   @click.stop="onVillageClick(getVillageAt(x - 1 - mapBounds.x_max, mapBounds.y_max - (y - 1)))">
                <div class="village-title" v-if="zoom > 1.2">
                  {{ getVillageAt(x - 1 - mapBounds.x_max, mapBounds.y_max - (y - 1)).name }}
                </div>
                
                <!-- 5x5 grid for resources -->
                <div class="fields-grid">
                  <div v-for="ry in 5" :key="`field-row-${ry}`" class="field-row">
                    <div v-for="rx in 5" :key="`field-cell-${rx}-${ry}`" 
                         class="field-cell"
                         :class="{ 
                           'field-center': rx === 3 && ry === 3,
                           'field-wheat': (rx === 1 || rx === 5) && (ry === 1 || ry === 5),
                           'field-wood': (rx === 2 || rx === 4) && (ry === 2 || ry === 4),
                           'field-stone': (rx === 1 || rx === 5) && ry === 3 || (rx === 3 && (ry === 1 || ry === 5)),
                           'field-iron': (rx === 2 || rx === 4) && (ry === 1 || ry === 5) || (rx === 1 || rx === 5) && (ry === 2 || ry === 4)
                         }">
                      
                      <!-- If center cell, show the 5x5 city grid -->
                      <template v-if="rx === 3 && ry === 3">
                        <div class="city-grid">
                          <div v-for="cy in 5" :key="`city-row-${cy}`" class="city-row">
                            <div v-for="cx in 5" :key="`city-cell-${cx}-${cy}`" 
                                class="city-cell"
                                :class="{
                                  'city-center': cx === 3 && cy === 3,
                                  'city-wall': cx === 1 || cx === 5 || cy === 1 || cy === 5,
                                  'city-building': !(cx === 3 && cy === 3) && !(cx === 1 || cx === 5 || cy === 1 || cy === 5)
                                }">
                              <!-- Central city square is black -->
                              <div v-if="cx === 3 && cy === 3" class="city-core"></div>
                            </div>
                          </div>
                        </div>
                      </template>
                      
                      <!-- Show field coordinates if zoomed in enough -->
                      <div v-else-if="zoom > 2" class="field-coord">
                        {{ rx }},{{ ry }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Coordinates display -->
    <div class="coords-display" v-if="highlightedCoords.x !== null">
      X: {{ highlightedCoords.x }}, Y: {{ highlightedCoords.y }}
    </div>
    
    <!-- Zoom level indicator -->
    <div class="zoom-indicator">
      Zoom: {{ zoomLevel }}
    </div>
    
    <!-- Mobile-friendly controls -->
    <div class="map-controls">
      <v-btn fab small color="primary" class="mb-2" @click="zoomIn()" aria-label="Zoom in">
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <v-btn fab small color="primary" class="mb-2" @click="zoomOut()" aria-label="Zoom out">
        <v-icon>mdi-minus</v-icon>
      </v-btn>
      <v-btn fab small color="primary" @click="resetView" aria-label="Reset view">
        <v-icon>mdi-home</v-icon>
      </v-btn>
    </div>
    
    <!-- Village detail dialog -->
    <v-dialog v-model="villageDialogOpen" max-width="500" :fullscreen="isMobile">
      <v-card v-if="selectedVillage">
        <v-toolbar color="primary" dark>
          <v-toolbar-title>{{ selectedVillage.name }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="villageDialogOpen = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        
        <v-card-subtitle>
          Location: ({{ selectedVillage.location.x }}, {{ selectedVillage.location.y }})
        </v-card-subtitle>
        
        <v-card-text>
          <v-row v-if="selectedVillage.is_owned">
            <v-col cols="12">
              <v-card outlined>
                <v-card-title>Village Details</v-card-title>
                <v-card-text>
                  <!-- Resource field grid for owned villages -->
                  <div class="village-grid">
                    <!-- 5x5 grid for resources -->
                    <div v-for="ry in 5" :key="`resource-row-${ry}`" class="resource-row">
                      <div v-for="rx in 5" :key="`resource-cell-${rx}-${ry}`" 
                           class="resource-cell"
                           :class="{ 'city-cell': rx === 3 && ry === 3 }">
                        <!-- City is in the middle -->
                        <template v-if="rx === 3 && ry === 3">
                          <div class="city-container">
                            <!-- 5x5 grid for city buildings -->
                            <div v-for="cy in 5" :key="`city-row-${cy}`" class="city-row">
                              <div v-for="cx in 5" :key="`city-cell-${cx}-${cy}`" 
                                   class="city-cell"
                                   :class="{ 
                                     'city-center': cx === 3 && cy === 3,
                                     'wall-cell': cx === 1 || cx === 5 || cy === 1 || cy === 5 
                                   }">
                                <!-- City center in the middle -->
                                <template v-if="cx === 3 && cy === 3">
                                  <v-icon small>mdi-home-city</v-icon>
                                </template>
                                <!-- Walls around the city -->
                                <template v-else-if="cx === 1 || cx === 5 || cy === 1 || cy === 5">
                                  <v-icon x-small>mdi-wall</v-icon>
                                </template>
                              </div>
                            </div>
                          </div>
                        </template>
                        <template v-else>
                          <div class="resource-slot">
                            {{ rx }},{{ ry }}
                          </div>
                        </template>
                      </div>
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
          <v-row v-else>
            <v-col cols="12">
              <v-alert type="info">
                This village belongs to another player.
              </v-alert>
            </v-col>
          </v-row>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="villageDialogOpen = false">Close</v-btn>
          <v-btn v-if="selectedVillage.is_owned" text color="primary" @click="goToVillageDetail">
            Manage Village
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import apiService from '@/services/apiService';
import authService from '@/services/authService';

// Define interfaces for the API response types
// These help with code completeness and documentation
const MapInterfaces = {
  /**
   * Map bounds from the API
   */
  MapBounds: {
    x_min: 0,
    x_max: 0,
    y_min: 0,
    y_max: 0
  },
  
  /**
   * Location coordinates
   */
  Location: {
    x: 0,
    y: 0
  },
  
  /**
   * Village data for map display
   */
  MapVillage: {
    id: '',
    name: '',
    location: {
      x: 0,
      y: 0
    },
    owner_id: '',
    is_owned: false
  },
  
  /**
   * Complete map info response
   */
  MapInfoResponse: {
    map_bounds: {},
    map_size: 0,
    villages: []
  }
};

// Village marker component
const VillageMarker = {
  props: ['village', 'zoom'],
  template: `
    <div class="village-marker" :class="{ 'owned-village': village.is_owned }">
      <div class="village-icon">
        <v-icon :size="iconSize">{{ village.is_owned ? 'mdi-home-circle' : 'mdi-home-outline' }}</v-icon>
      </div>
      <div class="village-name" v-if="zoom > 1.2">{{ village.name }}</div>
    </div>
  `,
  computed: {
    iconSize() {
      return 18 * this.zoom;
    }
  }
};

export default {
  name: 'MapView',
  
  components: {
    VillageMarker
  },
  
  data() {
    return {
      loading: true,
      error: null,
      mapData: null,
      mapBounds: {
        x_min: -15,
        x_max: 15,
        y_min: -15,
        y_max: 15
      },
      mapSize: 31,
      villages: [],
      zoom: 1,
      position: { x: 0, y: 0 },
      dragging: false,
      lastPoint: { x: 0, y: 0 },
      selectedVillage: null,
      villageDialogOpen: false,
      highlightedCoords: { x: null, y: null },
      windowWidth: window.innerWidth,
      pinchDistance: 0, // For tracking pinch-to-zoom distance
      lastScale: 1,     // For tracking zoom scale changes
    };
  },
  
  computed: {
    mapGridStyle() {
      // Using Math.round to avoid sub-pixel rendering which can cause blurriness
      const x = Math.round(this.position.x);
      const y = Math.round(this.position.y);
      
      return {
        transform: `translate(${x}px, ${y}px) scale(${this.zoom})`,
        width: `${this.mapSize * 60}px`,
        height: `${this.mapSize * 60}px`
      };
    },
    
    isMobile() {
      return this.windowWidth < 600;
    },
    
    zoomLevel() {
      return this.zoom.toFixed(2);
    }
  },
  
  async created() {
    if (!authService.isAuthenticated()) {
      this.$router.push('/login');
      return;
    }
    
    await this.fetchMapData();
    
    // Add window resize handler
    window.addEventListener('resize', this.handleResize);
    // Track window width for mobile detection
    this.checkWindowSize();
    
    // Set CSS custom property for current zoom level that will be used for text scaling
    this.$nextTick(() => {
      this.updateTextScaling();
    });
  },
  
  beforeDestroy() {
    // Clean up resize listener
    window.removeEventListener('resize', this.handleResize);
    
    // Clean up document event listeners if they exist
    document.removeEventListener('mousemove', this.onDragDocument);
    document.removeEventListener('mouseup', this.endDragDocument);
    document.removeEventListener('touchmove', this.onTouchDocument);
    document.removeEventListener('touchend', this.endTouchDocument);
    document.removeEventListener('touchcancel', this.endTouchDocument);
    document.removeEventListener('touchmove', this.handlePinchZoom);
    document.removeEventListener('touchend', this.endPinchZoom);
    document.removeEventListener('touchcancel', this.endPinchZoom);
  },
  
  methods: {
    async fetchMapData() {
      try {
        this.loading = true;
        const data = await apiService.getMapInfo();
        
        // Set map data
        this.mapData = data;
        this.mapBounds = data.map_bounds;
        this.mapSize = data.map_size;
        this.villages = data.villages;
        
        // Center the map
        this.resetView();
      } catch (error) {
        this.error = 'Failed to load map data. Please try again later.';
        console.error('Error fetching map data:', error);
      } finally {
        this.loading = false;
      }
    },
    
    getVillageAt(x, y) {
      return this.villages.find(v => 
        v.location.x === x && 
        v.location.y === y
      );
    },
    
    getCellStyle(x, y) {
      // Basic cell style
      const style = {};
      
      // Add a different background for owned villages
      const village = this.getVillageAt(x, y);
      if (village) {
        if (village.is_owned) {
          style.backgroundColor = 'rgba(76, 175, 80, 0.3)';  // Green for owned
        } else {
          style.backgroundColor = 'rgba(244, 67, 54, 0.3)';  // Red for others
        }
      }
      
      return style;
    },
    
    // Cell highlight methods
    highlightCell(x, y) {
      this.highlightedCoords = { x, y };
    },
    
    unhighlightCell() {
      // Keep coordinates in the display but don't highlight cell
    },
    
    onCellClick(x, y) {
      // Handle cell click (can be used for placing a new village)
      console.log(`Cell clicked at ${x},${y}`);
      
      // If there's a village here, show its info
      const village = this.getVillageAt(x, y);
      if (village) {
        this.onVillageClick(village);
      }
    },
    
    // Mouse drag handling - improved for better tracking
    startDrag(event) {
      if (event.button === 0) { // Left mouse button
        this.dragging = true;
        this.lastPoint = { 
          x: event.clientX, 
          y: event.clientY 
        };
        
        // Add event listeners to document for smoother drag experience
        document.addEventListener('mousemove', this.onDragDocument);
        document.addEventListener('mouseup', this.endDragDocument);
        
        // Set cursor style
        document.body.style.cursor = 'grabbing';
        
        event.preventDefault();
      }
    },
    
    onDrag(event) {
      // Only handle if inside the map container - document events handle the rest
      if (this.dragging) {
        event.preventDefault();
      }
    },
    
    onDragDocument(event) {
      if (!this.dragging) return;
      
      // Calculate movement difference
      const dx = event.clientX - this.lastPoint.x;
      const dy = event.clientY - this.lastPoint.y;
      
      // Update position with the exact difference
      this.position.x += dx;
      this.position.y += dy;
      
      // Update last point for next calculation
      this.lastPoint = { 
        x: event.clientX, 
        y: event.clientY 
      };
      
      event.preventDefault();
    },
    
    endDrag() {
      if (this.dragging) {
        this.dragging = false;
      }
    },
    
    endDragDocument() {
      this.dragging = false;
      
      // Reset cursor
      document.body.style.cursor = '';
      
      // Remove document listeners
      document.removeEventListener('mousemove', this.onDragDocument);
      document.removeEventListener('mouseup', this.endDragDocument);
    },
    
    // Touch handling for mobile - improved
    startTouch(event) {
      if (event.touches.length === 1) {
        // Single touch - handle drag
        this.dragging = true;
        this.lastPoint = { 
          x: event.touches[0].clientX, 
          y: event.touches[0].clientY 
        };
        
        // Add event listeners to document for smoother touch experience
        document.addEventListener('touchmove', this.onTouchDocument, { passive: false });
        document.addEventListener('touchend', this.endTouchDocument);
        document.addEventListener('touchcancel', this.endTouchDocument);
        
        event.preventDefault();
      } else if (event.touches.length === 2) {
        // Two touches - handle pinch zoom
        this.dragging = false;
        const touch1 = event.touches[0];
        const touch2 = event.touches[1];
        
        // Calculate the distance between the two points
        this.pinchDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        
        // Calculate the midpoint between the touches (center of screen)
        const container = this.$refs.mapContainer;
        const rect = container.getBoundingClientRect();
        this.lastPoint = {
          x: rect.left + rect.width / 2,
          y: rect.top + rect.height / 2
        };
        
        // Store last scale
        this.lastScale = this.zoom;
        
        document.addEventListener('touchmove', this.handlePinchZoom, { passive: false });
        document.addEventListener('touchend', this.endPinchZoom);
        document.addEventListener('touchcancel', this.endPinchZoom);
        
        event.preventDefault();
      }
    },
    
    onTouch(event) {
      // Only handle if inside the map container - document events handle the rest
      if (this.dragging) {
        event.preventDefault();
      }
    },
    
    onTouchDocument(event) {
      if (!this.dragging || event.touches.length !== 1) return;
      
      const dx = event.touches[0].clientX - this.lastPoint.x;
      const dy = event.touches[0].clientY - this.lastPoint.y;
      
      this.position.x += dx;
      this.position.y += dy;
      
      this.lastPoint = { 
        x: event.touches[0].clientX, 
        y: event.touches[0].clientY 
      };
      
      event.preventDefault();
    },
    
    endTouch() {
      if (this.dragging) {
        this.dragging = false;
      }
    },
    
    endTouchDocument() {
      this.dragging = false;
      // Remove document listeners
      document.removeEventListener('touchmove', this.onTouchDocument);
      document.removeEventListener('touchend', this.endTouchDocument);
      document.removeEventListener('touchcancel', this.endTouchDocument);
    },
    
    handlePinchZoom(event) {
      if (event.touches.length !== 2) return;
      
      const touch1 = event.touches[0];
      const touch2 = event.touches[1];
      
      // Calculate the new distance between touches
      const newDistance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      
      // Calculate zoom scale factor based on the change in distance
      const scaleFactor = newDistance / this.pinchDistance;
      
      // Calculate new zoom level
      let newZoom = this.lastScale * scaleFactor;
      
      // Apply zoom limits
      if (newZoom > 50) newZoom = 50;
      if (newZoom < 0.5) newZoom = 0.5;
      
      // Use center of screen for pinch zoom
      this.zoomToCenter(newZoom);
      
      event.preventDefault();
    },
    
    endPinchZoom() {
      // Remove document listeners
      document.removeEventListener('touchmove', this.handlePinchZoom);
      document.removeEventListener('touchend', this.endPinchZoom);
      document.removeEventListener('touchcancel', this.endPinchZoom);
      
      // Store final scale for next pinch
      this.lastScale = this.zoom;
    },
    
    // Zoom handling - completely rewritten
    handleZoom(event) {
      event.preventDefault();
      event.stopPropagation();
      
      const delta = event.deltaY;
      
      // Calculate new zoom level
      const oldZoom = this.zoom;
      let newZoom;
      
      if (delta < 0) {
        // Zoom in - use smaller increments at higher zoom levels for finer control
        const zoomFactor = oldZoom > 10 ? 1.05 : 1.1;
        newZoom = oldZoom * zoomFactor;
        if (newZoom > 50) newZoom = 50; // Increased max zoom to 50x
      } else {
        // Zoom out - use smaller decrements at higher zoom levels
        const zoomFactor = oldZoom > 10 ? 1.05 : 1.1;
        newZoom = oldZoom / zoomFactor;
        if (newZoom < 0.5) newZoom = 0.5;
      }
      
      this.zoomToCenter(newZoom);
    },
    
    // New zoom method that focuses on the center of the viewport
    zoomToCenter(newZoom) {
      // Get container dimensions
      const container = this.$refs.mapContainer;
      const rect = container.getBoundingClientRect();
      const viewportCenterX = rect.width / 2;
      const viewportCenterY = rect.height / 2;
      
      // Get the current zoom level
      const oldZoom = this.zoom;
      
      // Calculate the point in the map that is currently at the center of the viewport
      // in world coordinates (unzoomed)
      const worldX = (viewportCenterX - this.position.x) / oldZoom;
      const worldY = (viewportCenterY - this.position.y) / oldZoom;
      
      // Set the new zoom level
      this.zoom = newZoom;
      
      // Calculate where that same world point would be at the new zoom level
      const newViewportX = worldX * newZoom;
      const newViewportY = worldY * newZoom;
      
      // Adjust position to keep that world point at the center of the viewport
      this.position.x = viewportCenterX - newViewportX;
      this.position.y = viewportCenterY - newViewportY;
      
      // Update CSS variable for text scaling
      this.updateTextScaling();
    },
    
    // New method to update CSS custom property for text scaling
    updateTextScaling() {
      document.documentElement.style.setProperty('--current-zoom', this.zoom);
      
      // Update text elements directly after zoom changes
      this.$nextTick(() => {
        // Get all elements that need to maintain constant size
        const scalableElements = document.querySelectorAll('.cell-coords, .field-coord, .village-title, .village-name, .resource-slot');
        
        // Apply scaling inversely proportional to zoom
        scalableElements.forEach(element => {
          // Use a slightly larger scale to increase text readability
          const scale = 1 / this.zoom;
          element.style.transform = `scale(${scale})`;
        });
      });
    },
    
    zoomIn() {
      // Use smaller increments at higher zoom levels for finer control
      const zoomFactor = this.zoom > 10 ? 1.1 : 1.2;
      const newZoom = this.zoom * zoomFactor;
      if (newZoom <= 50) { // Increased from 20 to 50
        this.zoomToCenter(newZoom);
      }
    },
    
    zoomOut() {
      const newZoom = this.zoom / 1.2; // 20% zoom decrease
      if (newZoom >= 0.5) {
        this.zoomToCenter(newZoom);
      }
    },
    
    resetView() {
      this.zoom = 1;
      this.centerMap();
    },
    
    centerMap() {
      // Center map in the container
      const container = this.$refs.mapContainer;
      if (container) {
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;
        const mapWidth = this.mapSize * 60;
        const mapHeight = this.mapSize * 60;
        
        this.position.x = (containerWidth - mapWidth) / 2;
        this.position.y = (containerHeight - mapHeight) / 2;
      }
    },
    
    handleResize() {
      this.centerMap();
      this.checkWindowSize();
    },
    
    // Village selection
    onVillageClick(village) {
      this.selectedVillage = village;
      this.villageDialogOpen = true;
    },
    
    goToVillageDetail() {
      if (this.selectedVillage && this.selectedVillage.is_owned) {
        // Redirect to village detail view
        this.$router.push({
          path: '/village',
          query: { id: this.selectedVillage.id }
        });
      }
    },
    
    checkWindowSize() {
      this.windowWidth = window.innerWidth;
    }
  }
};
</script>

<style scoped>
.map-container {
  position: relative;
  overflow: hidden;
  touch-action: none; /* Prevent browser handling of touch gestures */
}

.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: #e9e2d0; /* Parchment/map-like color */
  background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23bc9d71' fill-opacity='0.25' fill-rule='evenodd'/%3E%3C/svg%3E");
  cursor: grab;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  touch-action: none;
}

.map-wrapper:active {
  cursor: grabbing;
}

.map-grid-container {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: 0 0;
  will-change: transform;
  transition: none; /* Remove transition to prevent blur during zoom */
  
  /* High-quality rendering settings for different browsers */
  image-rendering: -webkit-optimize-contrast; /* Chrome */
  image-rendering: -moz-crisp-edges; /* Firefox */
  image-rendering: crisp-edges; /* Safari and standard */
  image-rendering: pixelated; /* Last resort for extreme zoom */
  -ms-interpolation-mode: nearest-neighbor; /* IE */
  
  /* Force hardware acceleration */
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  -webkit-transform-style: preserve-3d;
  
  /* Additional optimization */
  perspective: 1000px;
  -webkit-perspective: 1000px;
}

.map-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: 60px 60px;
  background-image: linear-gradient(to right, rgba(150, 150, 150, 0.05) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(150, 150, 150, 0.05) 1px, transparent 1px);
  pointer-events: none;
}

.map-row {
  display: flex;
}

.map-cell {
  width: 60px;
  height: 60px;
  border: none; /* Removed border */
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease;
  box-sizing: border-box;
}

.map-cell:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.map-cell-highlight {
  box-shadow: inset 0 0 10px rgba(255, 223, 0, 0.3);
}

.cell-coords {
  position: absolute;
  bottom: 2px;
  right: 2px;
  font-size: 12px; /* Increased from 8px for better readability */
  color: rgba(0, 0, 0, 0.7); /* Darker for better contrast */
  pointer-events: none;
  transform-origin: right bottom;
  background-color: rgba(255, 255, 255, 0.6); /* Background to improve readability */
  padding: 1px 2px;
  border-radius: 2px;
}

.village-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  z-index: 10;
  text-align: center;
}

.village-icon {
  padding: 4px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.7);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease;
}

.village-icon:hover {
  transform: scale(1.1);
}

.owned-village .village-icon {
  background-color: rgba(76, 175, 80, 0.2);
  border: 2px solid #4CAF50;
}

.village-name {
  margin-top: 2px;
  font-size: 12px; /* Increased from 10px for better readability */
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px; /* Increased from 80px */
  background-color: rgba(255, 255, 255, 0.8); /* More opaque background */
  padding: 2px 4px;
  border-radius: 3px;
  text-align: center;
  transform-origin: center top;
}

.field-coord {
  color: rgba(0, 0, 0, 0.7); /* Darker for better contrast */
  font-size: 10px; /* Increased from 5px for better readability */
  transform-origin: center center;
  background-color: rgba(255, 255, 255, 0.6); /* Background to improve readability */
  padding: 1px 2px;
  border-color: 2px;
  z-index: 2;
}

.village-title {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px; /* Increased from 8px */
  font-weight: bold;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.9); /* More opaque */
  padding: 2px 5px;
  border-radius: 3px;
  max-width: 100%; /* Increased from 90% */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  z-index: 3;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transform-origin: center center;
}

.resource-slot {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px; /* Increased from 10px */
  font-weight: bold;
  color: rgba(0, 0, 0, 0.8); /* Darker for better contrast */
  transform-origin: center center;
  background-color: rgba(255, 255, 255, 0.3); /* Background to improve readability */
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

.map-error {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  max-width: 80%;
}

/* Village detail view styles */
.village-grid {
  display: flex;
  flex-direction: column;
  border: none; /* Removed border */
  border-radius: 6px;
  width: 100%;
  overflow: hidden;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.resource-row {
  display: flex;
}

.resource-cell {
  width: 60px;
  height: 60px;
  border: none; /* Removed border */
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  font-size: 10px;
  color: rgba(0, 0, 0, 0.6);
  background-color: rgba(139, 195, 74, 0.1);
}

.city-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-sizing: border-box;
  border: none; /* Removed border */
}

.city-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.city-row {
  display: flex;
  flex: 1;
}

.city-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-sizing: border-box;
  border: none; /* Removed border */
}

.city-center {
  position: relative;
  background-color: #4A4644; /* Darker gray */
}

.city-core {
  width: 70%;
  height: 70%;
  background-color: #212121; /* Almost black */
  border-radius: 1px;
}

.city-wall {
  background-color: #A1887F; /* Brown */
  border: none; /* Removed border */
}

.city-building {
  background-color: #D7CCC8; /* Light brown */
  border: none; /* Removed border */
}

.resource-slot {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px; /* Increased from 10px */
  font-weight: bold;
  color: rgba(0, 0, 0, 0.8); /* Darker for better contrast */
  transform-origin: center center;
  background-color: rgba(255, 255, 255, 0.3); /* Background to improve readability */
}

/* Recursive village detail styles */
.village-fields {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 4px;
  padding: 2px;
}

.village-fields-title {
  font-size: 8px;
  font-weight: bold;
  margin-bottom: 2px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 1px 4px;
  border-radius: 2px;
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transform: scale(calc(1 / var(--current-zoom, 1))); /* Keep size constant regardless of zoom */
  transform-origin: center bottom;
}

.fields-grid {
  display: flex;
  flex-direction: column;
  width: 90%;
  height: 90%;
  border: none; /* Removed border */
}

.field-row {
  display: flex;
  flex: 1;
}

.field-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none; /* Removed border */
  background-color: rgba(139, 195, 74, 0.1);
  position: relative;
}

/* Resource field types */
.field-wheat {
  background-color: rgba(255, 235, 59, 0.3); /* Yellow */
}

.field-wood {
  background-color: rgba(139, 195, 74, 0.3); /* Green */
}

.field-stone {
  background-color: rgba(158, 158, 158, 0.3); /* Gray */
}

.field-iron {
  background-color: rgba(96, 125, 139, 0.3); /* Blue-gray */
}

.field-center {
  background-color: rgba(255, 193, 7, 0.2);
  border: none; /* Removed border */
}

.simple-building {
  font-weight: bold;
  font-size: 10px;
  color: #654321; /* Brown */
  transform: scale(calc(1 / var(--current-zoom, 1))); /* Keep size constant regardless of zoom */
}

.minimalist-city {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #FFE0B2; /* Light orange */
  border-radius: 2px;
}

/* City walls as simple lines - no longer needed as borders are removed */
.city-wall-h, .city-wall-v, .city-wall-tl, .city-wall-tr, .city-wall-bl, .city-wall-br {
  background-color: #A1887F; /* Brown */
}

.city-label {
  font-weight: bold;
  font-size: 10px;
  color: #5D4037; /* Dark brown */
  transform: scale(calc(1 / var(--current-zoom, 1))); /* Keep size constant regardless of zoom */
}

.resource-indicator {
  font-size: 6px;
  color: rgba(0, 0, 0, 0.5);
  transform: scale(calc(1 / var(--current-zoom, 1))); /* Keep size constant regardless of zoom */
}

/* Village detail containers */
.village-detail-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 4px;
  padding: 2px;
}

.village-detail-title {
  font-size: 8px;
  font-weight: bold;
  margin-bottom: 2px;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 1px 4px;
  border-radius: 2px;
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transform: scale(calc(1 / var(--current-zoom, 1))); /* Keep size constant regardless of zoom */
}

.detail-grid {
  display: flex;
  flex-direction: column;
  width: 95%;
  height: 95%;
}

.detail-row {
  display: flex;
  flex: 1;
}

.detail-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none; /* Removed border */
  position: relative;
}

.detail-city {
  background-color: rgba(255, 193, 7, 0.1);
  border: none; /* Removed border */
}

/* Village full view with nested grids */
.village-full-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
}

.village-title {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%) scale(calc(1 / var(--current-zoom, 1))); /* Keep size constant regardless of zoom */
  font-size: 12px; /* Increased from 8px */
  font-weight: bold;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.9); /* More opaque */
  padding: 2px 5px;
  border-radius: 3px;
  max-width: 100%; /* Increased from 90% */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  z-index: 3;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transform-origin: center center;
}

.fields-grid {
  display: flex;
  flex-direction: column;
  width: 98%;
  height: 98%;
  border: none; /* Removed border */
  border-radius: 2px;
  overflow: hidden;
}

.field-row {
  display: flex;
  flex: 1;
}

.field-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none; /* Removed border */
  background-color: rgba(139, 195, 74, 0.1);
  position: relative;
  font-size: 6px;
}

.field-coord {
  color: rgba(0, 0, 0, 0.7); /* Darker for better contrast */
  font-size: 10px; /* Increased from 5px for better readability */
  transform-origin: center center;
  background-color: rgba(255, 255, 255, 0.6); /* Background to improve readability */
  padding: 1px 2px;
  border-radius: 2px;
  z-index: 2;
}

.city-grid {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #FFE0B2; /* Light orange */
  border-radius: 1px;
  overflow: hidden;
}

.city-row {
  display: flex;
  flex: 1;
}

.city-cell {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  box-sizing: border-box;
}

/* Responsive styles */
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