#!/usr/bin/env python
"""
MongoDB Database Cleanup Script

This script safely cleans all collections in the MongoDB database.
It includes confirmation prompts and proper connection handling.
"""

import os
import sys
import asyncio
from typing import List
from datetime import datetime

from minute_empire.db.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    MONGO_DB
)

def get_confirmation(database_name: str) -> bool:
    """Get user confirmation before proceeding with database cleanup."""
    print(f"\n⚠️  WARNING: You are about to delete all data from database '{database_name}'!")
    print("This action cannot be undone!")
    
    confirmation = input("\nType the database name to confirm deletion: ")
    return confirmation.strip() == database_name

async def clean_database() -> None:
    """Clean all collections in the database asynchronously."""
    try:
        # Connect to MongoDB
        db = await connect_to_mongodb()
        
        # Get all collection names
        collections = await db.list_collection_names()
        
        if not collections:
            print(f"\nDatabase '{MONGO_DB}' is already empty.")
            return
        
        # Show current collections and their document counts
        print("\nCurrent collections:")
        for collection_name in collections:
            count = await db[collection_name].count_documents({})
            print(f"- {collection_name}: {count} documents")
        
        # Get confirmation
        if not get_confirmation(MONGO_DB):
            print("\n❌ Cleanup cancelled.")
            return
        
        # Drop each collection
        print("\nCleaning database...")
        for collection_name in collections:
            print(f"Dropping collection '{collection_name}'...")
            await db[collection_name].drop()
        
        print(f"\n✅ Successfully cleaned database '{MONGO_DB}'")
        
    except Exception as e:
        print(f"\n❌ Error cleaning database: {e}")
        sys.exit(1)
    finally:
        await close_mongodb_connection()

async def main():
    """Main function to clean the database."""
    print("\n=== MongoDB Database Cleanup ===")
    await clean_database()

if __name__ == "__main__":
    asyncio.run(main()) 