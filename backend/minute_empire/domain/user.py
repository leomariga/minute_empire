from datetime import datetime
from typing import Dict, List, Optional, Any
from minute_empire.schemas.schemas import UserInDB

class User:
    """Domain class for users with game logic"""
    
    def __init__(self, user_data: UserInDB):
        self._data = user_data
        self._changed = False
        
    @property
    def id(self) -> str:
        """User ID"""
        return self._data.id
    
    @property
    def username(self) -> str:
        """Username"""
        return self._data.username
    
    @property
    def family_name(self) -> str:
        """Family name"""
        return self._data.family_name
    
    @property
    def color(self) -> str:
        """User color"""
        return self._data.color
    
    @property
    def created_at(self) -> datetime:
        """User creation time"""
        return self._data.created_at
    
    @property
    def updated_at(self) -> datetime:
        """Last update time"""
        return self._data.updated_at
    
    def update_family_name(self, new_name: str) -> bool:
        """Update the family name"""
        if len(new_name) < 2 or len(new_name) > 50:
            return False
            
        self._data.family_name = new_name
        self.mark_as_changed()
        return True
    
    def update_color(self, new_color: str) -> bool:
        """Update the user color"""
        import re
        # Validate hex color
        if not re.match(r'^#[0-9a-fA-F]{6}$', new_color):
            return False
            
        self._data.color = new_color
        self.mark_as_changed()
        return True
    
    def mark_as_changed(self) -> None:
        """Mark that this user needs to be saved to database"""
        self._changed = True
        # Update the timestamp
        self._data.updated_at = datetime.utcnow()
    
    def has_changes(self) -> bool:
        """Check if user has unsaved changes"""
        return self._changed
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary for storage or API responses"""
        data = self._data.dict(by_alias=True)
        if not include_password:
            data.pop('password', None)
        return data
    
    def get_public_info(self) -> Dict[str, Any]:
        """Get public information about the user"""
        return {
            "id": self.id,
            "username": self.username,
            "family_name": self.family_name,
            "color": self.color,
            "created_at": self.created_at
        }
    
    def __str__(self) -> str:
        return f"User: {self.username} ({self.family_name})" 