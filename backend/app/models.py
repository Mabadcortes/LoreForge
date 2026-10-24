"""
LoreForge - Database Models
Defines relational database schemas for players, characters, and game state.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Character(Base):
    """
    Stores D&D 5e character attributes deterministically.
    Health points, inventory, and stats are managed here to prevent AI hallucination.
    """
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    # Core D&D 5e Identity
    race = Column(String(50), nullable=False)
    character_class = Column(String(50), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    
    # Core D&D 5e Attributes
    strength = Column(Integer, default=10, nullable=False)
    dexterity = Column(Integer, default=10, nullable=False)
    constitution = Column(Integer, default=10, nullable=False)
    intelligence = Column(Integer, default=10, nullable=False)
    wisdom = Column(Integer, default=10, nullable=False)
    charisma = Column(Integer, default=10, nullable=False)

    # Health and Combat State
    max_hp = Column(Integer, default=10, nullable=False)
    current_hp = Column(Integer, default=10, nullable=False)
    armor_class = Column(Integer, default=10, nullable=False)

    # Auditing timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())