# Minute Empire Domain Model Guide

This guide explains how to use the domain-driven design (DDD) approach implemented in the Minute Empire game.

## Overview

The project follows a layered architecture:

1. **Schemas Layer**: Pydantic models for data validation and serialization
2. **Domain Layer**: Business logic and behavior
3. **Repository Layer**: Data access and persistence (using context managers)
4. **Service Layer**: Complex operations and workflows

## Database Access Pattern

The project uses a context manager pattern for database access, ensuring connections are properly managed:

```python
# In mongodb.py
@asynccontextmanager
async def get_db():
    """Context manager for database connections.
    
    Usage:
        async with get_db() as db:
            result = await db.collection.find_one(...)
    """
    client = AsyncIOMotorClient(MONGODB_URI)
    try:
        db = client[DATABASE_NAME]
        yield db
    finally:
        client.close()
```

Repositories use this context manager internally for each database operation, ensuring that:
- Connections are opened only when needed
- Connections are automatically closed after each operation
- Resource cleanup happens even if exceptions occur

## How to Use Domain Models

### Village Operations

```python
# Import what you need
from minute_empire.domain import Village
from minute_empire.repositories import VillageRepository
from minute_empire.services import ResourceService

async def example_village_operations():
    # Initialize repository
    village_repo = VillageRepository()
    
    # Get a village by ID
    village = await village_repo.get_by_id("village_id_here")
    
    # Access village properties
    print(f"Village name: {village.name}")
    print(f"Village location: {village.location}")
    print(f"Wood: {getattr(village.resources, 'wood', 0)}")
    
    # Calculate resource production rates
    rates = village.get_resource_rates()
    print(f"Production rates: {rates}")
    
    # Get a building by slot number
    building = village.get_building(1)  # Slot 1 typically contains the city center
    
    # Upgrade a building if possible
    if building and building.can_upgrade():
        building.upgrade()
        print(f"Upgraded {building.type} to level {building.level}")
        
    # Mark village as changed and save to database
    village.mark_as_changed()
    await village_repo.save(village)
```

### Using Services for Complex Operations

```python
# Import services
from minute_empire.services import ResourceService, BuildingService

async def example_service_operations():
    # Initialize services
    resource_service = ResourceService()
    building_service = BuildingService()
    
    # Update all resources for a user's villages
    updated_villages = await resource_service.update_all_user_villages("user_id_here")
    
    # Upgrade a building
    result = await building_service.upgrade_building("village_id_here", 2)  # Upgrade building in slot 2
    
    if result["success"]:
        print(f"Successfully upgraded building to level {result['new_level']}")
    else:
        print(f"Upgrade failed: {result['error']}")
        if "missing" in result:
            print(f"Missing resources: {result['missing']}")
```

## Domain Model Overview

### Village (domain/village.py)

The core entity representing a player's village.

Key methods:
- `get_building(slot)`: Get a building by slot number
- `get_resource_field(slot)`: Get a resource field by slot number
- `get_resource_rates()`: Calculate hourly production rates
- `update_resources(time_elapsed_hours)`: Update resources based on elapsed time

### Building (domain/building.py)

Represents a building in a village.

Key methods:
- `get_upgrade_cost()`: Calculate upgrade cost based on type and level
- `can_upgrade()`: Check if requirements are met
- `upgrade()`: Perform the upgrade if possible

### ResourceProducer (domain/resource.py)

Represents a resource field in a village.

Key methods:
- `production_rate`: Calculate hourly production based on level
- `get_upgrade_cost()`: Calculate upgrade cost
- `upgrade()`: Perform the upgrade if possible

## Repositories

Repositories handle data access using the context manager pattern:

```python
# Example repository method
async def get_by_id(self, entity_id: str) -> Optional[Entity]:
    """Get entity by ID"""
    async with get_db() as db:
        data = await db[self.COLLECTION].find_one({"_id": entity_id})
        if data is None:
            return None
        
        model = EntityInDB(**data)
        return Entity(model)
```

Available repositories:
- `VillageRepository`: CRUD operations for villages
- `UserRepository`: CRUD operations for users

## Services

Services handle complex operations:

- `ResourceService`: Resource calculations and updates
- `BuildingService`: Building operations like upgrading and construction
- `AuthenticationService`: User authentication and token management
- `RegistrationService`: User and village registration workflow

## Error Handling

The application uses defensive programming to handle potential errors:

```python
# Example of safe method with proper error handling
def get_resource_rates(self) -> Dict[str, float]:
    """Calculate hourly production rates for all resources"""
    # Default rates in case of errors
    rates = {
        "wood": 0,
        "stone": 0, 
        "iron": 0,
        "food": 0
    }
    
    # Safely try to calculate actual rates
    try:
        for field in self.get_all_resource_fields():
            resource_type = field.type.value
            rates[resource_type] += field.production_rate
    except Exception:
        # Fall back to defaults if any error occurs
        pass
        
    return rates
```

## Best Practices

1. Always use domain objects (Village, Building) when working with game logic
2. Use repositories for database operations
3. Use services for complex workflows
4. Keep domain logic in domain classes
5. Access properties safely using `getattr(obj, "property", default_value)`
6. Use the context manager pattern for all database operations
7. Implement proper error handling with fallback values
8. Log errors to help with debugging but continue operation when possible 