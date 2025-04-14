/**
 * Utility functions for troop movement and attack calculation
 */

/**
 * Get valid move positions for a troop based on its type and current location
 * 
 * @param {string} troopType - The type of troop (militia, archer, light_cavalry, pikeman)
 * @param {Object} currentLocation - The current location of the troop {x, y}
 * @param {Object} mapBounds - The map boundaries {x_min, x_max, y_min, y_max}
 * @returns {Array} Array of valid move positions as {x, y} objects
 */
export function getValidMoveSpots(troopType, currentLocation, mapBounds) {
  // Use the grid cell position (floor values to get cell origin)
  const x = Math.floor(currentLocation.x);
  const y = Math.floor(currentLocation.y);
  let validSpots = [];
  
  // Adjacent cells (orthogonal)
  const orthogonal = [
    { x: x, y: y + 1 },     // North
    { x: x, y: y - 1 },     // South
    { x: x + 1, y: y },     // East
    { x: x - 1, y: y }      // West
  ];
  
  // Diagonal cells
  const diagonal = [
    { x: x + 1, y: y + 1 }, // Northeast
    { x: x + 1, y: y - 1 }, // Southeast
    { x: x - 1, y: y + 1 }, // Northwest
    { x: x - 1, y: y - 1 }  // Southwest
  ];
  
  // L-shaped cells (knight's move in chess)
  const lShaped = [
    { x: x + 2, y: y + 1 },
    { x: x + 2, y: y - 1 },
    { x: x - 2, y: y + 1 },
    { x: x - 2, y: y - 1 },
    { x: x + 1, y: y + 2 },
    { x: x - 1, y: y + 2 },
    { x: x + 1, y: y - 2 },
    { x: x - 1, y: y - 2 }
  ];
  
  // Different movement patterns based on troop type
  switch(troopType) {
    case 'militia':
      // Militia: Adjacent cells including diagonals
      validSpots = [...orthogonal, ...diagonal];
      break;
      
    case 'archer':
      // Archer: Adjacent cells excluding diagonals
      validSpots = [...orthogonal];
      break;
      
    case 'light_cavalry':
      // Light Cavalry: L-shaped movement like knight in chess
      validSpots = [...lShaped];
      break;
      
    case 'pikeman':
      // Pikeman: Adjacent cells including diagonals + L-shaped cells
      validSpots = [...orthogonal, ...diagonal, ...lShaped];
      break;
      
    default:
      console.warn(`Unknown troop type: ${troopType}`);
      return [];
  }
  
  // Filter out the current position if it's in the valid spots
  validSpots = validSpots.filter(spot => !(spot.x === x && spot.y === y));
  
  // Filter out spots outside map bounds
  return validSpots.filter(spot => 
    spot.x >= mapBounds.x_min && 
    spot.x <= mapBounds.x_max && 
    spot.y >= mapBounds.y_min && 
    spot.y <= mapBounds.y_max
  );
}

/**
 * Get valid attack positions for a troop based on its type and current location
 * 
 * @param {string} troopType - The type of troop (militia, archer, light_cavalry, pikeman)
 * @param {Object} currentLocation - The current location of the troop {x, y}
 * @param {Object} mapBounds - The map boundaries {x_min, x_max, y_min, y_max}
 * @returns {Array} Array of valid attack positions as {x, y} objects
 */
export function getValidAttackSpots(troopType, currentLocation, mapBounds) {
  // Use the grid cell position (floor values to get cell origin)
  const x = Math.floor(currentLocation.x);
  const y = Math.floor(currentLocation.y);
  let validSpots = [];
  
  // Current cell
  const current = [
    { x: x, y: y }
  ];
  
  // Adjacent cells (orthogonal)
  const orthogonal = [
    { x: x, y: y + 1 },     // North
    { x: x, y: y - 1 },     // South
    { x: x + 1, y: y },     // East
    { x: x - 1, y: y }      // West
  ];
  
  // Diagonal cells
  const diagonal = [
    { x: x + 1, y: y + 1 }, // Northeast
    { x: x + 1, y: y - 1 }, // Southeast
    { x: x - 1, y: y + 1 }, // Northwest
    { x: x - 1, y: y - 1 }  // Southwest
  ];
  
  // L-shaped cells (knight's move in chess)
  const lShaped = [
    { x: x + 2, y: y + 1 },
    { x: x + 2, y: y - 1 },
    { x: x - 2, y: y + 1 },
    { x: x - 2, y: y - 1 },
    { x: x + 1, y: y + 2 },
    { x: x - 1, y: y + 2 },
    { x: x + 1, y: y - 2 },
    { x: x - 1, y: y - 2 }
  ];
  
  // Different attack patterns based on troop type
  switch(troopType) {
    case 'militia':
      // Militia: Only current cell (must move to attack)
      validSpots = [...current];
      break;
      
    case 'archer':
      // Archer: Adjacent cells including diagonals
      validSpots = [...orthogonal, ...diagonal];
      break;
      
    case 'light_cavalry':
      // Light Cavalry: Only current cell (must move to attack)
      validSpots = [...current];
      break;
      
    case 'pikeman':
      // Pikeman: L-shaped cells + current cell
      validSpots = [...current, ...lShaped];
      break;
      
    default:
      console.warn(`Unknown troop type: ${troopType}`);
      return [];
  }
  
  // Filter out spots outside map bounds
  return validSpots.filter(spot => 
    spot.x >= mapBounds.x_min && 
    spot.x <= mapBounds.x_max && 
    spot.y >= mapBounds.y_min && 
    spot.y <= mapBounds.y_max
  );
} 