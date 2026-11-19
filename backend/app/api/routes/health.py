import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health(session: SessionDep, response: Response) -> HealthResponse:
    """Report whether the API is up and can reach the database."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        # A health check must never raise: any failure means "unavailable".
        # The details (host, user, driver message) go to the log only; the
        # client gets a generic body so no internals leak.
        logger.exception("Health check failed: database is unreachable")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="error", database="unavailable")
    return HealthResponse(status="ok", database="ok")
