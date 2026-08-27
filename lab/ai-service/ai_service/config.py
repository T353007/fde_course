"""Settings for ai-service, read from the environment.

Every knob has a default that works with no network and no API key. If you
change a default here, check the README and the mission that depends on it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_ROOT = Path(__file__).resolve().parent.parent

ProviderName = Literal["stub", "ollama", "openai", "anthropic"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    # ---- service ----
    service_name: str = "ai-service"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # ---- provider selection ----
    llm_provider: ProviderName = "stub"

    # ---- stub provider ----
    stub_scenario: str = "default"
    fixture_dir: Path = SERVICE_ROOT / "fixtures" / "recorded"
    # Scales the slow-p99 sleep. 1.0 is the real thing. Tests set it to 0.0 so
    # the suite does not take nine minutes. The delay is still calculated and
    # still reported, so the scenario stays honest.
    stub_slow_scale: float = 1.0

    # ---- ollama ----
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_router_model: str = "qwen3:1.7b"
    ollama_compare_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 120.0

    # ---- hosted providers ----
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    hosted_timeout_seconds: float = 60.0

    # ---- retrieval ----
    policy_corpus_dir: Path = SERVICE_ROOT / "fixtures" / "policies"
    retrieval_top_k: int = 4
    retrieval_chunk_chars: int = 900
    retrieval_chunk_overlap: int = 150
    embedding_backend: Literal["hash", "sentence-transformers"] = "hash"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 256

    # Order of the tenant metadata filter against the vector search.
    # "post" was the original behavior and is still the default because the
    # 2025 reindex changed scores and nobody wanted to requalify the eval runs.
    retrieval_tenant_filter_mode: Literal["post", "pre"] = "post"

    # ---- retry ----
    # "legacy" matches the retry worker in underwriting-service so the two
    # sides behave the same. "typed" reads the failure kind first.
    retry_policy: Literal["legacy", "typed"] = "legacy"
    retry_max_attempts: int = 5
    retry_base_delay_seconds: float = 0.5

    # ---- prompt assembly ----
    # How much policy text goes into a memo prompt.
    # "full_corpus" was how the first demo worked and Marcus liked the answers.
    memo_policy_context: Literal["full_corpus", "retrieved"] = "full_corpus"
    # Model tier used by the transaction classifier. Set to "premium" during
    # the accuracy push in March and never set back.
    classify_model_tier: Literal["premium", "small"] = "premium"
    # Cache identical document extractions by content hash.
    cache_extractions: bool = False
    # Also return the model's own revenue average on the classify response.
    # underwriting-service still reads that field.
    legacy_revenue_summary: bool = True

    # ---- tools ----
    # Check the tool allowlist before running a mutating tool.
    enforce_tool_authorization: bool = False

    # ---- observability ----
    trace_buffer_size: int = 500

    @property
    def fixture_path(self) -> Path:
        return Path(self.fixture_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Drop the cached Settings. Tests call this after changing the environment."""
    get_settings.cache_clear()
