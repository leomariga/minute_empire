#!/usr/bin/env python
"""
MongoDB User and Village Management Test Script

This script demonstrates how to use the mongodb utility module to perform 
basic MongoDB operations like creating users and villages.
"""

import os
import sys
import asyncio
from pprint import pprint
from datetime import datetime

# Import our utility module
from minute_empire.db.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    create_user,
    initialize_village,
    get_all_users
)
from minute_empire.schemas.schemas import (
    UserInDB,
    VillageInDB,
    Location, 
    TroopType, 
    TroopMode, 
    ResourceFieldType
)

async def test_operations():
    """Test MongoDB operations."""
    print("\n=== Testing MongoDB Operations ===\n")
    
    try:
        # Connect to MongoDB
        await connect_to_mongodb()
        
        # Create a test user with a village
        print("\nCreating test user...")
        try:
            # Create the user with individual parameters
            user = await create_user(
                username="empire_lord",
                password="secure123",
                family_name="Stark",
                color="#FF0000"  # Red color for the empire
            )
            print(f"Created user: {user['username']}")
            pprint(user)
        except ValueError as e:
            print(f"Note: {e}")
            # If user already exists, continue with the test
        
        # Get all users to find the empire_lord user
        print("\nRetrieving all users:")
        users = await get_all_users()
        empire_user = None
        for user in users:
            if user["username"] == "empire_lord":
                empire_user = user
                pprint(user)
        
        if not empire_user:
            raise ValueError("Could not find the empire_lord user!")
        
        # Create a village for the user
        print("\nCreating village for user...")
        try:
            village_location = Location(x=10, y=10)  # Starting coordinates
            village = await initialize_village(
                owner_id=empire_user["_id"],
                name="Winterfell",
                location=village_location
            )
            print(f"Created village for user {empire_user['username']}:")
            pprint(village.dict(by_alias=True))
        except ValueError as e:
            print(f"Note: {e}")
            # If village already exists at this location, continue

        # Close the connection
        await close_mongodb_connection()
        print("\nMongoDB operations completed successfully")
        
    except Exception as e:
        print(f"Error in operations: {e}")
        sys.exit(1)

async def main():
    """Main function to demonstrate MongoDB operations."""
    await test_operations()
    print("\nAll MongoDB tests completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
