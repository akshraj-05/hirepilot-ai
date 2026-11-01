"""Service for managing integrations and syncing candidates."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.models.integration import Integration
from app.db.models.integration_sync_log import IntegrationSyncLog
from app.db.models.uploaded_resume import UploadedResume
from app.db.models.candidate import Candidate
from app.db.models.job_posting import JobPosting
from app.integrations.base_provider import BaseIntegrationProvider, CandidateData
from app.integrations.naukri_provider import NaukriProvider

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing external platform integrations."""

    def __init__(self, db: AsyncSession, api_base_url: str = "http://localhost:8002"):
        """Initialize service with database session and API base URL."""
        self.db = db
        self.api_base_url = api_base_url
        self.providers: Dict[str, BaseIntegrationProvider] = {
            "naukri": NaukriProvider(api_base_url=api_base_url)
        }

    async def get_integration(
        self,
        org_id: uuid.UUID,
        platform: str
    ) -> Optional[Integration]:
        """Get active integration for an organization and platform."""
        query = select(Integration).where(
            Integration.org_id == org_id,
            Integration.platform == platform,
            Integration.is_active == True
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def save_integration(
        self,
        org_id: uuid.UUID,
        platform: str,
        credentials: Dict[str, str],
        user_id: Optional[str] = None
    ) -> Integration:
        """Save integration credentials securely."""
        # TODO: Implement proper encryption for credentials
        # For now, storing as JSON string (implement encryption in production)
        import json

        existing = await self.get_integration(org_id, platform)
        if existing:
            # Update existing
            existing.encrypted_credentials = json.dumps(credentials)
            existing.is_active = True
            existing.connection_status = "connected"
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            return existing
        else:
            # Create new
            integration = Integration(
                id=uuid.uuid4(),
                org_id=org_id,
                platform=platform,
                encrypted_credentials=json.dumps(credentials),
                is_active=True,
                connection_status="connected",
                created_by=user_id,
            )
            self.db.add(integration)
            await self.db.commit()
            await self.db.refresh(integration)
            return integration

    async def test_connection(
        self,
        platform: str,
        credentials: Dict[str, str]
    ) -> bool:
        """Test connection with provided credentials."""
        provider = self.providers.get(platform)
        if not provider:
            logger.error(f"Unknown platform: {platform}")
            return False

        result = await provider.test_connection(credentials)
        return result.success

    async def sync_candidates(
        self,
        integration_id: uuid.UUID,
        org_id: uuid.UUID,
        job_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> IntegrationSyncLog:
        """Sync candidates from external platform."""
        # Get integration
        query = select(Integration).where(Integration.id == integration_id)
        result = await self.db.execute(query)
        integration = result.scalar_one_or_none()

        if not integration:
            raise ValueError(f"Integration {integration_id} not found")

        # Get all open jobs for this org
        query = select(JobPosting).where(JobPosting.organization_id == org_id, JobPosting.status == "open")
        result = await self.db.execute(query)
        open_jobs = result.scalars().all()

        # Use first open job for sync_log, or use provided job_id
        primary_job_id = job_id or (open_jobs[0].job_id if open_jobs else "GENERAL")

        # Create sync log
        sync_log = IntegrationSyncLog(
            id=uuid.uuid4(),
            integration_id=integration_id,
            job_id=primary_job_id,
            org_id=org_id,
            sync_status="in_progress",
        )
        self.db.add(sync_log)
        await self.db.flush()

        try:
            # Get provider
            provider = self.providers.get(integration.platform)
            if not provider:
                raise ValueError(f"Unknown platform: {integration.platform}")

            # Decode credentials
            import json
            credentials = json.loads(integration.encrypted_credentials)

            # Authenticate
            auth_success = await provider.authenticate(credentials)
            if not auth_success:
                logger.error(f"Failed to authenticate with {integration.platform}")
                sync_log.sync_status = "failed"
                sync_log.error_message = "Authentication failed"
                sync_log.error_type = "AUTH_FAILED"
                await self.db.commit()
                return sync_log

            logger.info(f"Successfully authenticated with {integration.platform}")

            # Fetch candidates
            candidates = await provider.fetch_candidates(filters=filters, limit=limit)
            logger.info(f"Fetched {len(candidates)} candidates from {integration.platform}")
            sync_log.total_candidates_fetched = len(candidates)

            if len(candidates) == 0:
                logger.warning(f"No candidates returned from {integration.platform}")
                sync_log.sync_status = "completed"
                sync_log.sync_completed_at = datetime.utcnow()
                await self.db.commit()
                return sync_log

            # Process each candidate
            processed = 0
            failed = 0
            deduplicated = 0

            for candidate_data in candidates:
                try:
                    # Check if candidate already exists
                    existing_candidate = await self._find_existing_candidate(
                        org_id, candidate_data.email
                    )

                    if existing_candidate:
                        deduplicated += 1
                        continue

                    # Create candidate
                    candidate = await self._create_candidate(
                        org_id=org_id,
                        candidate_data=candidate_data,
                        platform=integration.platform,
                    )

                    # Fetch resume
                    resume_content = await provider.fetch_candidate_resume(
                        candidate_data.external_id
                    )

                    # Create uploaded_resume record for the primary job
                    if primary_job_id != "GENERAL":
                        uploaded_resume = await self._create_uploaded_resume(
                            org_id=org_id,
                            job_id=primary_job_id,
                            candidate_id=candidate.id,
                            resume_content=resume_content or candidate_data.resume_content,
                            external_candidate_id=candidate_data.external_id,
                            platform=integration.platform,
                        )

                    # Trigger orchestration for ALL open jobs (non-blocking)
                    for open_job in open_jobs:
                        asyncio.create_task(
                            self._trigger_orchestration(
                                org_id=org_id,
                                candidate_id=candidate.id,
                                job_id=open_job.job_id,
                            )
                        )

                    processed += 1

                except Exception as e:
                    logger.error(f"Failed to process candidate {candidate_data.external_id}: {e}")
                    failed += 1

            # Update sync log
            sync_log.candidates_processed = processed
            sync_log.candidates_failed = failed
            sync_log.candidates_deduplicated = deduplicated
            sync_log.sync_status = "completed"
            sync_log.sync_completed_at = datetime.utcnow()
            sync_log.response_summary = {
                "processed": processed,
                "failed": failed,
                "deduplicated": deduplicated,
            }

            # Update integration
            integration.last_synced_at = datetime.utcnow()
            integration.total_candidates_synced += processed
            integration.sync_status = "idle"

            await self.db.commit()
            logger.info(f"Sync completed: {processed} processed, {failed} failed, {deduplicated} deduplicated")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sync_log.sync_status = "failed"
            sync_log.error_message = str(e)
            sync_log.error_type = type(e).__name__
            sync_log.sync_completed_at = datetime.utcnow()
            await self.db.commit()

        return sync_log

    async def _find_existing_candidate(
        self,
        org_id: uuid.UUID,
        email: str
    ) -> Optional[Candidate]:
        """Find existing candidate by email."""
        query = select(Candidate).where(
            Candidate.org_id == org_id,
            Candidate.email == email,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _create_candidate(
        self,
        org_id: uuid.UUID,
        candidate_data: CandidateData,
        platform: str,
    ) -> Candidate:
        """Create a new candidate record."""
        candidate = Candidate(
            id=uuid.uuid4(),
            org_id=org_id,
            name=candidate_data.name,
            email=candidate_data.email,
            mobile_number=candidate_data.phone,
            title=candidate_data.title,
            years_experience=candidate_data.years_experience,
            skills=candidate_data.skills,
            source_channel="sourced",
            source_platform=platform,
        )
        self.db.add(candidate)
        await self.db.flush()
        return candidate

    async def _create_uploaded_resume(
        self,
        org_id: uuid.UUID,
        job_id: str,
        candidate_id: uuid.UUID,
        resume_content: Optional[str],
        external_candidate_id: str,
        platform: str,
    ) -> UploadedResume:
        """Create uploaded resume record for sourced candidate."""
        uploaded_resume = UploadedResume(
            id=uuid.uuid4(),
            org_id=org_id,
            posted_job_id=job_id,
            candidate_id=candidate_id,
            original_filename=f"{external_candidate_id}_resume",
            parsed_resume_text=resume_content,
            is_sourced=True,
            source_type=platform,
            external_candidate_id=external_candidate_id,
            processing_status="pending",
        )
        self.db.add(uploaded_resume)
        await self.db.flush()
        return uploaded_resume

    async def _trigger_orchestration(
        self,
        org_id: uuid.UUID,
        candidate_id: uuid.UUID,
        job_id: str,
    ):
        """Trigger the existing orchestration pipeline."""
        try:
            logger.info(
                f"Starting orchestration for candidate {candidate_id} "
                f"on job {job_id}"
            )

            # Import here to avoid circular imports
            import httpx

            # Call the orchestrator endpoint
            orchestrator_url = "http://127.0.0.1:4000/api/orchestrator"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    orchestrator_url,
                    json={
                        "candidate_id": str(candidate_id),
                        "job_id": job_id,
                        "organization_id": str(org_id),
                    },
                    timeout=120.0,
                )

                if response.status_code == 200:
                    logger.info(f"Orchestration completed for candidate {candidate_id}")
                else:
                    logger.warning(
                        f"Orchestration failed for candidate {candidate_id}: "
                        f"Status {response.status_code}: {response.text}"
                    )
        except Exception as e:
            logger.error(
                f"Failed to trigger orchestration for candidate {candidate_id}: {e}",
                exc_info=True
            )

    async def list_integrations(self, org_id: uuid.UUID) -> List[Integration]:
        """List all integrations for an organization."""
        query = select(Integration).where(Integration.org_id == org_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def deactivate_integration(self, integration_id: uuid.UUID) -> bool:
        """Deactivate an integration."""
        query = update(Integration).where(
            Integration.id == integration_id
        ).values(is_active=False)
        await self.db.execute(query)
        await self.db.commit()
        return True
