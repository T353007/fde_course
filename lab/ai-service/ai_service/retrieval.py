"""Policy corpus retrieval.

Chunk the markdown files under fixtures/policies, embed them, and return the
top matches for a question. Tenant, product, and effective date all matter.

RETRIEVAL_TENANT_FILTER_MODE controls when the tenant check runs:

  pre   Filter the corpus first, then take top-k. Correct.
  post  Take top-k on the full corpus, then filter. Broken default.

The post mode is how Cascade once saw Bayline's pricing supplement. Leave the
default alone so Mission 24 can find it. Set the env var to pre to fix it.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from ai_service.config import Settings, get_settings
from ai_service.schemas import Citation

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
_HEADING = re.compile(r"(?m)^(#{1,3}\s+.+)$")


@dataclass(frozen=True)
class PolicyChunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    tenant_scope: str
    product_scope: str
    effective_from: date | None
    superseded_by: str | None
    embedding: list[float]


def _parse_frontmatter(raw: str) -> tuple[dict[str, str | None], str]:
    match = _FRONTMATTER.match(raw.strip())
    if not match:
        return {}, raw
    meta: dict[str, str | None] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        meta[key.strip()] = None if value.lower() == "null" or value == "" else value
    return meta, match.group(2).strip()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _chunk_body(body: str, chunk_chars: int, overlap: int) -> list[str]:
    """Split on headings when we can, then by character window."""
    parts = _HEADING.split(body)
    sections: list[str] = []
    if len(parts) == 1:
        sections = [body]
    else:
        # parts alternates: preamble, heading, body, heading, body, ...
        preamble = parts[0].strip()
        if preamble:
            sections.append(preamble)
        for index in range(1, len(parts), 2):
            heading = parts[index].strip()
            content = parts[index + 1].strip() if index + 1 < len(parts) else ""
            sections.append(f"{heading}\n\n{content}".strip())

    chunks: list[str] = []
    for section in sections:
        if len(section) <= chunk_chars:
            chunks.append(section)
            continue
        start = 0
        while start < len(section):
            end = min(len(section), start + chunk_chars)
            chunks.append(section[start:end].strip())
            if end >= len(section):
                break
            start = max(0, end - overlap)
    return [c for c in chunks if c]


def hash_embed(text: str, dim: int) -> list[float]:
    """A cheap deterministic embedder. No downloads, no network.

    It is not semantic in any deep sense. It is good enough for the lab corpus
    because the policy files use distinct vocabulary (Bayline, Cascade, SBA,
    DSCR) and the missions lean on that.
    """
    tokens = re.findall(r"[a-z0-9]+", text.casefold())
    if not tokens:
        return [0.0] * dim
    vec = [0.0] * dim
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vec[index] += sign * weight
    # L2 normalize so cosine is a plain dot product.
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _tenant_visible(chunk: PolicyChunk, tenant_id: str) -> bool:
    scope = (chunk.tenant_scope or "ALL").upper()
    if scope in {"ALL", "*", "ANY"}:
        return True
    return scope == tenant_id.upper()


def _product_visible(chunk: PolicyChunk, product: str | None) -> bool:
    if not product:
        return True
    scope = (chunk.product_scope or "ALL").upper()
    if scope in {"ALL", "*", "ANY"}:
        return True
    return scope == product.upper()


def _effective_visible(chunk: PolicyChunk, on: date) -> bool:
    if chunk.effective_from is None:
        # Drafts with no effective date stay in the index. Mission 23 is about
        # that choice, not about hiding them here.
        return True
    return chunk.effective_from <= on


class PolicyIndex:
    """In-memory policy search over the markdown fixtures."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.chunks: list[PolicyChunk] = []
        self.reload()

    def reload(self) -> None:
        self.chunks = load_policy_chunks(self.settings)

    def search(
        self,
        query: str,
        *,
        tenant_id: str,
        product: str | None = None,
        effective_on: date | None = None,
        top_k: int | None = None,
    ) -> list[Citation]:
        settings = self.settings
        k = top_k or settings.retrieval_top_k
        on = effective_on or date.today()
        query_vec = hash_embed(query, settings.embedding_dim)

        # Product and effective date always filter the pool. Tenant is the one
        # that moves, because that is the Mission 24 defect.
        base_pool = [
            c
            for c in self.chunks
            if _product_visible(c, product) and _effective_visible(c, on)
        ]

        mode = settings.retrieval_tenant_filter_mode
        if mode == "pre":
            pool = [c for c in base_pool if _tenant_visible(c, tenant_id)]
            ranked = self._rank(pool, query_vec)
            chosen = ranked[:k]
        else:
            # post (default): rank the full pool, take top-k, then filter.
            ranked = self._rank(base_pool, query_vec)
            top = ranked[:k]
            filtered = [c for c, _ in top if _tenant_visible(c, tenant_id)]
            # The filter ran. Its result is not what we return. A rename during
            # the 2025 reindex left `top` on the return path and `filtered` only
            # in a local that nothing reads. Cascade can cite Bayline this way.
            _ = filtered
            chosen = top

        citations: list[Citation] = []
        for chunk, score in chosen:
            citations.append(
                Citation(
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    chunk_id=chunk.chunk_id,
                    score=round(score, 6),
                    excerpt=chunk.text[:400],
                    tenant_scope=chunk.tenant_scope,
                    product_scope=chunk.product_scope,
                    effective_from=(
                        chunk.effective_from.isoformat()
                        if chunk.effective_from
                        else None
                    ),
                )
            )
        return citations

    def _rank(
        self, pool: list[PolicyChunk], query_vec: list[float]
    ) -> list[tuple[PolicyChunk, float]]:
        scored = [(c, _cosine(query_vec, c.embedding)) for c in pool]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def format_context(self, citations: list[Citation]) -> str:
        blocks: list[str] = []
        for cite in citations:
            blocks.append(
                f"[chunkId={cite.chunk_id} docId={cite.doc_id} "
                f"tenant={cite.tenant_scope} product={cite.product_scope} "
                f"effectiveFrom={cite.effective_from}]\n{cite.excerpt}"
            )
        return "\n\n".join(blocks) if blocks else "(no policy excerpts matched)"

    def full_corpus_text(self) -> str:
        """Every chunk, used when MEMO_POLICY_CONTEXT=full_corpus."""
        return self.format_context(
            [
                Citation(
                    doc_id=c.doc_id,
                    title=c.title,
                    chunk_id=c.chunk_id,
                    score=0.0,
                    excerpt=c.text[:900],
                    tenant_scope=c.tenant_scope,
                    product_scope=c.product_scope,
                    effective_from=(
                        c.effective_from.isoformat() if c.effective_from else None
                    ),
                )
                for c in self.chunks
            ]
        )


def load_policy_chunks(settings: Settings) -> list[PolicyChunk]:
    root = Path(settings.policy_corpus_dir)
    if not root.exists():
        return []

    chunks: list[PolicyChunk] = []
    for path in sorted(root.glob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        doc_id = str(meta.get("docId") or path.stem)
        title = str(meta.get("title") or doc_id)
        tenant_scope = str(meta.get("tenantScope") or "ALL")
        product_scope = str(meta.get("productScope") or "ALL")
        effective_from = _parse_date(meta.get("effectiveFrom"))
        superseded_by = meta.get("supersededBy")

        pieces = _chunk_body(
            body, settings.retrieval_chunk_chars, settings.retrieval_chunk_overlap
        )
        for index, text in enumerate(pieces):
            chunk_id = f"{doc_id}::chunk-{index}"
            chunks.append(
                PolicyChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    title=title,
                    text=text,
                    tenant_scope=tenant_scope,
                    product_scope=product_scope,
                    effective_from=effective_from,
                    superseded_by=superseded_by,
                    embedding=hash_embed(text, settings.embedding_dim),
                )
            )
    return chunks


@lru_cache
def get_policy_index() -> PolicyIndex:
    return PolicyIndex()


def reset_policy_index() -> None:
    get_policy_index.cache_clear()


def corpus_stats() -> dict[str, Any]:
    index = get_policy_index()
    docs = sorted({c.doc_id for c in index.chunks})
    return {"documents": docs, "chunkCount": len(index.chunks)}
