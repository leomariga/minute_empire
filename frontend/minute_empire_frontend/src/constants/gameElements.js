/**
 * Game Elements Constants
 * Centralized definitions for all game element properties including:
 * - Buildings
 * - Resource fields
 * - Task types
 * - UI elements
 */

// Import images directly
import logoImage from '@/assets/logo.png';
import woodFieldImage from '@/assets/wood_field.png';
import foodFieldImage from '@/assets/food_field.png';
import stoneFieldImage from '@/assets/stone_field.png';
import ironFieldImage from '@/assets/iron_field.png';


// Image mapping
export const GAME_IMAGES = {
  'logo.png': logoImage,
  'wood_field.png': woodFieldImage,
  'food_field.png': foodFieldImage,
  'stone_field.png': stoneFieldImage,
  'iron_field.png': ironFieldImage,
};

// Building types with standardized properties
export const BUILDINGS = {
  CITY_CENTER: {
    id: 'city_center',
    name: 'Town Center',
    description: 'The heart of your village. Higher levels unlock more building slots and increase village capacity.',
    icon: 'mdi-home-city',
    color: '#795548', // Brown
    category: 'core',
    image: 'logo.png'
  },
  RALLY_POINT: {
    id: 'rally_point',
    name: 'Rally Point',
    description: 'Command center for your military. Higher levels allow larger armies and more simultaneous attacks.',
    icon: 'mdi-flag-outline',
    color: '#ff5722', // Deep orange
    category: 'military',
    image: 'logo.png'
  },
  BARRAKS: {
    id: 'barraks',
    name: 'Barracks',
    description: 'Train infantry units here. Higher levels unlock more powerful unit types and faster training.',
    icon: 'mdi-shield-outline',
    color: '#f44336', // Red
    category: 'military',
    image: 'logo.png'
  },
  ARCHERY: {
    id: 'archery',
    name: 'Archery Range',
    description: 'Train ranged units here. Higher levels unlock more powerful archer units and faster training.',
    icon: 'mdi-bow-arrow',
    color: '#9c27b0', // Purple
    category: 'military',
    image: 'logo.png'
  },
  STABLE: {
    id: 'stable',
    name: 'Stable',
    description: 'Train cavalry units here. Higher levels unlock more powerful mounted units and faster training.',
    icon: 'mdi-horse',
    color: '#8d6e63', // Brown
    category: 'military',
    image: 'logo.png'
  },
  WAREHOUSE: {
    id: 'warehouse',
    name: 'Warehouse',
    description: 'Store resources safely. Higher levels significantly increase the storage capacity for wood, stone, and iron.',
    icon: 'mdi-warehouse',
    color: '#607d8b', // Blue gray
    category: 'economy',
    image: 'logo.png'
  },
  GRANARY: {
    id: 'granary',
    name: 'Granary',
    description: 'Store food safely. Higher levels significantly increase the food storage capacity of your village.',
    icon: 'mdi-food-apple',
    color: '#8bc34a', // Light green
    category: 'economy',
    image: 'logo.png'
  },
  HIDE_SPOT: {
    id: 'hide_spot',
    name: 'Hide Spot',
    description: 'Conceals resources from attackers. Higher levels allow more resources to be hidden during enemy raids.',
    icon: 'mdi-eye-off-outline',
    color: '#455a64', // Dark blue gray
    category: 'defense',
    image: 'logo.png'
  },
  WALL: {
    id: 'wall',
    name: 'Wall',
    description: 'Provides defense against attacks. Higher levels increase village defense and enemy damage reduction.',
    icon: 'mdi-wall',
    color: '#78909c', // Blue gray
    category: 'defense',
    image: 'logo.png'
  }
};

// Resource field types with standardized properties
export const RESOURCE_FIELDS = {
  WOOD: {
    id: 'wood',
    name: 'Lumber Camp',
    description: 'Harvests wood from surrounding forests. Higher levels increase wood production rate.',
    icon: 'mdi-pine-tree',
    color: '#8d6e63', // Brown
    resourceColor: '#795548', // Darker brown
    image: 'wood_field.png'
  },
  STONE: {
    id: 'stone',
    name: 'Quarry',
    description: 'Extracts stone from rocky terrain. Higher levels increase stone production rate.',
    icon: 'mdi-hexagon-multiple',
    color: '#9e9e9e', // Gray
    resourceColor: '#616161', // Dark gray
    image: 'stone_field.png'
  },
  IRON: {
    id: 'iron',
    name: 'Iron Mine',
    description: 'Mines iron ore from mineral-rich ground. Higher levels increase iron production rate.',
    icon: 'mdi-anvil',
    color: '#78909c', // Blue-gray
    resourceColor: '#455a64', // Dark blue-gray
    image: 'iron_field.png'
  },
  FOOD: {
    id: 'food',
    name: 'Farm',
    description: 'Cultivates crops for food production. Higher levels increase food production rate.',
    icon: 'mdi-barley',
    color: '#aed581', // Light green
    resourceColor: '#7cb342', // Green
    image: 'food_field.png'
  }
};

// Task types with standardized properties
export const TASK_TYPES = {
  CREATE_BUILDING: {
    id: 'create_building',
    name: 'Construct Building',
    icon: 'mdi-hammer',
    color: '#2196f3', // Blue
    operationIcon: 'mdi-hammer',
    operationColor: '#3f51b5' // Indigo
  },
  UPGRADE_BUILDING: {
    id: 'upgrade_building',
    name: 'Upgrade Building',
    icon: 'mdi-office-building',
    color: '#ff9800', // Orange
    operationIcon: 'mdi-arrow-up-bold',
    operationColor: '#4caf50' // Green
  },
  CREATE_FIELD: {
    id: 'create_field',
    name: 'Clear Field',
    icon: 'mdi-shovel',
    color: '#8bc34a', // Light green
    operationIcon: 'mdi-hammer',
    operationColor: '#3f51b5' // Indigo
  },
  UPGRADE_FIELD: {
    id: 'upgrade_field',
    name: 'Upgrade Field',
    icon: 'mdi-grass',
    color: '#4caf50', // Green
    operationIcon: 'mdi-arrow-up-bold',
    operationColor: '#4caf50' // Green
  }
};

// Resource types with standardized properties
export const RESOURCES = {
  WOOD: {
    id: 'wood',
    name: 'Wood',
    description: 'Basic building material',
    icon: 'mdi-pine-tree',
    color: '#8bc34a', // Green
    iconBackgroundColor: 'rgba(139, 195, 74, 0.15)'
  },
  FOOD: {
    id: 'food',
    name: 'Food',
    description: 'Feeds your population',
    icon: 'mdi-barley',
    color: '#ffc107', // Amber
    iconBackgroundColor: 'rgba(255, 193, 7, 0.15)'
  },
  STONE: {
    id: 'stone',
    name: 'Stone',
    description: 'Used for advanced buildings',
    icon: 'mdi-hexagon-multiple',
    color: '#9e9e9e', // Gray
    iconBackgroundColor: 'rgba(158, 158, 158, 0.15)'
  },
  IRON: {
    id: 'iron',
    name: 'Iron',
    description: 'Used for military units and buildings',
    icon: 'mdi-anvil',
    color: '#42a5f5', // Blue
    iconBackgroundColor: 'rgba(66, 165, 245, 0.15)'
  }
};

// UI Colors for consistent styling across components
export const UI_COLORS = {
  // Background colors
  BACKGROUND: {
    PRIMARY: 'rgba(255, 255, 255, 0.95)',
    SECONDARY: 'rgba(245, 245, 245, 0.9)',
    DARK: 'rgba(33, 33, 33, 0.8)',
    TRANSPARENT: 'rgba(255, 255, 255, 0.2)'
  },
  // Text colors
  TEXT: {
    PRIMARY: 'rgba(33, 33, 33, 1)',
    SECONDARY: 'rgba(97, 97, 97, 1)',
    LIGHT: 'rgba(255, 255, 255, 0.9)',
    DARK: 'rgba(0, 0, 0, 0.8)'
  },
  // Border colors
  BORDER: {
    LIGHT: 'rgba(224, 224, 224, 1)',
    DARK: 'rgba(97, 97, 97, 0.5)',
    BLACK: 'rgba(0, 0, 0, 0.5)'
  },
  // Status colors
  STATUS: {
    SUCCESS: 'rgba(76, 175, 80, 0.8)',
    ERROR: 'rgba(244, 67, 54, 0.8)',
    WARNING: 'rgba(255, 152, 0, 0.8)',
    INFO: 'rgba(33, 150, 243, 0.8)'
  },
  // Map specific colors
  MAP: {
    GRID_FILL: 'rgba(255, 255, 255, 0.3)',
    GRID_STROKE: 'rgba(0, 0, 0, 1)',
    ENEMY_VILLAGE: 'rgba(158, 158, 158, 0.6)',
    EMPTY_SLOT: 'rgba(255, 255, 255, 0.2)',
    ENEMY_CITY: 'rgba(0, 0, 0, 0.8)'
  },
  // Dialog specific colors
  DIALOG: {
    BACKDROP: 'rgba(0, 0, 0, 0.5)',
    SHADOW: '0 4px 12px rgba(0, 0, 0, 0.15)',
    SHADOW_HOVER: '0 6px 16px rgba(0, 0, 0, 0.2)',
    INFO_ITEM_BG: 'rgba(0, 0, 0, 0.03)',
    EMPTY_ICON: 'rgba(158, 158, 158, 1)'
  }
};

/**
 * Helper functions to work with game elements
 */

// Get building info by ID (case insensitive)
export function getBuildingInfo(buildingId) {
  if (!buildingId) return null;
  
  const normalizedId = buildingId.toUpperCase();
  return BUILDINGS[normalizedId] || null;
}

// Get resource field info by ID (case insensitive)
export function getResourceFieldInfo(fieldId) {
  if (!fieldId) return null;
  
  const normalizedId = fieldId.toUpperCase();
  return RESOURCE_FIELDS[normalizedId] || null;
}

// Get task type info by ID (case insensitive)
export function getTaskTypeInfo(taskTypeId) {
  if (!taskTypeId) return null;
  
  const normalizedId = taskTypeId.toUpperCase();
  return TASK_TYPES[normalizedId] || null;
}

// Get resource info by ID (case insensitive)
export function getResourceInfo(resourceId) {
  if (!resourceId) return null;
  
  const normalizedId = resourceId.toUpperCase();
  return RESOURCES[normalizedId] || null;
}

// Get resource color with optional opacity
export function getResourceColor(resourceId, opacity = 1) {
  const resource = getResourceInfo(resourceId);
  if (!resource) return `rgba(255, 255, 255, ${opacity})`;
  
  // Convert hex to rgba
  const hex = resource.color;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Get resource icon
export function getResourceIcon(resourceId) {
  const resource = getResourceInfo(resourceId);
  return resource ? resource.icon : 'mdi-help-circle';
}

// Get proper display name for any game element type
export function getDisplayName(elementType, elementId) {
  if (!elementType || !elementId) return 'Unknown';
  
  switch (elementType.toLowerCase()) {
    case 'building':
      return getBuildingInfo(elementId)?.name || elementId;
    case 'field':
      return getResourceFieldInfo(elementId)?.name || elementId;
    case 'task':
      return getTaskTypeInfo(elementId)?.name || elementId;
    default:
      return elementId;
  }
}

// Format target type name for display (e.g. "city_center" → "Town Center")
export function formatTargetTypeName(targetType) {
  if (!targetType) return 'Unknown';
  
  // Try to match with building first
  for (const key in BUILDINGS) {
    if (BUILDINGS[key].id.toLowerCase() === targetType.toLowerCase()) {
      return BUILDINGS[key].name;
    }
  }
  
  // Then try resource fields
  for (const key in RESOURCE_FIELDS) {
    if (RESOURCE_FIELDS[key].id.toLowerCase() === targetType.toLowerCase()) {
      return RESOURCE_FIELDS[key].name;
    }
  }
  
  // If no match, format the raw string nicely
  return targetType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}

// Get building color with optional opacity
export function getBuildingColor(buildingId, opacity = 1) {
  const building = getBuildingInfo(buildingId);
  if (!building) return `rgba(255, 255, 255, ${opacity})`;
  
  // Convert hex to rgba
  const hex = building.color;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Get building icon
export function getBuildingIcon(buildingId) {
  const building = getBuildingInfo(buildingId);
  return building ? building.icon : 'mdi-help-circle';
}

// Get resource field image path
export function getResourceFieldImage(fieldId) {
  const field = getResourceFieldInfo(fieldId);
  return field ? field.image : 'logo.png';
}

// Get building image path
export function getBuildingImage(buildingId) {
  const building = getBuildingInfo(buildingId);
  return building ? building.image : 'logo.png';
}

// Get resource field image reference
export function getResourceFieldImageRef(fieldId) {
  const field = getResourceFieldInfo(fieldId);
  const imageName = field ? field.image : 'logo.png';
  return GAME_IMAGES[imageName] || GAME_IMAGES['logo.png'];
}

// Get building image reference
export function getBuildingImageRef(buildingId) {
  const building = getBuildingInfo(buildingId);
  const imageName = building ? building.image : 'logo.png';
  return GAME_IMAGES[imageName] || GAME_IMAGES['logo.png'];
} 