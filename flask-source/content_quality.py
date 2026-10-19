"""Deterministic publication checks, not a factual-accuracy guarantee.

New facts need substantive support in a source excerpt that actually names the
canonical subject. Source titles and a single correct fact cannot authenticate
other content. The legacy audit uses a narrower mismatch test because older
excerpts and legitimate aliases may omit the full canonical name.
"""
from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

QUALITY_GATE_VERSION = "2026-10-19-subject-evidence-v2"

_STOP = frozenset("""
a an and are as at be been being but by can could did do does for from had has
have how if in into is it its may of on or our should so than that the their
them there these they this those to was were what when where which who why will
with would you your about ten fourteen facts fact things thing know before
after visit visiting visits guide guides introduction overview key essential
interesting clear useful uncovered complete ultimate practical distinct
verified sourced evidence backed insights experiences experience information
best top
""".split())
# These words do not count as substantive fact/source support. Entity words
# are NOT removed from subject identity: New York needs both New and York.
_LEXICAL_STOP = _STOP | frozenset("""
source sources point points claim claims article articles text content detail
details available provided supplied based include includes including describes
describe describes described known also only many much most some more less
several used uses using such each very other another all any through which
""".split())
_FAILURES = (
    r"\b(?:supplied|provided)\s+(?:source\s+material|evidence|sources?|documents?|references)\b.{0,160}\b(?:does\s+not|do\s+not|did\s+not|contains?\s+no|includes?\s+no|lacks?)\s+(?:contain|cover|mention|provide|support|include|information|details)",
    r"\bnone\s+of\s+(?:the\s+)?(?:supplied|provided)\s+(?:sources|references|documents)\b.{0,80}\b(?:mention|contain|provide|cover|support)",
    r"\b(?:this|the\s+requested)\s+(?:explainer|article|response)\b.{0,90}\b(?:cannot|can\s+not|unable\s+to)\s+(?:be\s+)?(?:produced|written|generated|provide\s+(?:verified\s+)?facts)\b",
    r"\btherefore\b.{0,100}\b(?:explainer|article)\b.{0,60}\bcannot\s+be\s+(?:produced|written|generated)\b",
    r"\b(?:unable\s+to|cannot)\s+(?:write|produce|generate)\s+(?:this|the\s+requested)\s+(?:article|explainer|response)\b",
    r"\bsummary\s+not\s+available\s+(?:due\s+to|because)\b",
    r"\bthe\s+candidate\s+topic\s+is\b.{0,150}\b(?:but|however|not\s+covered|unrelated|insufficient)\b",
    r"\bas\s+an?\s+ai(?:\s+language\s+model)?\b.{0,80}\bI\s+(?:cannot|can.t|am\s+unable|do\s+not\s+have)\b",
    r"\b(?:supplied|provided)\s+(?:evidence|sources)\b.{0,160}\b(?:each\s+item|following\s+items|following\s+points)\b.{0,80}\b(?:absence|what\s+the\s+evidence\s+lacks)\b",
    # Source absence becomes a generation failure when the output explicitly
    # turns each promised item into a statement that the source has no facts.
    r"\bnone\s+of\s+(?:the(?:\s+(?:six|[0-9]+))?|these|those)\s+(?:sources|references|documents|profiles)\b.{0,160}\b(?:contain|mention|provide|cover)\b.{0,240}\b(?:following\s+(?:items|points)|each\s+item|this\s+explainer)\b.{0,200}\b(?:absence|absent|lack|limits\s+of\s+(?:the\s+)?available\s+data|rather\s+than\s+substantive\s+facts)\b",
    r"\bno\s+(?:verifiable|verified)\s+facts\b.{0,100}\bcan\s+be\s+(?:drawn|extracted)\b.{0,80}\b(?:supplied|provided|given)\b",
    r"\bimpossible\s+to\s+generate\b.{0,100}\b(?:explainers?|articles?)\b.{0,100}\b(?:given|supplied|provided)\s+sources\b",
    # These paired phrases describe a generated article redirecting from its
    # nominal subject to unrelated supplied material, not scholarly uncertainty.
    r"\bthis\s+explainer\b.{0,700}\balthough\b.{0,160}\b(?:available|supplied|provided)\s+(?:evidence|source\s+material)\s+(?:concerns?|pertains?\s+to)\b.{0,180}\b(?:the\s+)?following\s+(?:items|points)\b",
    r"\b(?:supplied|provided)\s+(?:evidence|sources|source\s+material)\b.{0,160}\brather\s+than\b.{0,100}\b(?:the\s+)?following\s+(?:items|points)\b",
    r"\b(?:following\s+(?:items|points)|each\s+item)\b.{0,140}\b(?:explicitly\s+)?(?:notes?|states?|reports?)\b.{0,40}\b(?:absence|lack)\b.{0,80}\b(?:reference|information|details|content|facts)\b",
)
_FAILURE_RE = re.compile("|".join(_FAILURES), re.I)
_COUNT_PATTERN = r"\b(?:14|fourteen)\s+(?=(?:(?:distinct|essential|verified|key|interesting|useful|ranked|sourced|evidence[- ]backed)\s+){0,3}(?:facts|points|things|experiences|items|places|attractions)\b)"
_COUNT_RE = re.compile(_COUNT_PATTERN, re.I)


def normalise_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def subject_terms(value: Any) -> set[str]:
    return {term for term in normalise_text(value).split() if len(term) > 1 and not term.isdigit() and term not in _STOP}


def matches_subject(text: Any, subject: Any) -> bool:
    """Require every identity word within a bounded local text window."""
    wanted = subject_terms(subject)
    if not wanted:
        return False
    words = normalise_text(text).split()
    width = max(12, len(wanted) * 3)
    for index, word in enumerate(words):
        if word in wanted and wanted <= set(words[index:index + width]):
            return True
    return False


def _stem(word: str) -> str:
    if len(word) > 5 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def lexical_terms(value: Any) -> set[str]:
    return {_stem(word) for word in normalise_text(value).split() if len(word) >= 3 and word not in _LEXICAL_STOP}


def fact_has_support(fact: Any, excerpt: Any, subject: Any) -> bool:
    """Require support beyond just the topic name in the actual excerpt.

    This admits source-grounded pronouns/aliases without demanding keyword
    stuffing in every fact. Three content-word matches (two for a very short
    claim), covering at least one quarter of its content terms, are a bounded
    relevance heuristic. It is not semantic entailment or fact verification.
    """
    if not matches_subject(excerpt, subject):
        return False
    identity = {_stem(word) for word in subject_terms(subject)}
    claim_words = lexical_terms(fact) - identity
    evidence_words = lexical_terms(excerpt) - identity
    shared = claim_words & evidence_words
    return len(claim_words) >= 2 and len(shared) >= min(3, len(claim_words)) and len(shared) / len(claim_words) >= .25


def normalise_article_count(value: Any) -> str:
    return _COUNT_RE.sub("10 ", str(value or ""))


def failed_generation_text(value: Any) -> bool:
    text = " ".join(html.unescape(str(value or "")).split())
    return bool(_FAILURE_RE.search(text))


def topic_quality_issues(
    payload: dict[str, Any],
    *,
    expected_title: str | None = None,
    expected_subject: str | None = None,
    require_evidence: bool = True,
    legacy: bool = False,
) -> list[str]:
    issues: list[str] = []
    title = str(payload.get("title") or "")
    identity = expected_title or title or str(payload.get("slug") or "").replace("-", " ")
    if not subject_terms(identity):
        identity = expected_subject or str(payload.get("slug") or "").replace("-", " ")
    if not legacy and expected_title and not matches_subject(title, identity):
        issues.append("title_does_not_match_candidate")
    lead = " ".join(str(payload.get(key) or "") for key in ("summary", "intro"))
    if failed_generation_text(lead):
        issues.append("failed_generation_message")
    if not legacy and not matches_subject(lead, identity):
        issues.append("article_does_not_address_subject")
    items = payload.get("items")
    if not isinstance(items, list) or len(items) != 10:
        issues.append("requires_exactly_ten_facts")
        return list(dict.fromkeys(issues))

    seen_bodies: set[str] = set()
    facts_text = []
    old_source_text = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            issues.append(f"fact_{index}_invalid")
            continue
        fact = str(item.get("title") or "") + " " + str(item.get("body") or "")
        facts_text.append(fact)
        if failed_generation_text(fact):
            issues.append(f"fact_{index}_failed_generation_message")
        body = normalise_text(item.get("body"))
        if body in seen_bodies:
            issues.append(f"fact_{index}_duplicate_body")
        seen_bodies.add(body)
        sources = item.get("sources")
        sources = sources if isinstance(sources, list) else []
        usable = [source for source in sources if isinstance(source, dict)]
        old_source_text.extend(str(source.get("title") or "") + " " + str(source.get("evidence_excerpt") or "") for source in usable)
        if require_evidence:
            related = [source for source in usable if len(str(source.get("evidence_excerpt") or "").strip()) >= 15 and matches_subject(source["evidence_excerpt"], identity)]
            if not related:
                issues.append(f"fact_{index}_sources_do_not_address_subject")
            elif not any(fact_has_support(fact, source["evidence_excerpt"], identity) for source in related):
                issues.append(f"fact_{index}_not_grounded_in_source")

    if legacy:
        # Legacy records are held for a silent mismatch only if none of the
        # subject words appear in the lead, facts OR old source metadata. This
        # avoids treating omitted words or source-grounded aliases as certain
        # defects. New incoming records use the stricter complete-identity and
        # per-fact excerpt gates above.
        # Basic word inflections also count here: Cotswold Hills / Cotswolds is
        # a valid legacy subject variant, not certain evidence of a mismatch.
        corpus = {_stem(word) for word in normalise_text(" ".join([lead, *facts_text, *old_source_text])).split()}
        if not ({_stem(word) for word in subject_terms(identity)} & corpus):
            issues.append("article_and_sources_do_not_address_subject")
    elif not require_evidence and not matches_subject(" ".join(facts_text), identity):
        issues.append("facts_do_not_address_subject")
    return list(dict.fromkeys(issues))
