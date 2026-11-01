"""LLM provider for agents — returns a single shared instance based on config."""

from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings

_agent_llm: BaseChatModel | None = None


def get_agent_llm() -> BaseChatModel:
    """Returns the LLM instance based on LLM_PROVIDER env var. Singleton."""
    global _agent_llm
    if _agent_llm is not None:
        return _agent_llm

    provider = settings.llm_provider.lower()

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set — add it to .env to enable agents.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        _agent_llm = ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.2,
        )

    elif provider == "cerebras":
        if not settings.cerebras_api_key:
            raise RuntimeError("CEREBRAS_API_KEY is not set — add it to .env to enable agents.")
        from langchain_cerebras import ChatCerebras
        _agent_llm = ChatCerebras(
            model=settings.cerebras_chat_model,
            api_key=settings.cerebras_api_key,
        )

    else:  # default: openai-compatible
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set — add it to .env to enable agents.")
        from langchain_openai import ChatOpenAI
        _agent_llm = ChatOpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.2,
        )

    return _agent_llm
