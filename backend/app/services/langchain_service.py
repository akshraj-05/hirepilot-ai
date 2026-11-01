"""
LangChain helpers — lazy LLM init so the app starts without OPENAI_API_KEY.

When OPENAI_API_KEY is not set, every function returns a mock result so the
app works end-to-end without a real LLM.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.schemas.hiring import HiringDecisionResult, MatchAnalysis
from app.schemas.resume_parse import ParsedResume

_MOCK_NOTE = "mock result — set OPENAI_API_KEY in .env for real AI output"

_chat: ChatOpenAI | None = None


def get_chat_model() -> ChatOpenAI:
    """Singleton chat model; requires OPENAI_API_KEY when invoked."""
    global _chat
    if _chat is None:
        _chat = ChatOpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )
    return _chat


def build_match_summary_chain():
    """
    Example LCEL chain: job description + resume excerpt → short rationale.

    Use in /analyze after text extraction from PDFs/DOCx.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert recruiter. Be concise and factual.",
            ),
            (
                "human",
                "Job description:\n{job_description}\n\nResume excerpt:\n{resume_text}\n\n"
                "Give 3 bullet points: strengths, gaps, and a hiring recommendation "
                "(shortlist / review / reject) with one-line justification each.",
            ),
        ]
    )
    return prompt | get_chat_model() | StrOutputParser()


def summarize_candidate_match(job_description: str, resume_text: str) -> str:
    """Run the example chain (raises if API key missing)."""
    chain = build_match_summary_chain()
    return chain.invoke(
        {"job_description": job_description, "resume_text": resume_text},
    )


def parse_resume_structured(resume_text: str) -> ParsedResume:
    """Extract structured fields from resume text. Returns mock if no API key."""
    if not settings.openai_api_key:
        return ParsedResume(
            skills=["Python", "FastAPI", "REST APIs"],
            experience=_MOCK_NOTE,
            education=_MOCK_NOTE,
        )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You extract structured data from resumes. Use empty string or empty "
                "list when a field is missing. For skills, list concise technology and "
                "role-relevant capabilities. For experience, give a short human-readable "
                "summary (e.g. '3 years' or '5+ years in backend'). For education, a short "
                "line such as degree and field.",
            ),
            (
                "human",
                "Resume text:\n{resume_text}",
            ),
        ]
    )
    llm = get_chat_model().with_structured_output(ParsedResume)
    chain = prompt | llm
    result = chain.invoke({"resume_text": resume_text})
    if isinstance(result, ParsedResume):
        return result
    return ParsedResume.model_validate(result)


def analyze_match_structured(job_description: str, resume_text: str) -> MatchAnalysis:
    """Score and summarize candidate vs job. Returns mock if no API key."""
    if not settings.openai_api_key:
        return MatchAnalysis(
            match_score=72,
            matched_skills=["Python", "FastAPI"],
            missing_skills=["Kubernetes", "Go"],
            summary=_MOCK_NOTE,
        )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You compare a resume to a job description. Output a match_score from "
                "0-100, lists of matched_skills and missing_skills (concise tokens), "
                "and a short summary of fit.",
            ),
            (
                "human",
                "Job description:\n{job_description}\n\nResume:\n{resume_text}",
            ),
        ]
    )
    llm = get_chat_model().with_structured_output(MatchAnalysis)
    chain = prompt | llm
    result = chain.invoke({"job_description": job_description, "resume_text": resume_text})
    if isinstance(result, MatchAnalysis):
        return result
    return MatchAnalysis.model_validate(result)


def hiring_decision_structured(
    job_description: str,
    resume_text: str,
    match_summary: str,
) -> HiringDecisionResult:
    """Produce SHORTLIST / REJECT / REVIEW. Returns mock if no API key."""
    if not settings.openai_api_key:
        return HiringDecisionResult(
            decision="REVIEW",
            confidence=0.6,
            reasoning=_MOCK_NOTE,
        )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a hiring decision assistant. decision must be exactly one of: "
                "SHORTLIST, REJECT, REVIEW. confidence is 0.0-1.0. reasoning is 2-4 sentences.",
            ),
            (
                "human",
                "Job description:\n{job_description}\n\nResume:\n{resume_text}\n\n"
                "Prior match summary:\n{match_summary}",
            ),
        ]
    )
    llm = get_chat_model().with_structured_output(HiringDecisionResult)
    chain = prompt | llm
    result = chain.invoke(
        {
            "job_description": job_description,
            "resume_text": resume_text,
            "match_summary": match_summary,
        },
    )
    if isinstance(result, HiringDecisionResult):
        return result
    return HiringDecisionResult.model_validate(result)
