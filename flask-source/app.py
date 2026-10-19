from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import re
from pathlib import Path
from flask import Flask, Response, abort, request, send_from_directory

from knowledge_store import (
    add_candidates,
    add_signals,
    claim_candidate,
    claim_signal,
    claim_social_job,
    finish_candidate,
    finish_signal,
    finish_social_job,
    get_topic,
    publish_topic,
    search_topics,
    stats as knowledge_stats,
    topic_summaries,
)

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
DATA = json.loads((ROOT / "site_data.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
CATEGORIES = DATA["categories"]
GUIDES = DATA["guides"]
DESTINATIONS = DATA["destinations"]
SITE["description"] = "Evidence-backed ten-point explainers, connected topics and practical seed guides from What10Things."
SITE["tagline"] = "Ten clear things. Sources where they matter."
CATEGORIES.update({
    "science-nature": {"name": "Science & nature", "short": "Understand the world", "description": "Evidence-backed explainers about nature, science, weather, geology and the environment.", "accent": "mint", "symbol": "S"},
    "world": {"name": "World & places", "short": "Understand places", "description": "Geography, countries, cities and the background behind places people are talking about.", "accent": "sky", "symbol": "W"},
    "history-culture": {"name": "History & culture", "short": "Understand the context", "description": "People, events, ideas and cultural subjects explained through sourced facts.", "accent": "sun", "symbol": "C"},
    "general-knowledge": {"name": "General knowledge", "short": "Keep exploring", "description": "Evidence-backed subjects that do not fit neatly into one specialist category.", "accent": "lavender", "symbol": "K"},
})

app = Flask(__name__, static_folder=None)
app.url_map.strict_slashes = False
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024

# The secret itself stays on the Oracle/n8n server. Only its one-way hash is stored here.
AUTOMATION_KEY_SHA256 = os.getenv(
    "W10_AUTOMATION_KEY_SHA256",
    "b76299f1c940b25b2a6f403e5e7ed0cd2efe09d96e2a8f43915b2978bcba5b8b",
).strip().lower()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def json_response(payload: object, status: int = 200) -> Response:
    response = Response(json.dumps(payload, ensure_ascii=False), status=status, mimetype="application/json")
    response.headers["Cache-Control"] = "no-store"
    return response


def automation_authorized() -> bool:
    supplied = request.headers.get("X-Automation-Key", "")
    if not supplied or not AUTOMATION_KEY_SHA256:
        return False
    digest = hashlib.sha256(supplied.encode("utf-8")).hexdigest()
    return hmac.compare_digest(digest, AUTOMATION_KEY_SHA256)


def require_automation() -> Response | None:
    return None if automation_authorized() else json_response({"ok": False, "error": "unauthorised"}, 401)


def header(active: str = "") -> str:
    def nav(url: str, label: str, key: str) -> str:
        current = ' aria-current="page"' if active == key else ""
        return f'<a href="{url}"{current}>{label}</a>'

    return f'''<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header" data-header><div class="shell site-header__inner">
<a class="brand" href="/" aria-label="What 10 Things home"><svg class="brand__mark" viewBox="0 0 48 48" aria-hidden="true"><rect x="3" y="3" width="42" height="42" rx="11"></rect><path d="M14 14h7v20h-7zM27 14h7v20h-7z"></path><path class="brand__slash" d="M10 25h28"></path></svg><span class="brand__text"><strong>What</strong><b>10</b><strong>Things</strong></span></a>
<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-navigation" data-nav-toggle><span></span><span></span><span></span><span class="sr-only">Open menu</span></button>
<nav class="site-nav" id="primary-navigation" aria-label="Primary navigation" data-nav>
{nav('/topics','Explore','topics')}{nav('/guides','Seed guides','guides')}{nav('/travel','Travel','travel')}{nav('/methodology','How we work','methodology')}
<a class="site-nav__search" href="/search" aria-label="Search What 10 Things"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"></circle><path d="m16 16 4 4"></path></svg><span>Search</span></a>
</nav></div></header>'''


def footer() -> str:
    return '''<footer class="site-footer"><div class="shell site-footer__top"><div><a class="brand brand--footer" href="/" aria-label="What 10 Things home"><svg class="brand__mark" viewBox="0 0 48 48" aria-hidden="true"><rect x="3" y="3" width="42" height="42" rx="11"></rect><path d="M14 14h7v20h-7zM27 14h7v20h-7z"></path><path class="brand__slash" d="M10 25h28"></path></svg><span class="brand__text"><strong>What</strong><b>10</b><strong>Things</strong></span></a><p>Ten clear things. Sources where they matter.</p></div><div class="site-footer__links"><div><h2>Explore</h2><a href="/topics">Knowledge topics</a><a href="/guides">Seed guides</a><a href="/travel">Travel</a></div><div><h2>About</h2><a href="/about">About us</a><a href="/methodology">Methodology</a><a href="/contact">Contact</a><a href="/affiliate-disclosure">Affiliate disclosure</a></div><div><h2>Legal</h2><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/sitemap.xml">Sitemap</a></div></div></div><div class="shell site-footer__bottom"><div><p>© 2026 Urban Sky Web Ltd. What 10 Things is a trading name of Urban Sky Web Ltd. Practical information, not personal professional advice.</p><p><strong>What10Things.co.uk is operated by Urban Sky Web Ltd.</strong></p><p>Urban Sky Web Ltd is registered in England and Wales. Company number: 17421062. Registered office: 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX.</p></div><a href="#main-content">Back to top ↑</a></div></footer>'''


def page(title: str, description: str, body: str, *, active: str = "", body_class: str = "") -> Response:
    canonical = "https://what10things.co.uk" + request.path
    doc = f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#101c2c"><meta name="color-scheme" content="light"><link rel="canonical" href="{esc(canonical)}"><link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml"><link rel="manifest" href="/manifest.webmanifest"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="https://what10things.co.uk/assets/img/social-card.svg"><meta name="twitter:card" content="summary_large_image"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="/assets/css/site.css?v=3.0.0"><script defer src="/assets/js/site.js?v=3.0.0"></script></head><body class="{esc(body_class)}">{header(active)}<main id="main-content">{body}</main>{footer()}</body></html>'''
    response = Response(doc, mimetype="text/html")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


def guide_row(slug: str, guide: dict, compact: bool = False) -> str:
    cat = CATEGORIES[guide["category"]]
    compact_class = " guide-row--compact" if compact else ""
    return f'''<article class="guide-row{compact_class}" data-category="{esc(guide['category'])}"><a class="guide-row__link" href="/guides/{esc(slug)}"><span class="guide-row__mark accent-{esc(cat['accent'])}" aria-hidden="true">{esc(cat['symbol'])}</span><span class="guide-row__body"><span class="guide-row__eyebrow">Seed guide · {esc(cat['name'])} · {esc(guide['reading_time'])}</span><strong>{esc(guide['title'])}</strong><span>{esc(guide['summary'])}</span></span><span class="guide-row__arrow" aria-hidden="true">→</span></a></article>'''


def topic_category(topic: dict) -> dict:
    return CATEGORIES.get(topic.get("category")) or {
        "name": str(topic.get("category") or "Knowledge").replace("-", " ").title(),
        "accent": "sky",
        "symbol": "10",
        "description": "Evidence-backed ten-point explainers.",
    }


def topic_row(topic: dict, compact: bool = False) -> str:
    cat = topic_category(topic)
    compact_class = " guide-row--compact" if compact else ""
    return f'''<article class="guide-row{compact_class}" data-category="{esc(topic.get('category',''))}"><a class="guide-row__link" href="/topics/{esc(topic['slug'])}"><span class="guide-row__mark accent-{esc(cat['accent'])}" aria-hidden="true">{esc(cat['symbol'])}</span><span class="guide-row__body"><span class="guide-row__eyebrow">Evidence-backed · {esc(cat['name'])} · {esc(topic.get('reading_time','7 min read'))}</span><strong>{esc(topic['title'])}</strong><span>{esc(topic['summary'])}</span></span><span class="guide-row__arrow" aria-hidden="true">→</span></a></article>'''


def category_item(slug: str, category: dict, index: int) -> str:
    legacy_count = sum(1 for guide in GUIDES.values() if guide["category"] == slug)
    dynamic_count = len(topic_summaries(500, slug))
    count = legacy_count + dynamic_count
    return f'''<a class="category-index__item" href="/category/{esc(slug)}"><span class="category-index__number">{index:02d}</span><span class="category-index__symbol accent-{esc(category['accent'])}">{esc(category['symbol'])}</span><span class="category-index__copy"><strong>{esc(category['name'])}</strong><small>{esc(category['description'])}</small></span><span class="category-index__count">{count} item{'s' if count != 1 else ''}</span><span aria-hidden="true">→</span></a>'''


def dynamic_home_section() -> str:
    topics = topic_summaries(4)
    if topics:
        rows = "".join(topic_row(topic, True) for topic in topics)
        return f'''<section class="section section--featured"><div class="shell split-heading"><div><p class="eyebrow">Evidence-backed knowledge</p><h2>New topics from the knowledge network</h2></div><p>Current interest helps us choose what to explain. The articles themselves focus on durable facts, not live-news reporting.</p></div><div class="shell feature-list">{rows}</div><div class="shell"><a class="text-link" href="/topics">Explore all knowledge topics →</a></div></section>'''
    return '''<section class="section section--featured"><div class="shell split-heading"><div><p class="eyebrow">Building the knowledge network</p><h2>Automated research is now being connected.</h2></div><p>What10Things is being populated from trend signals, evidence research and ten-fact publishing gates. Breaking stories are used to discover subjects worth explaining; they are not republished as live news.</p></div><div class="shell"><a class="text-link" href="/methodology">See how the system works →</a></div></section>'''


@app.get("/")
def home():
    featured = [(slug, g) for slug, g in GUIDES.items() if g.get("featured")]
    lead_slug, lead = featured[0]
    secondary = featured[1:4]
    rails = "".join(f'<div class="ten-rail__line" style="--i:{i}"><span>{10-i}</span><i></i><b>{label}</b></div>' for i, label in enumerate(["Discover", "Research", "Verify", "Explain", "Connect", "Learn", "Explore", "Question", "Share", "Repeat"]))
    cats = "".join(category_item(slug, cat, i) for i, (slug, cat) in enumerate(CATEGORIES.items(), 1))
    body = f'''<section class="hero"><div class="shell hero__grid"><div class="hero__copy"><p class="eyebrow">Useful answers, counted properly</p><h1>Ten clear things.<br><em>No endless scrolling.</em></h1><p class="hero__lede">What10Things is being built into an evidence-backed knowledge network: ten sourced facts about subjects people want to understand, linked to the next useful question.</p><form class="hero-search" action="/search" method="get" role="search"><label for="home-search">What do you need to know?</label><div><input id="home-search" name="q" type="search" placeholder="Try ‘landslides’, ‘Rome’ or ‘Wi-Fi’" autocomplete="off"><button type="submit">Find ten things <span aria-hidden="true">→</span></button></div></form><div class="hero__quick-links"><span>Explore:</span><a href="/topics">Knowledge topics</a><a href="/methodology">How we research</a><a href="/guides">Seed guides</a></div></div><div class="hero__visual"><div class="ten-rail" aria-label="Ten knowledge stages">{rails}</div></div></div></section>'''
    body += dynamic_home_section()
    body += f'''<section class="section section--featured"><div class="shell split-heading"><div><p class="eyebrow">Seed content</p><h2>The original launch guides remain while the automated catalogue grows</h2></div><p>These pages are the starting content set. They are separate from the new evidence-backed knowledge pipeline and are labelled accordingly.</p></div><div class="shell feature-layout"><article class="feature-lead"><a href="/guides/{esc(lead_slug)}"><div class="feature-lead__number">10</div><div class="feature-lead__content"><span class="pill">Seed guide</span><h3>{esc(lead['title'])}</h3><p>{esc(lead['summary'])}</p><strong>Read the guide <span aria-hidden="true">→</span></strong></div></a></article><div class="feature-list">{''.join(guide_row(s,g,True) for s,g in secondary)}</div></div></section>
<section class="section section--categories"><div class="shell"><div class="section-heading section-heading--inline"><div><p class="eyebrow">Browse by subject</p><h2>One ten-point format, multiple areas of knowledge</h2></div><a class="text-link" href="/topics">Browse evidence-backed topics →</a></div><div class="category-index">{cats}</div></div></section>'''
    return page("What 10 Things", SITE["description"], body, body_class="home-page")


@app.get("/topics")
def topics():
    rows = topic_summaries(200)
    content = "".join(topic_row(topic) for topic in rows) if rows else '<div class="no-results"><strong>The automated knowledge catalogue is being populated.</strong><p>No automated topic appears here until it passes the ten-fact evidence gate.</p><a href="/methodology">Read the methodology →</a></div>'
    body = f'''<section class="page-hero"><div class="shell"><p class="eyebrow">Knowledge network</p><h1>Ten facts. Sources attached. Topics connected.</h1><p>Explore evidence-backed explainers selected from public-interest signals and related questions. We explain the underlying subject rather than trying to report breaking news.</p></div></section><section class="section"><div class="shell"><div class="guide-list">{content}</div></div></section>'''
    return page("Explore topics | What 10 Things", "Evidence-backed ten-fact explainers and their connected topics.", body, active="topics")


@app.get("/topics/<slug>")
def topic(slug: str):
    item = get_topic(slug)
    if not item:
        abort(404)
    cat = topic_category(item)
    trigger = item.get("trigger") or {}
    trigger_note = ""
    if trigger.get("query") or trigger.get("title"):
        label = trigger.get("query") or trigger.get("title")
        trigger_note = f'''<aside class="topic-trigger"><strong>Why we researched this</strong><p>Interest around “{esc(label)}” helped surface this subject. This page explains the underlying topic; it is not live-news coverage.</p></aside>'''
    fact_html = []
    for fact in item["items"]:
        source_links = []
        for source in fact.get("sources", []):
            label = source.get("publisher") or source.get("title") or "Source"
            source_links.append(f'<a href="{esc(source["url"])}" rel="nofollow noopener noreferrer" target="_blank">{esc(label)}</a>')
        sources = " · ".join(source_links)
        fact_html.append(f'''<article class="numbered-point evidence-point"><span>{fact['position']}</span><div><h2>{esc(fact['title'])}</h2><p>{esc(fact['body'])}</p><div class="fact-evidence"><strong>Sources</strong> {sources}<small>Evidence confidence: {round(float(fact['confidence']) * 100)}%</small></div></div></article>''')
    related = []
    for rel in item.get("related_topics", []):
        if get_topic(rel["to_slug"]):
            related.append(f'<a href="/topics/{esc(rel["to_slug"])}">{esc(rel["to_title"])} →</a>')
        else:
            related.append(f'<span>{esc(rel["to_title"])} <small>research candidate</small></span>')
    related_html = "".join(related) or '<span>Related subjects will appear here as the knowledge graph grows.</span>'
    body = f'''<article class="guide-article topic-article"><header class="guide-hero"><div class="shell guide-hero__grid"><div><p class="eyebrow">{esc(cat['name'])} · Evidence-backed</p><h1>{esc(item['title'])}</h1><p class="guide-hero__lede">{esc(item['intro'])}</p><div class="guide-meta"><span>{esc(item['reading_time'])}</span><span>Quality gate {round(float(item['quality_score']) * 100)}%</span><span>Updated {esc(item['updated_at'][:10])}</span></div></div><div class="guide-hero__number" aria-hidden="true">10</div></div></header><div class="shell article-layout"><div class="article-main"><p class="article-intro">{esc(item['summary'])}</p>{trigger_note}<div class="numbered-list">{''.join(fact_html)}</div><div class="article-end"><strong>That is the ten.</strong><p>Every numbered claim above was required to carry source evidence before this topic could be published.</p></div></div><aside class="article-aside"><div class="aside-card"><span class="accent-{esc(cat['accent'])}">{esc(cat['symbol'])}</span><h2>Connected topics</h2><div class="topic-relations">{related_html}</div><a href="/methodology">How evidence is checked →</a></div></aside></div></article>'''
    return page(f"{item['title']} | What 10 Things", item["summary"], body, active="topics")


@app.get("/guides")
def guides():
    rows = "".join(guide_row(slug, guide) for slug, guide in GUIDES.items())
    filters = "".join(f'<button type="button" data-filter="{esc(slug)}">{esc(cat["name"])}</button>' for slug, cat in CATEGORIES.items() if any(g["category"] == slug for g in GUIDES.values()))
    body = f'''<section class="page-hero"><div class="shell"><p class="eyebrow">Seed guides</p><h1>The original ten-point launch content.</h1><p>These guides pre-date the automated evidence pipeline. They remain useful seed content while the new knowledge network is populated.</p></div></section><section class="section"><div class="shell"><div class="filter-bar" data-filter-bar><button class="is-active" type="button" data-filter="all">All</button>{filters}</div><div class="guide-list" data-guide-list>{rows}</div></div></section>'''
    return page("Seed guides | What 10 Things", "Browse the original ten-point seed guides.", body, active="guides")


@app.get("/guides/<slug>")
def guide(slug: str):
    guide = GUIDES.get(slug)
    if not guide:
        abort(404)
    cat = CATEGORIES[guide["category"]]
    items = "".join(f'''<article class="numbered-point"><span>{i}</span><div><h2>{esc(item['title'])}</h2><p>{esc(item['body'])}</p></div></article>''' for i, item in enumerate(guide["items"], 1))
    related = [(s,g) for s,g in GUIDES.items() if s != slug and g["category"] == guide["category"]][:3]
    body = f'''<article class="guide-article"><header class="guide-hero"><div class="shell guide-hero__grid"><div><p class="eyebrow">Seed guide · {esc(cat['name'])}</p><h1>{esc(guide['title'])}</h1><p class="guide-hero__lede">{esc(guide['intro'])}</p><div class="guide-meta"><span>{esc(guide['reading_time'])}</span><span>Updated {esc(guide['updated'])}</span></div></div><div class="guide-hero__number" aria-hidden="true">10</div></div></header><div class="shell article-layout"><div class="article-main"><p class="article-intro">{esc(guide['summary'])}</p><aside class="topic-trigger"><strong>Seed content</strong><p>This page is part of the original launch set and does not yet use the newer per-fact evidence pipeline.</p></aside><div class="numbered-list">{items}</div></div><aside class="article-aside"><div class="aside-card"><span class="accent-{esc(cat['accent'])}">{esc(cat['symbol'])}</span><h2>{esc(cat['name'])}</h2><p>{esc(cat['description'])}</p><a href="/category/{esc(guide['category'])}">More in this category →</a></div></aside></div></article><section class="section section--related"><div class="shell"><div class="section-heading"><p class="eyebrow">Keep going</p><h2>Related seed guides</h2></div><div class="feature-list">{''.join(guide_row(s,g,True) for s,g in related)}</div></div></section>'''
    return page(f"{guide['title']} | What 10 Things", guide["summary"], body)


@app.get("/category/<slug>")
def category(slug: str):
    cat = CATEGORIES.get(slug)
    if not cat:
        abort(404)
    dynamic = topic_summaries(100, slug)
    legacy = [(s,g) for s,g in GUIDES.items() if g["category"] == slug]
    content = "".join(topic_row(t) for t in dynamic) + "".join(guide_row(s,g) for s,g in legacy)
    if not content:
        content = '<div class="no-results"><strong>More topics are being researched.</strong><p>Browse the knowledge network while this category grows.</p></div>'
    body = f'''<section class="category-hero"><div class="shell category-hero__grid"><div><p class="eyebrow">Category</p><h1>{esc(cat['name'])}</h1><p>{esc(cat['description'])}</p></div><div class="category-hero__symbol accent-{esc(cat['accent'])}">{esc(cat['symbol'])}</div></div></section><section class="section"><div class="shell"><div class="guide-list">{content}</div></div></section>'''
    return page(f"{cat['name']} | What 10 Things", cat["description"], body)


@app.get("/travel")
def travel():
    cards = "".join(f'''<article class="destination-card"><a href="/travel/{esc(slug)}"><span>{esc(place['region'])} · {esc(place['country'])}</span><h2>{esc(place['name'])}</h2><p>{esc(place['summary'])}</p><strong>Explore {esc(place['name'])} →</strong></a></article>''' for slug, place in DESTINATIONS.items())
    body = f'''<section class="travel-hero"><div class="shell travel-hero__grid"><div><p class="eyebrow">Travel seed content</p><h1>Know the ten things before you go.</h1><p>The original destination set remains available while travel subjects are moved into the evidence-backed topic pipeline.</p></div><div class="travel-hero__stamp">10<br><small>places</small></div></div></section><section class="section"><div class="shell destination-grid">{cards}</div></section>'''
    return page("Travel guides | What 10 Things", "Practical first-trip and family holiday guidance.", body, active="travel")


@app.get("/travel/<slug>")
def destination(slug: str):
    place = DESTINATIONS.get(slug)
    if not place:
        abort(404)
    linked = GUIDES.get(place.get("guide"))
    guide_link = f'''<article class="feature-lead"><a href="/guides/{esc(place['guide'])}"><div class="feature-lead__number">10</div><div class="feature-lead__content"><span class="pill">Seed guide</span><h2>{esc(linked['title'])}</h2><p>{esc(linked['summary'])}</p><strong>Read the ten things →</strong></div></a></article>''' if linked else ""
    nearby = [(s,p) for s,p in DESTINATIONS.items() if s != slug and p["region"] == place["region"]][:3]
    body = f'''<section class="destination-hero"><div class="shell destination-hero__grid"><div><p class="eyebrow">{esc(place['region'])} · {esc(place['country'])}</p><h1>{esc(place['name'])}</h1><p>{esc(place['summary'])}</p><a class="button" href="#guide">Start planning ↓</a></div><div class="destination-hero__word" aria-hidden="true">{esc(place['name'][:3].upper())}</div></div></section><section class="section" id="guide"><div class="shell feature-layout">{guide_link}<div class="planning-list"><h2>Before you book</h2><ol><li>Choose dates around weather, crowds and school holidays.</li><li>Compare the whole journey, not only the headline fare.</li><li>Map the neighbourhood before choosing accommodation.</li><li>Pre-book only the attractions that genuinely sell out.</li><li>Keep arrival day simple and leave recovery time.</li></ol></div></div></section><section class="section section--related"><div class="shell"><div class="section-heading"><p class="eyebrow">Also in {esc(place['region'])}</p><h2>Continue exploring</h2></div><div class="destination-strip">{''.join(f'<a href="/travel/{esc(s)}"><span>{esc(p["country"])}</span><strong>{esc(p["name"])}</strong><small>{esc(p["summary"])}</small><b>Explore →</b></a>' for s,p in nearby)}</div></div></section>'''
    return page(f"{place['name']} travel guide | What 10 Things", place["summary"], body, active="travel")


def search_items(query: str):
    terms = [t for t in re.split(r"\s+", query.casefold().strip()) if t]
    results = []
    if not terms:
        return results
    for slug, guide in GUIDES.items():
        hay = " ".join([slug, guide["title"], guide["summary"], guide["intro"]]).casefold()
        score = sum(hay.count(t) for t in terms)
        if score:
            results.append((score, "Seed guide", guide["title"], guide["summary"], f"/guides/{slug}"))
    for slug, cat in CATEGORIES.items():
        hay = " ".join([slug, cat["name"], cat["description"]]).casefold()
        score = sum(hay.count(t) for t in terms)
        if score:
            results.append((score, "Category", cat["name"], cat["description"], f"/category/{slug}"))
    for slug, place in DESTINATIONS.items():
        hay = " ".join([slug, place["name"], place["country"], place["region"], place["summary"]]).casefold()
        score = sum(hay.count(t) for t in terms)
        if score:
            results.append((score, "Destination", place["name"], place["summary"], f"/travel/{slug}"))
    for topic in search_topics(query, 30):
        results.append((topic["score"] + 2, "Evidence-backed topic", topic["title"], topic["summary"], f"/topics/{topic['slug']}"))
    return sorted(results, key=lambda x: (-x[0], x[2]))[:30]


@app.get("/search")
def search():
    query = request.args.get("q", "").strip()[:100]
    results = search_items(query)
    safe = esc(query)
    if query and results:
        cards = "".join(f'<article><a href="{esc(url)}"><span>{esc(kind)}</span><h2>{esc(title)}</h2><p>{esc(summary)}</p><b aria-hidden="true">→</b></a></article>' for _,kind,title,summary,url in results)
        content = f'<p class="search-count">{len(results)} results</p><div class="search-results">{cards}</div>'
    elif query:
        content = '<p class="search-count">0 results</p><div class="no-results"><strong>No exact match yet.</strong><p>Try a shorter word or browse evidence-backed topics.</p><div><a href="/topics">Knowledge topics</a><a href="/guides">Seed guides</a></div></div>'
    else:
        content = '<div class="search-suggestions"><span>Try:</span><a href="/search?q=landslide">landslide</a><a href="/search?q=wifi">Wi-Fi</a><a href="/search?q=energy">energy</a></div>'
    body = f'''<section class="search-page"><div class="shell search-page__inner"><p class="eyebrow">Search the site</p><h1>{'Results for “'+safe+'”' if query else 'What do you need to know?'}</h1><form class="search-form" action="/search" method="get" role="search"><label for="site-search">Search topics, guides and places</label><div><input id="site-search" type="search" name="q" value="{safe}" placeholder="Type a subject"><button type="submit">Search</button></div></form>{content}</div></section>'''
    return page("Search | What 10 Things", "Search evidence-backed topics, seed guides, categories and destinations.", body)


STATIC_PAGES = {
    "about": ("About What 10 Things", "What What10Things is building and how it is being populated.", "About us", "What10Things is being developed as an evidence-backed knowledge network organised around ten clear facts. The automated research system is being rolled out progressively; existing seed guides remain while the knowledge graph grows."),
    "methodology": ("How we work | What 10 Things", "How trends, evidence and automation are used to build What10Things.", "How we work", "Current interest helps us decide what to research. Breaking events are discovery signals, not stories for us to rewrite. We research the underlying subject, require sources for every published automated fact and use related facts to build an interconnected knowledge graph."),
    "contact": ("Contact | What 10 Things", "Contact the What 10 Things team.", "Contact", "For corrections, partnership enquiries or suggestions for a future topic, email hello@what10things.co.uk. Please include the page address when reporting an issue."),
    "privacy": ("Privacy | What 10 Things", "Privacy information for What 10 Things.", "Privacy", "We minimise personal data collection. Standard hosting logs may record technical information such as IP address, browser and requested pages for security and reliability. Contact messages are used only to respond to the enquiry."),
    "terms": ("Terms | What 10 Things", "Terms for using What 10 Things.", "Terms", "The site provides general information, not personal professional advice. Check important decisions against current official guidance and the terms of any product, booking or service you use."),
    "affiliate-disclosure": ("Affiliate disclosure | What 10 Things", "How affiliate links are handled.", "Affiliate disclosure", "Some pages may contain affiliate links. A commission may be earned when a reader buys through one of those links, without increasing the price paid. Commercial relationships do not determine the ten points included in a page."),
}

RICH_PAGES = {
    "about": '''<h2>What exists today</h2><p>The site began with a small set of manually prepared seed guides. We are now adding an automated knowledge pipeline that discovers subjects, verifies facts and publishes evidence-backed ten-point explainers.</p><h2>What we are building</h2><p>Each automated topic contains exactly ten sourced facts. Facts can point to related topics, allowing the site to grow as an interconnected knowledge network rather than a pile of unrelated articles.</p><h2>News is a signal, not our product</h2><p>A breaking event may show that people suddenly want to understand landslides, a place, a scientific idea or another subject. We use that interest to choose an evergreen explanation. We do not present automated breaking-news summaries as original reporting.</p>''',
    "methodology": '''<h2>1. Discover</h2><p>Trend and public-interest signals identify subjects people are trying to understand. A signal is queued and scored for lasting usefulness.</p><h2>2. Map the evergreen subject</h2><p>The system separates the underlying subject from the live event. A flood story, for example, may lead to an explainer about how landslides form rather than a page claiming to report the unfolding incident.</p><h2>3. Research and verify</h2><p>Candidate facts must be supported by retrievable sources. Published automated topics require exactly ten facts, a confidence threshold and at least one source per fact. Weak research is rejected instead of padded into a page.</p><h2>4. Link the knowledge graph</h2><p>Strong related subjects return to the research queue. Expansion is deliberately gated so one page does not automatically create hundreds of low-value pages.</p><h2>5. Reuse verified facts</h2><p>Once a topic passes the publishing gate, its verified facts can be used to create image cards, carousels, short videos and responses to genuine audience questions.</p><h2>Corrections</h2><p>Sources are shown on evidence-backed topic pages. If a claim needs correcting, contact us with the page address and the supporting source.</p>''',
    "contact": '''<h2>Email</h2><p>For corrections, partnership enquiries or topic ideas, email <a href="mailto:hello@what10things.co.uk">hello@what10things.co.uk</a>. Do not send confidential documents or sensitive personal information.</p><h2>Company details</h2><p>What10Things.co.uk is operated by Urban Sky Web Ltd, registered in England and Wales under company number 17421062.</p><p>Registered office: 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX.</p>''',
    "privacy": '''<h2>Controller and contact</h2><p>Urban Sky Web Ltd is the controller of personal information handled through What10Things.co.uk. It is registered in England and Wales under company number 17421062. Its registered office is 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX. Privacy requests can be sent to <a href="mailto:privacy@what10things.co.uk">privacy@what10things.co.uk</a>.</p><h2>Information, purposes and lawful bases</h2><p>The core site can be read without an account. The hosting provider may process routine IP-address, browser, requested-page, time, error and security logs. Search terms are processed to return results and may appear in routine request logs; do not enter personal information. We rely on legitimate interests to deliver, secure, troubleshoot and improve the site.</p><p>If you email us, we use your address, message and related correspondence to reply, investigate corrections, administer the relationship and protect legal rights. The lawful basis is legitimate interests, or steps connected with a requested service where applicable. Information may also be processed to meet a legal obligation or establish, exercise or defend legal claims.</p><h2>Cookies and fonts</h2><p>The current site does not use analytics or advertising cookies. Pages request font files through Google Fonts, so Google may receive technical request information such as an IP address and browser details. We rely on legitimate interests in presenting a readable service and keep this use under review.</p><h2>Recipients and international transfers</h2><p>Information may be processed by providers supporting hosting, security, email and font delivery, and by professional advisers or public authorities where necessary. Some providers may process information outside the United Kingdom. Where required, we rely on an applicable adequacy regulation or approved contractual safeguards and supplementary measures. You may ask for information about the safeguard used.</p><h2>Retention</h2><p>Correspondence is normally deleted within 24 months after an enquiry is closed unless a longer period is needed for an ongoing relationship, legal claim or legal obligation. Hosting and security logs follow the provider's operational schedule. Retention is reviewed and information is deleted or anonymised when no longer needed.</p><h2>Your rights and complaints</h2><p>Depending on the circumstances, you may request access, correction, deletion, restriction or portability. You may object to processing based on legitimate interests. We may need reasonable information to locate and verify a request. The site does not use personal information for solely automated decisions with legal or similarly significant effects.</p><p>Please contact us first so we can investigate. You also have the right to complain to the <a href="https://ico.org.uk/make-a-complaint/data-protection-complaints/">Information Commissioner's Office</a>.</p>''',
    "terms": '''<h2>Website operator</h2><p>What10Things.co.uk is operated by Urban Sky Web Ltd, registered in England and Wales under company number 17421062. Registered office: 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX.</p><h2>General information</h2><p>What 10 Things provides general editorial information, not personalised legal, financial, medical or other professional advice.</p><h2>Accuracy and external services</h2><p>Facts, prices, services and rules can change. Check important current details with the relevant official source or provider. We do not control external websites, their availability, privacy practices or transactions.</p><h2>Acceptable use and intellectual property</h2><p>Use the site lawfully. Do not disrupt it, attempt unauthorised access, scrape at a harmful rate or republish substantial parts as your own work. Unless stated otherwise, original text, design and branding are protected by applicable intellectual-property law.</p><h2>Liability</h2><p>To the extent permitted by law, we are not responsible for losses caused by relying on outdated, incomplete or third-party information. Nothing excludes rights or liability that cannot legally be excluded.</p>''',
    "affiliate-disclosure": '''<h2>Website operator</h2><p>What10Things.co.uk is operated by Urban Sky Web Ltd, registered in England and Wales under company number 17421062. Registered office: 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX.</p><h2>How affiliate links work</h2><p>Some future pages may contain affiliate links. If a visitor follows one and makes a qualifying purchase, What 10 Things may receive a commission without increasing the price paid.</p><h2>Clear advertising labels</h2><p>Any affiliate offer or outgoing commercial button will be visibly marked <strong>Ad</strong> beside the link. A footer or this page will not be used as a substitute for a nearby label.</p><h2>Editorial independence</h2><p>Payment, free products or affiliate availability do not guarantee inclusion or allow a partner to approve a conclusion. Prices, stock and terms can change, so check the destination before buying.</p>''',
}


def static_page(slug: str):
    title, description, heading, copy = STATIC_PAGES[slug]
    company = ""
    if slug in {"about", "privacy", "terms", "affiliate-disclosure"}:
        company = '''<h2>Website operator</h2><p>What10Things.co.uk is operated by Urban Sky Web Ltd.</p><p>Urban Sky Web Ltd is a company registered in England and Wales under company number 17421062. Its registered office is 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX.</p>'''
    detail = RICH_PAGES.get(slug, f'<h2>Clear, useful and accountable</h2><p>{esc(description)}</p>')
    body = f'''<section class="page-hero"><div class="shell"><p class="eyebrow">What 10 Things</p><h1>{esc(heading)}</h1><p>{esc(copy)}</p></div></section><section class="section"><div class="shell prose">{company}{detail}<p>Last updated 29 August 2026.</p></div></section>'''
    return page(title, description, body, active="methodology" if slug == "methodology" else "")


for _slug in STATIC_PAGES:
    app.add_url_rule(f"/{_slug}", _slug.replace("-", "_"), lambda slug=_slug: static_page(slug))


@app.get("/api/status")
def api_status():
    return json_response({"ok": True, "knowledge": knowledge_stats(), "mode": "building"})


@app.get("/api/topics")
def api_topics():
    try:
        limit = min(max(int(request.args.get("limit", 100) or 100), 1), 500)
    except ValueError:
        limit = 100
    return json_response({"ok": True, "topics": topic_summaries(limit)})


@app.get("/api/topics/<slug>")
def api_topic(slug: str):
    item = get_topic(slug)
    return json_response({"ok": bool(item), "topic": item}, 200 if item else 404)


@app.post("/api/automation/signals/batch")
def automation_signals_batch():
    denied = require_automation()
    if denied:
        return denied
    payload = request.get_json(silent=True) or {}
    signals = payload.get("signals") if isinstance(payload, dict) else None
    if not isinstance(signals, list):
        return json_response({"ok": False, "error": "signals must be an array"}, 400)
    return json_response({"ok": True, **add_signals(signals)})


@app.post("/api/automation/signals/claim")
def automation_signal_claim():
    denied = require_automation()
    if denied:
        return denied
    return json_response({"ok": True, "signal": claim_signal()})


@app.post("/api/automation/signals/<int:signal_id>/result")
def automation_signal_result(signal_id: int):
    denied = require_automation()
    if denied:
        return denied
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status") or "mapped")
    try:
        candidate_result = add_candidates(payload.get("candidates") or [], signal_id=signal_id) if status == "mapped" else {"inserted": 0, "updated": 0}
        finish_signal(signal_id, status, payload.get("error"))
    except ValueError as exc:
        return json_response({"ok": False, "error": str(exc)}, 400)
    return json_response({"ok": True, "candidates": candidate_result})


@app.post("/api/automation/candidates/claim")
def automation_candidate_claim():
    denied = require_automation()
    if denied:
        return denied
    return json_response({"ok": True, "candidate": claim_candidate()})


@app.post("/api/automation/candidates/<int:candidate_id>/result")
def automation_candidate_result(candidate_id: int):
    denied = require_automation()
    if denied:
        return denied
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status") or "published")
    try:
        if status == "published":
            topic_payload = payload.get("topic")
            if not isinstance(topic_payload, dict):
                return json_response({"ok": False, "error": "topic payload is required"}, 400)
            result = publish_topic(topic_payload, candidate_id=candidate_id)
            return json_response({"ok": True, **result})
        actual_status = finish_candidate(candidate_id, status, payload.get("error"))
        return json_response({"ok": True, "status": actual_status or status})
    except ValueError as exc:
        actual_status = finish_candidate(candidate_id, "retry", str(exc))
        return json_response({"ok": False, "error": str(exc), "status": actual_status or "failed"}, 422)


@app.post("/api/automation/social/claim")
def automation_social_claim():
    denied = require_automation()
    if denied:
        return denied
    return json_response({"ok": True, "job": claim_social_job()})


@app.post("/api/automation/social/<int:job_id>/result")
def automation_social_result(job_id: int):
    denied = require_automation()
    if denied:
        return denied
    payload = request.get_json(silent=True) or {}
    try:
        finish_social_job(job_id, str(payload.get("status") or "ready"), payload.get("result"), payload.get("error"))
    except ValueError as exc:
        return json_response({"ok": False, "error": str(exc)}, 400)
    return json_response({"ok": True})


@app.get("/assets/<path:filename>")
def assets(filename: str):
    return send_from_directory(ASSETS, filename, max_age=604800)


@app.get("/robots.txt")
def robots():
    return send_from_directory(ROOT, "robots.txt", mimetype="text/plain")


@app.get("/manifest.webmanifest")
def manifest():
    return send_from_directory(ROOT, "manifest.webmanifest", mimetype="application/manifest+json")


@app.get("/sitemap.xml")
def sitemap():
    urls = ["/", "/topics", "/guides", "/travel", "/search", "/about", "/methodology", "/contact", "/privacy", "/terms", "/affiliate-disclosure"]
    urls += [f"/guides/{slug}" for slug in GUIDES]
    urls += [f"/category/{slug}" for slug in CATEGORIES]
    urls += [f"/travel/{slug}" for slug in DESTINATIONS]
    urls += [f"/topics/{topic['slug']}" for topic in topic_summaries(500)]
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>https://what10things.co.uk{esc(url)}</loc></url>' for url in urls) + '</urlset>'
    return Response(xml, mimetype="application/xml")


@app.errorhandler(404)
def not_found(_error):
    body = '''<section class="not-found"><div class="shell not-found__grid"><div class="not-found__number" aria-hidden="true">10?</div><div><p class="eyebrow">Page not found</p><h1>That is one thing we could not find.</h1><p>The address may have changed or the topic may not exist yet.</p><form class="search-form" action="/search" method="get"><label for="404-search">Search What 10 Things</label><div><input id="404-search" name="q" type="search" placeholder="What are you looking for?"><button type="submit">Search</button></div></form><a class="text-link" href="/topics">Explore knowledge topics →</a></div></div></section>'''
    response = page("Page not found | What 10 Things", "The page could not be found.", body)
    response.status_code = 404
    return response


application = app

if __name__ == "__main__":
    app.run(debug=True)
