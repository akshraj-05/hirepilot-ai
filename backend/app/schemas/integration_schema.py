from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# Request schemas
class CredentialsRequest(BaseModel):
    """Credentials for integration authentication"""
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_key: Optional[str] = None
    email: Optional[str] = None  # Alternative to username for some platforms


class TestConnectionRequest(BaseModel):
    """Request to test integration credentials"""
    org_id: UUID
    credentials: CredentialsRequest


class ConnectIntegrationRequest(BaseModel):
    """Request to save and activate integration"""
    org_id: UUID
    credentials: CredentialsRequest


class SyncFilters(BaseModel):
    """Filtering options for candidate search"""
    keywords: Optional[str] = None
    location: Optional[str] = None
    experience_min_years: Optional[int] = None
    experience_max_years: Optional[int] = None
    skills: Optional[list[str]] = None


class SyncRequest(BaseModel):
    """Request to trigger candidate sync"""
    job_id: Optional[str] = None  # If not provided, sync for all open jobs
    filters: SyncFilters
    limit: int = Field(default=50, ge=1, le=500)


# Response schemas
class IntegrationResponse(BaseModel):
    """Active integration metadata"""
    id: UUID
    platform: str
    is_active: bool
    connection_status: str
    last_synced_at: Optional[datetime] = None
    total_candidates_synced: int
    last_tested_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestConnectionResponse(BaseModel):
    """Response from connection test"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    platform: str
    verified_at: Optional[datetime] = None


class ConnectIntegrationResponse(BaseModel):
    """Response from saving integration"""
    id: UUID
    platform: str
    is_active: bool
    connection_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SyncLogResponse(BaseModel):
    """Sync status and results"""
    id: UUID
    sync_status: str
    total_candidates_fetched: int
    candidates_processed: int
    candidates_failed: int
    candidates_deduplicated: int
    sync_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


class SyncJobResponse(BaseModel):
    """Response when sync job is queued"""
    task_id: Optional[str] = None
    sync_log_id: Optional[UUID] = None
    status: str  # queued, in_progress, completed, failed
    message: str
    estimated_completion: Optional[datetime] = None


# Candidate-related schemas
class CandidateSourceInfo(BaseModel):
    """Source information for a candidate"""
    source_platform: str  # naukri, linkedin, indeed
    source_channel: str  # manual, sourced
    external_id: Optional[str] = None
    synced_at: Optional[datetime] = None
    source_url: Optional[str] = None


class CandidateListFilters(BaseModel):
    """Filters for candidate listing"""
    job_id: Optional[str] = None
    source_platform: Optional[str] = None  # naukri, linkedin, indeed, or 'all'
    source_channel: Optional[str] = None  # manual, sourced
    skills: Optional[list[str]] = None
    years_experience_min: Optional[int] = None
    years_experience_max: Optional[int] = None


# Pagination
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    total: int
    page: int
    page_size: int
    has_more: bool
    data: list[Any]
