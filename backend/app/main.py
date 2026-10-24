"""
LoreForge - Main Application Entrypoint
Exposes system health probes and character management endpoints.
"""

from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base, get_db
import app.models as models
import app.schemas as schemas
import app.rules as rules

# Ensure all relational tables exist upon startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LoreForge API",
    description="AI-driven Tabletop RPG and Dungeon Master Engine",
    version="0.1.0"
)

# Enable CORS for client applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """
    Root probe endpoint.
    """
    return {
        "status": "online",
        "service": "LoreForge Engine",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Performs active database connectivity diagnostics.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unreachable: {str(exc)}"

    return {
        "status": "healthy",
        "database": db_status
    }


# =============================================================
# Character Management Routes
# =============================================================

@app.post(
    "/characters/",
    response_model=schemas.CharacterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new adventurer"
)
def create_character(
    character_in: schemas.CharacterCreate,
    db: Session = Depends(get_db)
):
    """
    Persists a new character sheet into the PostgreSQL database.
    Prevents stat manipulation and validates ability score bounds.
    """
    new_character = models.Character(**character_in.model_dump())
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    return new_character


@app.get(
    "/characters/",
    response_model=List[schemas.CharacterResponse],
    summary="Retrieve all registered characters"
)
def list_characters(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Fetches a paginated list of active characters.
    """
    characters = db.query(models.Character).offset(skip).limit(limit).all()
    return characters


@app.get(
    "/characters/{character_id}",
    response_model=schemas.CharacterResponse,
    summary="Fetch character by unique ID"
)
def get_character(
    character_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves a specific character sheet. Returns 404 if not found.
    """
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character with ID {character_id} not found."
        )
    return character

# =============================================================
# Deterministic Gameplay Mechanics Routes
# =============================================================

@app.post(
    "/characters/{character_id}/check",
    response_model=schemas.AbilityCheckResponse,
    summary="Perform an ability check (D20 + stat modifier)"
)
def perform_ability_check(
    character_id: int,
    check_in: schemas.AbilityCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a rule-compliant ability check against a character's stored statistics.
    Prevents stat spoofing by querying ability scores directly from PostgreSQL.
    """
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character with ID {character_id} not found."
        )

    # Normalize ability attribute lookup
    ability_key = check_in.ability.lower()
    if not hasattr(character, ability_key):
        valid_abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ability '{check_in.ability}'. Must be one of: {', '.join(valid_abilities)}"
        )

    base_score = getattr(character, ability_key)
    modifier = rules.calculate_modifier(base_score)

    chosen_dice, raw_rolls, roll_type = rules.roll_d20(check_in.advantage, check_in.disadvantage)
    
    total = chosen_dice + modifier
    is_crit_success = (chosen_dice == 20)
    is_crit_failure = (chosen_dice == 1)

    # Evaluate against Difficulty Class (DC) if specified
    success_verdict = None
    if check_in.difficulty_class is not None:
        if is_crit_success:
            success_verdict = True
        elif is_crit_failure:
            success_verdict = False
        else:
            success_verdict = (total >= check_in.difficulty_class)

    return schemas.AbilityCheckResponse(
        character_name=character.name,
        ability=ability_key,
        base_score=base_score,
        modifier=modifier,
        raw_rolls=raw_rolls,
        chosen_dice=chosen_dice,
        total=total,
        roll_type=roll_type,
        is_critical_success=is_crit_success,
        is_critical_failure=is_crit_failure,
        success=success_verdict
    )


@app.post(
    "/characters/{character_id}/hp",
    response_model=schemas.HPModifyResponse,
    summary="Apply damage or healing to character"
)
def modify_character_hp(
    character_id: int,
    hp_in: schemas.HPModifyRequest,
    db: Session = Depends(get_db)
):
    """
    Applies health adjustments to a character with boundary enforcement (0 <= HP <= max_hp).
    Commits state immediately to the PostgreSQL database.
    """
    character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character with ID {character_id} not found."
        )

    previous_hp = character.current_hp
    new_hp = rules.apply_hp_change(
        current_hp=previous_hp,
        max_hp=character.max_hp,
        amount=hp_in.amount,
        is_healing=hp_in.is_healing
    )

    character.current_hp = new_hp
    db.commit()
    db.refresh(character)

    return schemas.HPModifyResponse(
        character_id=character.id,
        character_name=character.name,
        previous_hp=previous_hp,
        new_hp=new_hp,
        max_hp=character.max_hp,
        is_knocked_out=(new_hp == 0)
    )