"""
Mock Naukri API Server for testing integrations.
This server simulates the Naukri platform for sourcing candidates.

Run with: python mock_naukri_server.py
Server will be available at http://localhost:8002
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import base64

app = FastAPI(
    title="Mock Naukri API",
    description="Mock Naukri API server for testing integrations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
        "http://localhost:5173",
        "http://10.50.14.252:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MOCK DATA
# ============================================================================

# Simulated user accounts
MOCK_USERS = {
    "naukri_user": "naukri_pass123",
    "demo_user": "demo_pass123",
}

# Simulated candidates in Naukri database
MOCK_CANDIDATES = [
    {
        "id": "naukri_001",
        "name": "Rajesh Kumar",
        "email": "rajesh.kumar@email.com",
        "phone": "+91-9876543210",
        "title": "Senior Software Engineer",
        "years_experience": 8,
        "location": "Bangalore",
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker"],
        "resume_url": "http://localhost:8002/mock-resume/naukri_001",
        "profile_url": "https://www.naukri.com/mnjuser/profile",
    },
    {
        "id": "naukri_002",
        "name": "Priya Singh",
        "email": "priya.singh@email.com",
        "phone": "+91-9876543211",
        "title": "Full Stack Developer",
        "years_experience": 5,
        "location": "Mumbai",
        "skills": ["JavaScript", "React", "Node.js", "MongoDB", "TypeScript"],
        "resume_url": "http://localhost:8002/mock-resume/naukri_002",
        "profile_url": "https://www.naukri.com/mnjuser/profile",
    },
    {
        "id": "naukri_003",
        "name": "Amit Patel",
        "email": "amit.patel@email.com",
        "phone": "+91-9876543212",
        "title": "Data Engineer",
        "years_experience": 6,
        "location": "Pune",
        "skills": ["Python", "Spark", "Hadoop", "SQL", "Cloud"],
        "resume_url": "http://localhost:8002/mock-resume/naukri_003",
        "profile_url": "https://www.naukri.com/mnjuser/profile",
    },
    {
        "id": "naukri_004",
        "name": "Neha Sharma",
        "email": "neha.sharma@email.com",
        "phone": "+91-9876543213",
        "title": "Frontend Developer",
        "years_experience": 4,
        "location": "Delhi",
        "skills": ["React", "Vue.js", "CSS", "JavaScript", "UI/UX"],
        "resume_url": "http://localhost:8002/mock-resume/naukri_004",
        "profile_url": "https://www.naukri.com/mnjuser/profile",
    },
    {
        "id": "naukri_005",
        "name": "Vikram Desai",
        "email": "vikram.desai@email.com",
        "phone": "+91-9876543214",
        "title": "DevOps Engineer",
        "years_experience": 7,
        "location": "Hyderabad",
        "skills": ["Kubernetes", "Docker", "AWS", "CI/CD", "Terraform"],
        "resume_url": "http://localhost:8002/mock-resume/naukri_005",
        "profile_url": "https://www.naukri.com/mnjuser/profile",
    },
]

# Mock resume content
MOCK_RESUMES = {
    "naukri_001": """
RAJESH KUMAR
Senior Software Engineer
Email: rajesh.kumar@email.com | Phone: +91-9876543210 | Location: Bangalore

PROFESSIONAL SUMMARY
Experienced Senior Software Engineer with 8+ years of expertise in designing and developing scalable web applications
using Python and FastAPI. Strong background in microservices architecture, cloud deployment, and database optimization.

TECHNICAL SKILLS
Languages: Python, Java, SQL
Frameworks: FastAPI, Django, Spring Boot
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS (EC2, S3, RDS, Lambda)
DevOps: Docker, Kubernetes, GitLab CI/CD
Tools: Git, JIRA, Postman, DBeaver

PROFESSIONAL EXPERIENCE

Senior Software Engineer | TechCorp India | Jan 2020 - Present
- Led development of microservices-based platform serving 10M+ users
- Designed and implemented RESTful APIs using FastAPI achieving 99.9% uptime
- Optimized database queries reducing response time by 45%
- Mentored team of 5 junior developers
- Implemented CI/CD pipeline using GitLab CI

Software Engineer | StartupXYZ | Jun 2017 - Dec 2019
- Developed full-stack web applications using Python and PostgreSQL
- Built real-time data processing pipeline for analytics
- Reduced server costs by 30% through cloud optimization

EDUCATION
Bachelor of Technology in Computer Science
Indian Institute of Technology (IIT) Delhi | 2016

CERTIFICATIONS
AWS Solutions Architect - Associate | 2021
Kubernetes Administrator Certification | 2020
""",
    "naukri_002": """
PRIYA SINGH
Full Stack Developer
Email: priya.singh@email.com | Phone: +91-9876543211 | Location: Mumbai

PROFESSIONAL SUMMARY
Full Stack Developer with 5+ years of experience in building modern web applications. Expert in React and Node.js
with strong focus on user experience and scalable architecture.

TECHNICAL SKILLS
Frontend: React, Vue.js, Angular, TypeScript, HTML5, CSS3, Tailwind
Backend: Node.js, Express.js, MongoDB, PostgreSQL
Tools: Git, Webpack, Jest, Postman, VS Code

PROFESSIONAL EXPERIENCE

Senior Full Stack Developer | WebSolutions Inc | Feb 2021 - Present
- Developed responsive web applications serving 500K+ monthly users
- Implemented React components with Redux state management
- Built Node.js APIs with Express.js and MongoDB
- Improved application performance by 50% through code optimization

Full Stack Developer | DigitalAgency | Jul 2019 - Jan 2021
- Created interactive web applications using React and Node.js
- Managed AWS Lambda functions for serverless architecture
- Implemented automated testing with Jest achieving 85% coverage

EDUCATION
Bachelor of Computer Science
University of Mumbai | 2019

CERTIFICATIONS
React Advanced Patterns | 2021
Node.js Development Certified | 2020
""",
    "naukri_003": """
DATA ENGINEER
AMIT PATEL
Email: amit.patel@email.com | Phone: +91-9876543212 | Location: Pune

PROFESSIONAL SUMMARY
Data Engineer with 6+ years of experience in designing and implementing large-scale data processing pipelines.
Expertise in Apache Spark, Hadoop, and cloud data warehousing solutions.

TECHNICAL SKILLS
Big Data: Apache Spark, Hadoop, Hive, Kafka
Languages: Python, Scala, SQL
Cloud: AWS (EMR, S3, Glue), Google Cloud
Databases: PostgreSQL, MongoDB, Cassandra
Tools: Airflow, Jenkins, Git, Docker

PROFESSIONAL EXPERIENCE

Senior Data Engineer | DataCorp | Mar 2020 - Present
- Designed and implemented ETL pipelines processing 100TB+ data daily
- Optimized Spark jobs reducing processing time by 60%
- Implemented data quality frameworks
- Led migration of on-premise systems to AWS

Data Engineer | AnalyticsHub | Jan 2018 - Feb 2020
- Built data warehousing solutions using AWS Redshift
- Created real-time data pipelines using Apache Kafka
- Improved data processing efficiency by 40%

EDUCATION
Bachelor of Technology in Information Technology
Pune University | 2018

CERTIFICATIONS
AWS Certified Data Analytics | 2021
Apache Spark Developer Certified | 2020
""",
    "naukri_004": """
NEHA SHARMA
Frontend Developer
Email: neha.sharma@email.com | Phone: +91-9876543213 | Location: Delhi

PROFESSIONAL SUMMARY
Frontend Developer with 4+ years of experience in creating engaging and responsive user interfaces.
Passionate about modern web technologies and user experience design.

TECHNICAL SKILLS
Frontend: React, Vue.js, CSS, HTML5, JavaScript, TypeScript
UI Libraries: Material-UI, Bootstrap, Tailwind CSS
Tools: Webpack, Babel, ESLint, Git
Testing: Jest, React Testing Library

PROFESSIONAL EXPERIENCE

Frontend Developer | UICreators | Aug 2021 - Present
- Developed React-based single-page applications
- Implemented responsive designs using CSS and Tailwind
- Improved UI performance reducing load time by 35%
- Collaborated with UX designers on design systems

Associate Frontend Developer | WebDesignStudio | Jun 2020 - Jul 2021
- Built interactive UI components using React
- Implemented CSS animations and transitions
- Maintained and optimized legacy JavaScript code

EDUCATION
Bachelor of Computer Applications
Delhi University | 2020

CERTIFICATIONS
React Fundamentals Certified | 2021
UI/UX Design Basics | 2020
""",
    "naukri_005": """
VIKRAM DESAI
DevOps Engineer
Email: vikram.desai@email.com | Phone: +91-9876543214 | Location: Hyderabad

PROFESSIONAL SUMMARY
DevOps Engineer with 7+ years of experience in designing and maintaining cloud infrastructure.
Expert in containerization, orchestration, and CI/CD pipeline implementation.

TECHNICAL SKILLS
Cloud: AWS, Google Cloud, Azure
Containerization: Docker, Kubernetes, Helm
Infrastructure as Code: Terraform, CloudFormation, Ansible
CI/CD: Jenkins, GitLab CI, GitHub Actions
Monitoring: Prometheus, Grafana, ELK Stack
Databases: PostgreSQL, MySQL, MongoDB

PROFESSIONAL EXPERIENCE

Senior DevOps Engineer | CloudSystems | Apr 2020 - Present
- Managed Kubernetes clusters supporting 50+ microservices
- Implemented Infrastructure as Code using Terraform
- Designed monitoring and alerting systems using Prometheus
- Reduced infrastructure costs by 45% through optimization

DevOps Engineer | InfraTech | Jan 2018 - Mar 2020
- Deployed and managed AWS infrastructure
- Automated deployment pipelines using Jenkins
- Implemented container orchestration using Docker Compose

EDUCATION
Bachelor of Technology in Information Technology
Osmania University | 2017

CERTIFICATIONS
Kubernetes Administrator (CKA) | 2021
AWS Solutions Architect | 2020
"""
}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str


class CandidateProfile(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    title: str
    years_experience: int
    location: str
    skills: List[str]
    resume_url: str
    profile_url: str


class CandidatesListResponse(BaseModel):
    success: bool
    total: int
    candidates: List[CandidateProfile]


class ResumeContent(BaseModel):
    success: bool
    candidate_id: str
    content: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def verify_token(token: str) -> bool:
    """Verify if token is valid (mock implementation)"""
    try:
        decoded = base64.b64decode(token).decode()
        username = decoded.split(":")[0]
        return username in MOCK_USERS
    except Exception:
        return False


def get_token_username(token: str) -> Optional[str]:
    """Extract username from token"""
    try:
        decoded = base64.b64decode(token).decode()
        return decoded.split(":")[0]
    except Exception:
        return None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {
        "name": "Mock Naukri API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/auth/login", response_model=AuthResponse)
def login(request: AuthRequest):
    """
    Login endpoint - validates credentials and returns a token.

    Test credentials:
    - username: naukri_user
      password: naukri_pass123
    - username: demo_user
      password: demo_pass123
    """
    if request.username in MOCK_USERS and MOCK_USERS[request.username] == request.password:
        # Create a simple token (base64 encoded "username:timestamp")
        token_str = f"{request.username}:{datetime.now().isoformat()}"
        token = base64.b64encode(token_str.encode()).decode()
        return AuthResponse(
            success=True,
            token=token,
            message=f"Successfully authenticated as {request.username}"
        )
    else:
        raise HTTPException(
            status_code=401,
            detail=AuthResponse(
                success=False,
                message="Invalid username or password"
            ).dict()
        )


@app.get("/candidates", response_model=CandidatesListResponse)
def list_candidates(token: str):
    """
    List all available candidates.

    Required query parameter: token (from /auth/login)
    """
    if not verify_token(token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    candidates = [CandidateProfile(**c) for c in MOCK_CANDIDATES]
    return CandidatesListResponse(
        success=True,
        total=len(candidates),
        candidates=candidates
    )


@app.get("/candidates/search", response_model=CandidatesListResponse)
def search_candidates(
    token: str,
    keywords: Optional[str] = None,
    location: Optional[str] = None,
    min_experience: Optional[int] = None,
    max_experience: Optional[int] = None,
    skills: Optional[str] = None,
):
    """
    Search candidates with filters.

    Query parameters:
    - token: auth token from /auth/login
    - keywords: search in name, title, location (optional)
    - location: filter by location (optional)
    - min_experience: minimum years of experience (optional)
    - max_experience: maximum years of experience (optional)
    - skills: comma-separated skills to filter (optional)
    """
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    results = MOCK_CANDIDATES.copy()

    # Filter by keywords
    if keywords:
        keywords_lower = keywords.lower()
        results = [
            c for c in results
            if keywords_lower in c["name"].lower()
            or keywords_lower in c["title"].lower()
            or keywords_lower in c["location"].lower()
        ]

    # Filter by location
    if location:
        results = [c for c in results if location.lower() in c["location"].lower()]

    # Filter by experience
    if min_experience is not None:
        results = [c for c in results if c["years_experience"] >= min_experience]
    if max_experience is not None:
        results = [c for c in results if c["years_experience"] <= max_experience]

    # Filter by skills
    if skills:
        required_skills = [s.strip().lower() for s in skills.split(",")]
        results = [
            c for c in results
            if any(
                req_skill in [s.lower() for s in c["skills"]]
                for req_skill in required_skills
            )
        ]

    candidates = [CandidateProfile(**c) for c in results]
    return CandidatesListResponse(
        success=True,
        total=len(candidates),
        candidates=candidates
    )


@app.get("/candidates/{candidate_id}/resume", response_model=ResumeContent)
def get_candidate_resume(candidate_id: str, token: str):
    """
    Get resume content for a specific candidate.

    Path parameter: candidate_id
    Query parameter: token (from /auth/login)
    """
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if candidate_id not in MOCK_RESUMES:
        return ResumeContent(
            success=False,
            candidate_id=candidate_id,
            error=f"Resume not found for candidate {candidate_id}"
        )

    return ResumeContent(
        success=True,
        candidate_id=candidate_id,
        content=MOCK_RESUMES[candidate_id]
    )


@app.get("/mock-resume/{candidate_id}")
def get_mock_resume_content(candidate_id: str):
    """Direct access to mock resume content (for testing)"""
    if candidate_id not in MOCK_RESUMES:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "candidate_id": candidate_id,
        "content": MOCK_RESUMES[candidate_id],
        "content_type": "text/plain"
    }


@app.post("/candidates/{candidate_id}/verify", response_model=dict)
def verify_candidate(candidate_id: str, token: str):
    """
    Verify/check candidate profile (mock endpoint).

    Path parameter: candidate_id
    Query parameter: token
    """
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if candidate_id not in [c["id"] for c in MOCK_CANDIDATES]:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return {
        "success": True,
        "candidate_id": candidate_id,
        "verified": True,
        "verified_at": datetime.now().isoformat()
    }


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("Mock Naukri Server is running!")
    print("="*70)
    print("\n📌 TEST CREDENTIALS:")
    print("  Username: naukri_user")
    print("  Password: naukri_pass123")
    print("\n  OR")
    print("\n  Username: demo_user")
    print("  Password: demo_pass123")
    print("\n🔗 ENDPOINTS:")
    print("  POST   /auth/login")
    print("  GET    /candidates?token=<token>")
    print("  GET    /candidates/search?token=<token>&keywords=python")
    print("  GET    /candidates/{candidate_id}/resume?token=<token>")
    print("  POST   /candidates/{candidate_id}/verify?token=<token>")
    print("\n📚 API Documentation: http://localhost:8002/docs")
    print("="*70 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
