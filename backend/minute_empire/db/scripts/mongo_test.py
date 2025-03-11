#!/usr/bin/env python
"""
MongoDB User Management Test Script

This script demonstrates how to use the mongodb utility module to perform 
basic MongoDB operations like creating and retrieving users.
"""

import os
import sys
import asyncio
from pprint import pprint
from datetime import datetime

# Import our utility module
from minute_empire.db.mongodb import (
    get_sync_client, 
    get_sync_database,
    close_sync_connection,
    create_user_sync,
    get_all_users_sync,
    connect_to_mongodb,
    close_mongodb_connection,
    create_user_async,
    get_all_users_async
)

def test_sync_operations():
    """Test synchronous MongoDB operations."""
    print("\n=== Testing Synchronous MongoDB Operations ===\n")
    
    try:
        # Connect to MongoDB
        client = get_sync_client()
        
        # Create some test users
        create_user_sync("john_doe", "password123", "john@example.com")
        create_user_sync("jane_smith", "secure456", "jane@example.com")
        create_user_sync("admin_user", "admin789", "admin@example.com", "admin")
        
        # Get all users
        print("\nRetrieving all users:")
        users = get_all_users_sync()
        for user in users:
            pprint(user)
        
        # Close the connection
        close_sync_connection()
        print("\nSynchronous MongoDB operations completed successfully")
        
    except Exception as e:
        print(f"Error in synchronous operations: {e}")
        sys.exit(1)

async def test_async_operations():
    """Test asynchronous MongoDB operations."""
    print("\n=== Testing Asynchronous MongoDB Operations ===\n")
    
    try:
        # Connect to MongoDB
        await connect_to_mongodb()
        
        # Create some test users
        await create_user_async("async_john", "password123", "async_john@example.com")
        await create_user_async("async_jane", "secure456", "async_jane@example.com")
        await create_user_async("async_admin", "admin789", "async_admin@example.com", "admin")
        
        # Get all users
        print("\nRetrieving all users asynchronously:")
        users = await get_all_users_async()
        for user in users:
            pprint(user)
        
        # Close the connection
        await close_mongodb_connection()
        print("\nAsynchronous MongoDB operations completed successfully")
        
    except Exception as e:
        print(f"Error in asynchronous operations: {e}")
        sys.exit(1)

def main():
    """Main function to demonstrate MongoDB operations."""
    # Test synchronous operations
    #test_sync_operations()
    
    # Test asynchronous operations
    asyncio.run(test_async_operations())
    
    print("\nAll MongoDB tests completed successfully")

if __name__ == "__main__":
    main()
