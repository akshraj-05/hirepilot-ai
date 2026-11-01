"""Naukri integration provider."""

import httpx
import logging
from typing import Optional, List, Dict, Any
from .base_provider import BaseIntegrationProvider, CandidateData, ConnectionTestResult

logger = logging.getLogger(__name__)


class NaukriProvider(BaseIntegrationProvider):
    """Integration provider for Naukri platform."""

    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with Naukri API.
        Expects credentials with 'client_id' and 'client_secret'.
        """
        try:
            auth_url = f"{self.api_base_url}/auth/login"

            # Support both old (username/password) and new (client_id/client_secret) formats
            username = credentials.get("client_id") or credentials.get("username")
            password = credentials.get("client_secret") or credentials.get("password")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    auth_url,
                    json={
                        "username": username,
                        "password": password,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.credentials["token"] = data.get("token")
                        return True
        except Exception as e:
            logger.error(f"Naukri authentication failed: {e}")
        return False

    async def test_connection(self, credentials: Dict[str, str]) -> ConnectionTestResult:
        """Test connection with provided credentials."""
        try:
            success = await self.authenticate(credentials)
            if success:
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Naukri"
                )
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Failed to authenticate with Naukri",
                    error="Invalid credentials"
                )
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return ConnectionTestResult(
                success=False,
                message="Connection test failed",
                error=str(e)
            )

    async def fetch_candidates(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[CandidateData]:
        """Fetch candidates from Naukri.

        If filters have search terms (keywords, location, skills), uses search endpoint.
        Otherwise, fetches all available candidates.
        """
        if not self.credentials.get("token"):
            logger.error("Not authenticated. Call authenticate() first.")
            return []

        try:
            # Check if we have any search filters to apply
            keywords = filters.get("keywords") if filters else None
            location = filters.get("location") if filters else None
            skills = filters.get("skills") if filters else None
            min_exp = filters.get("experience_min_years") if filters else None
            max_exp = filters.get("experience_max_years") if filters else None

            # Determine which endpoint to use
            has_search_filters = bool(keywords or location or skills or min_exp or max_exp)
            candidates_url = f"{self.api_base_url}/candidates/search" if has_search_filters else f"{self.api_base_url}/candidates"

            params = {"token": self.credentials["token"], "limit": limit}

            # Add search filters if present
            if has_search_filters:
                logger.info(f"Searching with filters: keywords={keywords}, location={location}, skills={skills}")
                if keywords:
                    params["keywords"] = keywords
                if location:
                    params["location"] = location
                if min_exp:
                    params["min_experience"] = min_exp
                if max_exp:
                    params["max_experience"] = max_exp
                if skills:
                    params["skills"] = ",".join(skills)
            else:
                logger.info("Fetching all candidates (no search filters)")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    candidates_url,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()

            data = response.json()
            if not data.get("success"):
                logger.error(f"Naukri API error: {data.get('message')}")
                return []

            candidates = []
            for candidate_data in data.get("candidates", []):
                try:
                    candidate = CandidateData(
                        external_id=candidate_data["id"],
                        name=candidate_data.get("name", ""),
                        email=candidate_data.get("email", ""),
                        phone=candidate_data.get("phone", ""),
                        title=candidate_data.get("title", ""),
                        years_experience=candidate_data.get("years_experience", 0),
                        location=candidate_data.get("location", ""),
                        skills=candidate_data.get("skills", []),
                        source_url=candidate_data.get("profile_url", ""),
                    )
                    candidates.append(candidate)
                except Exception as e:
                    logger.warning(f"Failed to parse candidate: {e}")

            logger.info(f"Fetched {len(candidates)} candidates from Naukri")
            return candidates

        except Exception as e:
            logger.error(f"Failed to fetch candidates from Naukri: {e}")
            return []

    async def fetch_candidate_resume(self, external_id: str) -> Optional[str]:
        """Fetch resume content for a specific candidate."""
        if not self.credentials.get("token"):
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        try:
            resume_url = f"{self.api_base_url}/candidates/{external_id}/resume"
            params = {"token": self.credentials["token"]}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    resume_url,
                    params=params,
                    timeout=10.0,
                )
                response.raise_for_status()

            data = response.json()
            if data.get("success"):
                return data.get("content")
            else:
                logger.warning(f"Failed to fetch resume: {data.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Failed to fetch resume for candidate {external_id}: {e}")
            return None

    def platform_name(self) -> str:
        """Return platform name."""
        return "naukri"
