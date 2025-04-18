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
import emptyFieldImage from '@/assets/empty_field.png';


// Image mapping
export const GAME_IMAGES = {
  'logo.png': logoImage,
  'wood_field.png': woodFieldImage,
  'food_field.png': foodFieldImage,
  'stone_field.png': stoneFieldImage,
  'iron_field.png': ironFieldImage,
  'empty_field.png': emptyFieldImage,
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
    image: 'logo.png',
    buildingTypes: ['resource_bonus']
  },
  RALLY_POINT: {
    id: 'rally_point',
    name: 'Rally Point',
    description: 'Command center for your military. Higher levels allow larger armies and more simultaneous attacks.',
    icon: 'mdi-flag',
    color: '#ff5722', // Deep orange
    category: 'military',
    image: 'logo.png',
    buildingTypes: ['troop_command']
  },
  BARRAKS: {
    id: 'barraks',
    name: 'Barracks',
    description: 'Train infantry units here. Higher levels unlock more powerful unit types and faster training.',
    icon: 'mdi-shield',
    color: '#f44336', // Red
    category: 'military',
    image: 'logo.png',
    buildingTypes: ['troop_training'],
    troops: ['militia']
  },
  ARCHERY: {
    id: 'archery',
    name: 'Archery Range',
    description: 'Train ranged units here. Higher levels unlock more powerful archer units and faster training.',
    icon: 'mdi-bow-arrow',
    color: '#9c27b0', // Purple
    category: 'military',
    image: 'logo.png',
    buildingTypes: ['troop_training'],
    troops: ['archer']
  },
  STABLE: {
    id: 'stable',
    name: 'Stable',
    description: 'Train cavalry units here. Higher levels unlock more powerful mounted units and faster training.',
    icon: 'mdi-horse-variant',
    color: '#8d6e63', // Brown
    category: 'military',
    image: 'logo.png',
    buildingTypes: ['troop_training'],
    troops: ['light_cavalry']
  },
  WAREHOUSE: {
    id: 'warehouse',
    name: 'Warehouse',
    description: 'Store resources safely. Higher levels significantly increase the storage capacity for wood, stone, and iron.',
    icon: 'mdi-warehouse',
    color: '#607d8b', // Blue gray
    category: 'economy',
    image: 'logo.png',
    buildingTypes: ['resource_storage']
  },
  GRANARY: {
    id: 'granary',
    name: 'Granary',
    description: 'Store food safely. Higher levels significantly increase the food storage capacity of your village.',
    icon: 'mdi-hoop-house',
    color: '#8bc34a', // Light green
    category: 'economy',
    image: 'logo.png',
    buildingTypes: ['resource_storage']
  },
  HIDE_SPOT: {
    id: 'hide_spot',
    name: 'Hide Spot',
    description: 'Conceals resources from attackers. Higher levels allow more resources to be hidden during enemy raids.',
    icon: 'mdi-eye-off-outline',
    color: '#455a64', // Dark blue gray
    category: 'defense',
    image: 'logo.png',
    buildingTypes: ['defense']
  },
  WALL: {
    id: 'wall',
    name: 'Wall',
    description: 'Provides defense against attacks. Higher levels increase village defense and enemy damage reduction.',
    icon: 'mdi-wall',
    color: '#78909c', // Blue gray
    category: 'defense',
    image: 'logo.png',
    buildingTypes: ['defense']
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

// Troop types with standardized properties
export const TROOP_TYPES = {
  MILITIA: {
    id: 'militia',
    name: 'Militia',
    description: 'Basic infantry unit with balanced offense and defense',
    icon: 'mdi-sword',
    color: '#f44336', // Red
    category: 'military'
  },
  ARCHER: {
    id: 'archer',
    name: 'Archer',
    description: 'Ranged unit with good offense but weak defense',
    icon: 'mdi-bow-arrow',
    color: '#9c27b0', // Purple
    category: 'military'
  },
  LIGHT_CAVALRY: {
    id: 'light_cavalry',
    name: 'Light Cavalry',
    description: 'Fast moving mounted unit with strong offense',
    icon: 'mdi-horse',
    color: '#8d6e63', // Brown
    category: 'military'
  },
  PIKEMAN: {
    id: 'pikeman',
    name: 'Pikeman',
    description: 'Anti-cavalry unit with strong defense',
    icon: 'mdi-spear',
    color: '#03a9f4', // Light blue
    category: 'military'
  }
};

// Troop status types with standardized properties
export const TROOP_STATUS = {
  IDLE: {
    id: 'idle',
    name: 'Idle',
    description: 'Troop is not engaged in any action',
    icon: 'mdi-clock-outline',
    color: '#757575', // Gray
    actionText: 'Standing by'
  },
  MOVE: {
    id: 'move',
    name: 'Move',
    description: 'Troop is moving to a destination',
    icon: 'mdi-map-marker-path',
    color: '#2196f3', // Blue
    actionText: 'Moving to destination'
  },
  ATTACK: {
    id: 'attack',
    name: 'Attack',
    description: 'Troop is attacking a target',
    icon: 'mdi-sword-cross',
    color: '#f44336', // Red
    actionText: 'Attacking target'
  },
  DEFEND: {
    id: 'defend',
    name: 'Defend',
    description: 'Troop is defending a position',
    icon: 'mdi-shield',
    color: '#ff9800', // Orange
    actionText: 'Defending position'
  },
  RETURN: {
    id: 'return',
    name: 'Return',
    description: 'Troop is returning to home village',
    icon: 'mdi-home-import-outline',
    color: '#4caf50', // Green
    actionText: 'Returning to home village'
  }
};

// Friendly status types for ownership indication
export const FRIENDLY_STATUS = {
  MYSELF: {
    id: 'myself',
    name: 'My Troops',
    description: 'Troops owned by the current player',
    color: '#000000', // Black
    textColor: 'rgba(0, 0, 0, 0.87)' // Full opacity black for text
  },
  ENEMY: {
    id: 'enemy',
    name: 'Enemy Troops',
    description: 'Troops owned by enemies',
    color: '#f44336', // Red (from ATTACK status)
    textColor: '#f44336' // Same red for text
  },
  ALLY: {
    id: 'ally',
    name: 'Allied Troops',
    description: 'Troops owned by allies (not used yet)',
    color: '#4caf50', // Green (from RETURN status)
    textColor: '#4caf50' // Same green for text
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
  if (!fieldId) return 'empty_field.png';
  const field = getResourceFieldInfo(fieldId);
  return field ? field.image : 'empty_field.png';
}

// Get building image path
export function getBuildingImage(buildingId) {
  const building = getBuildingInfo(buildingId);
  return building ? building.image : 'logo.png';
}

// Get resource field image reference
export function getResourceFieldImageRef(fieldId) {
  if (!fieldId) return GAME_IMAGES['empty_field.png'];
  const field = getResourceFieldInfo(fieldId);
  const imageName = field ? field.image : 'empty_field.png';
  return GAME_IMAGES[imageName] || GAME_IMAGES['empty_field.png'];
}

// Get building image reference
export function getBuildingImageRef(buildingId) {
  const building = getBuildingInfo(buildingId);
  const imageName = building ? building.image : 'logo.png';
  return GAME_IMAGES[imageName] || GAME_IMAGES['logo.png'];
}

// Get troop info by ID (case insensitive)
export function getTroopInfo(troopId) {
  if (!troopId) return null;
  
  const normalizedId = troopId.toUpperCase();
  return TROOP_TYPES[normalizedId] || null;
}

// Get troop status info by ID (case insensitive)
export function getTroopStatusInfo(statusId) {
  if (!statusId) return TROOP_STATUS.IDLE;
  
  const normalizedId = statusId.toUpperCase();
  return TROOP_STATUS[normalizedId] || null;
}

// Get troop icon by ID
export function getTroopIcon(troopId) {
  const troop = getTroopInfo(troopId);
  return troop ? troop.icon : 'mdi-help-circle';
}

// Get troop status icon by ID
export function getTroopStatusIcon(statusId) {
  const status = getTroopStatusInfo(statusId);
  return status ? status.icon : TROOP_STATUS.IDLE.icon;
}

// Get troop color with optional opacity
export function getTroopColor(troopId, opacity = 1) {
  const troop = getTroopInfo(troopId);
  if (!troop) return `rgba(0, 0, 0, ${opacity})`;
  
  // Convert hex to rgba
  const hex = troop.color;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Get troop status color with optional opacity
export function getTroopStatusColor(statusId, opacity = 1) {
  const status = getTroopStatusInfo(statusId);
  if (!status) return `rgba(117, 117, 117, ${opacity})`; // Default to gray
  
  // Convert hex to rgba
  const hex = status.color;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Get a proper display name for a troop type
export function getTroopTypeName(troopType) {
  if (!troopType) return 'Unknown Troop';
  
  // Try to get name from TROOP_TYPES
  const troopInfo = getTroopInfo(troopType);
  if (troopInfo) return troopInfo.name;
  
  // Fallback to formatting the string
  return troopType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}

// Convert troop mode to proper display format
export function getTroopStatus(mode) {
  if (!mode) return TROOP_STATUS.IDLE.name;
  
  const statusInfo = getTroopStatusInfo(mode);
  return statusInfo ? statusInfo.name : mode;
}

// Get a descriptive action status message for a troop mode
export function getTroopActionDescription(mode) {
  if (!mode) return '';
  
  const statusInfo = getTroopStatusInfo(mode);
  return statusInfo ? statusInfo.actionText : mode;
}

// Get friendly status info
export function getFriendlyStatusInfo(statusId) {
  if (!statusId) return FRIENDLY_STATUS.MYSELF;
  
  const normalizedId = statusId.toUpperCase();
  return FRIENDLY_STATUS[normalizedId] || FRIENDLY_STATUS.MYSELF;
}

// Get friendly status color
export function getFriendlyStatusColor(statusId) {
  const status = getFriendlyStatusInfo(statusId);
  return status.color;
}

// Get friendly status text color
export function getFriendlyStatusTextColor(statusId) {
  const status = getFriendlyStatusInfo(statusId);
  return status.textColor;
} 