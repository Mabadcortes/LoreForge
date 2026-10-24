"""LoreForge - Pydantic Schemas
Defines request and response validation contracts for API endpoints."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CharacterBase(BaseModel):
    # Shared attributes across creation and retrieval models.
    name: str = Field(..., max_length=100, description="Name of the character.")
    race: str = Field(..., max_length=50, description="D&D 5e race of the character.")
    character_class: str = Field(..., max_length=50, description="D&D 5e class of the character.")
    level: int = Field(default=1, ge=1, le=20, description="Level of the character between 1 and 20.")

    # Core D&D 5e Attributes (1-30)
    strength: int = Field(default=10, ge=1, le=30, description="Strength attribute (1-30).")
    dexterity: int = Field(default=10, ge=1, le=30, description="Dexterity attribute (1-30).")
    constitution: int = Field(default=10, ge=1, le=30, description="Constitution attribute (1-30).")
    intelligence: int = Field(default=10, ge=1, le=30, description="Intelligence attribute (1-30).")
    wisdom: int = Field(default=10, ge=1, le=30, description="Wisdom attribute (1-30).")
    charisma: int = Field(default=10, ge=1, le=30, description="Charisma attribute (1-30).")

    # Health and Armor Class
    max_hp: int = Field(default=10, ge=1, description="Maximum health points of the character.")
    current_hp: int = Field(default=10, ge=0, description="Current health points of the character.")
    armor_class: int = Field(default=10, ge=1, description="Armor class of the character.")


class CharacterCreate(CharacterBase):
    """Schema required in the request body when creating a new character.
    Inherits all fields from CharacterBase without requiring an ID."""
    pass


class CharacterResponse(CharacterBase):
    """Schema returned to clients when retrieving character data.
    Includes the unique ID and creation timestamp."""
    id: int
    created_at: datetime

    # Tells pydantic to read data directly from SQLAlchemy ORM objects.
    model_config = ConfigDict(from_attributes=True)


# =============================================================
# Gameplay & Rules Engine Schemas
# =============================================================

class AbilityCheckRequest(BaseModel):
    """Payload to perform an ability check using character stats."""
    ability: str = Field(..., description="Ability to check: strength, dexterity, constitution, intelligence, wisdom, charisma")
    difficulty_class: Optional[int] = Field(default=None, ge=1, le=40, description="Optional DC to compare against")
    advantage: bool = Field(default=False, description="Roll twice and take highest")
    disadvantage: bool = Field(default=False, description="Roll twice and take lowest")

class AbilityCheckResponse(BaseModel):
    """Result of an ability check execution."""
    character_name: str
    ability: str
    base_score: int
    modifier: int
    raw_rolls: List[int]
    chosen_dice: int
    total: int
    roll_type: str
    is_critical_success: bool
    is_critical_failure: bool
    success: Optional[bool] = None

class HPModifyRequest(BaseModel):
    """Request payload to modify a character's health points (HP)."""
    amount: int = Field(..., gt=0, description="Positive amount of damage or healing points")
    is_healing: bool = Field(default=False, description="True for healing, False for damage")


class HPModifyResponse(BaseModel):
    """State of character health after adjustment."""
    character_id: int
    character_name: str
    previous_hp: int
    new_hp: int
    max_hp: int
    is_knocked_out: bool