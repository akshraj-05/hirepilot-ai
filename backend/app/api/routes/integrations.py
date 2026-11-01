"""Integration API routes."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import AsyncSessionLocal
from app.schemas.integration_schema import (
    TestConnectionRequest,
    ConnectIntegrationRequest,
    TestConnectionResponse,
    ConnectIntegrationResponse,
    IntegrationResponse,
    SyncRequest,
    SyncJobResponse,
    SyncLogResponse,
)
from app.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


async def get_db() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


# Placeholder for authentication - in production, use actual auth
def get_org_id(org_id: Optional[str] = Query(None)) -> UUID:
    """Get organization ID from request context or query parameter."""
    # TODO: Get actual org_id from authenticated user
    # For now, check query parameter first, then use default
    if org_id:
        try:
            return UUID(org_id)
        except ValueError:
            logger.warning(f"Invalid org_id in query: {org_id}, using default")

    # Default org_id if not provided or invalid
    return UUID("00000000-0000-0000-0000-000000000001")


@router.get("")
async def list_integrations(
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
) -> dict:
    """List all active integrations for the organization."""
    try:
        service = IntegrationService(db)
        integrations = await service.list_integrations(org_id)
        logger.info(f"Listed {len(integrations)} integrations for org {org_id}")
        for integration in integrations:
            logger.info(f"  - {integration.platform}: active={integration.is_active}, status={integration.connection_status}")
        return {
            "success": True,
            "integrations": [
                IntegrationResponse.from_orm(i).model_dump() for i in integrations
            ],
        }
    except Exception as e:
        logger.error(f"Failed to list integrations for org {org_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list integrations",
        )


@router.post("/naukri/test-connection")
async def test_naukri_connection(
    request: TestConnectionRequest,
    db: AsyncSession = Depends(get_db),
) -> TestConnectionResponse:
    """Test Naukri connection with provided credentials."""
    try:
        service = IntegrationService(db)
        success = await service.test_connection("naukri", request.credentials.model_dump())

        return TestConnectionResponse(
            success=success,
            platform="naukri",
            message="Connection successful" if success else "Connection failed",
            error=None if success else "Invalid credentials",
        )
    except Exception as e:
        logger.error(f"Naukri connection test failed: {e}")
        return TestConnectionResponse(
            success=False,
            platform="naukri",
            message="Connection test failed",
            error=str(e),
        )


@router.post("/naukri/connect")
async def connect_naukri(
    request: ConnectIntegrationRequest,
    db: AsyncSession = Depends(get_db),
) -> ConnectIntegrationResponse:
    """Connect and save Naukri integration."""
    try:
        # First test connection
        service = IntegrationService(db)
        success = await service.test_connection("naukri", request.credentials.model_dump())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Naukri. Please check your credentials.",
            )

        # Save integration
        integration = await service.save_integration(
            org_id=request.org_id,
            platform="naukri",
            credentials=request.credentials.model_dump(),
        )

        return ConnectIntegrationResponse.from_orm(integration)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect Naukri: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save integration",
        )


@router.post("/naukri/sync")
async def sync_naukri_candidates(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    org_id: Optional[str] = Query(None),
) -> SyncJobResponse:
    """Trigger candidate sync from Naukri."""
    try:
        # Parse org_id from query parameter or use default
        if org_id:
            try:
                parsed_org_id = UUID(org_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid org_id format",
                )
        else:
            parsed_org_id = UUID("00000000-0000-0000-0000-000000000001")

        service = IntegrationService(db)

        # Get Naukri integration
        integration = await service.get_integration(parsed_org_id, "naukri")
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Naukri integration not configured for this organization",
            )

        # Trigger sync
        sync_log = await service.sync_candidates(
            integration_id=integration.id,
            org_id=parsed_org_id,
            job_id=request.job_id,
            filters={
                "keywords": request.filters.keywords,
                "location": request.filters.location,
                "min_experience": request.filters.experience_min_years,
                "max_experience": request.filters.experience_max_years,
                "skills": request.filters.skills,
            },
            limit=request.limit,
        )

        logger.info(f"Sync result: fetched={sync_log.total_candidates_fetched}, processed={sync_log.candidates_processed}, failed={sync_log.candidates_failed}, dedup={sync_log.candidates_deduplicated}, status={sync_log.sync_status}, error={sync_log.error_message}")

        return SyncJobResponse(
            sync_log_id=sync_log.id,
            status=sync_log.sync_status,
            message=f"Sync completed: {sync_log.candidates_processed} candidates processed, {sync_log.candidates_failed} failed, {sync_log.candidates_deduplicated} deduplicated",
            estimated_completion=sync_log.sync_completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync candidates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger sync",
        )


@router.post("/linkedin/test-connection")
async def test_linkedin_connection(
    request: TestConnectionRequest,
) -> TestConnectionResponse:
    """Test LinkedIn connection (future)."""
    return TestConnectionResponse(
        success=False,
        platform="linkedin",
        message="LinkedIn integration coming soon",
        error="Not yet implemented",
    )


@router.post("/indeed/test-connection")
async def test_indeed_connection(
    request: TestConnectionRequest,
) -> TestConnectionResponse:
    """Test Indeed connection (future)."""
    return TestConnectionResponse(
        success=False,
        platform="indeed",
        message="Indeed integration coming soon",
        error="Not yet implemented",
    )


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    org_id: UUID = Depends(get_org_id),
) -> dict:
    """Deactivate an integration."""
    try:
        service = IntegrationService(db)
        await service.deactivate_integration(integration_id)
        return {"success": True, "message": "Integration deactivated"}
    except Exception as e:
        logger.error(f"Failed to delete integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate integration",
        )
