"""Base integration provider class."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class CandidateData(BaseModel):
    """Standardized candidate data from external platforms."""
    external_id: str
    name: str
    email: str
    phone: str
    title: str
    years_experience: int
    location: str
    skills: List[str]
    resume_content: Optional[str] = None
    source_url: Optional[str] = None


class ConnectionTestResult(BaseModel):
    """Result of connection test."""
    success: bool
    message: str
    error: Optional[str] = None


class BaseIntegrationProvider(ABC):
    """Abstract base class for integration providers."""

    def __init__(self, api_base_url: str, **kwargs):
        """Initialize provider with base URL and optional credentials."""
        self.api_base_url = api_base_url
        self.credentials: Dict[str, Any] = kwargs

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with the external platform.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    async def test_connection(self, credentials: Dict[str, str]) -> ConnectionTestResult:
        """Test if credentials are valid."""
        pass

    @abstractmethod
    async def fetch_candidates(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[CandidateData]:
        """
        Fetch candidates from the platform with optional filters.
        """
        pass

    @abstractmethod
    async def fetch_candidate_resume(self, external_id: str) -> Optional[str]:
        """Fetch resume content for a specific candidate."""
        pass

    def platform_name(self) -> str:
        """Return the platform name (e.g., 'naukri', 'linkedin')."""
        return self.__class__.__name__.lower().replace("provider", "")
