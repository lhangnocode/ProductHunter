from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.advisor import AdvisorChatRequest, AdvisorChatResponse
from app.services.advisor import (
    AdvisorConfigurationError,
    AdvisorProviderError,
    AdvisorRetrievalError,
    answer_advisor_chat,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=AdvisorChatResponse)
async def advisor_chat(
    request: AdvisorChatRequest,
    db: AsyncSession = Depends(get_db),
) -> AdvisorChatResponse:
    try:
        return await answer_advisor_chat(request, db)
    except AdvisorConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AdvisorProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except AdvisorRetrievalError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unhandled advisor chat failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Advisor chat failed unexpectedly",
        ) from exc
