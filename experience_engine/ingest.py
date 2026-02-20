"""
ingest.py
---------
Ingest social media exports into the episodic log.

Supported platforms and their export formats:
  WhatsApp    → .txt  (Settings → Chats → Export Chat)
  Twitter/X   → tweets.js  (Settings → Your Account → Download Archive)
  LinkedIn    → posts.csv + messages.csv  (Settings → Data Privacy → Get a copy)
  Instagram   → JSON  (Settings → Your Activity → Download Your Information)
  Telegram    → JSON  (Desktop App → Settings → Export Telegram Data)
  Generic     → .csv or .json  (any flat structure with text content)

Public API:
    ingest(source, platform, config, user_handle) -> IngestResult
    ingest_file(filepath, platform, config, user_handle) -> IngestResult
"""

import json
import re
import csv
import io
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .config import EngineConfig, default_config
from .core import log_interaction


# ── Result object ─────────────────────────────────────────────────────────────

@dataclass
class IngestResult:
    platform:       str
    total_parsed:   int = 0
    total_ingested: int = 0
    skipped:        int = 0
    errors:         list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"[{self.platform}] "
            f"{self.total_ingested} ingested | "
            f"{self.skipped} skipped | "
            f"{self.total_parsed} total parsed"
            + (f" | {len(self.errors)} errors" if self.errors else "")
        )


# ── Normalised entry ──────────────────────────────────────────────────────────

def _make_entry(
    question:  str,
    answer:    str,
    platform:  str,
    timestamp: str | None = None,
    extra_tags: list[str] | None = None,
) -> dict:
    """
    Build a log entry from social content.

    For posts (monologues):   question="" answer=post_text
    For chats (dialogues):    question=their_message answer=user_message
    """
    tags = [f"source:{platform}", "social_media"]
    if extra_tags:
        tags += extra_tags

    return {
        "question":   question.strip(),
        "answer":     answer.strip(),
        "extra_tags": tags,
    }


def _write_entry(entry: dict, config: EngineConfig) -> bool:
    """Write a normalised entry to the log. Returns True on success."""
    if not entry["answer"].strip():
        return False
    try:
        log_interaction(
            question   = entry["question"],
            answer     = entry["answer"],
            config     = config,
            extra_tags = entry.get("extra_tags", []),
        )
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Platform parsers
# ══════════════════════════════════════════════════════════════════════════════

# ── WhatsApp ──────────────────────────────────────────────────────────────────

_WA_LINE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"   # date
    r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?)\s+-\s+"  # time
    r"([^:]+):\s+"                          # sender
    r"(.+)$"                                # message
)

def _parse_whatsapp(text: str, user_handle: str | None) -> list[dict]:
    """
    Parse WhatsApp export txt.
    Groups consecutive messages into Q/A pairs where possible.
    If user_handle provided, user's messages become 'answer', others become 'question'.
    If no handle, treats each message as a standalone post (question="").
    """
    entries = []
    messages = []

    for line in text.splitlines():
        m = _WA_LINE.match(line.strip())
        if m:
            _, _, sender, content = m.groups()
            messages.append({"sender": sender.strip(), "content": content.strip()})
        elif messages and line.strip() and not line.startswith("\u200e"):
            # continuation of previous message
            messages[-1]["content"] += " " + line.strip()

    if not messages:
        return entries

    if user_handle:
        # Pair messages into Q/A
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg["sender"].lower() == user_handle.lower():
                # find preceding message from someone else as the question
                question = ""
                if i > 0 and messages[i-1]["sender"].lower() != user_handle.lower():
                    question = messages[i-1]["content"]
                entries.append(_make_entry(
                    question  = question,
                    answer    = msg["content"],
                    platform  = "whatsapp",
                    extra_tags= ["chat"],
                ))
            i += 1
    else:
        # No handle — treat each message as a standalone post
        for msg in messages:
            if len(msg["content"]) > 20:  # skip very short messages
                entries.append(_make_entry(
                    question  = "",
                    answer    = msg["content"],
                    platform  = "whatsapp",
                    extra_tags= ["chat"],
                ))

    return entries


# ── Twitter / X ───────────────────────────────────────────────────────────────

def _parse_twitter(text: str) -> list[dict]:
    """
    Parse tweets.js from Twitter archive.
    Strips the JavaScript wrapper and extracts tweet text.
    Filters out retweets — only original tweets.
    """
    # Strip JS wrapper: window.YTD.tweets.part0 = [...]
    clean = re.sub(r"^window\.[^=]+=\s*", "", text.strip())
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        # Try parsing as plain JSON array
        try:
            data = json.loads(text)
        except Exception:
            return []

    entries = []
    items = data if isinstance(data, list) else data.get("tweets", [])

    for item in items:
        tweet = item.get("tweet", item)
        content = tweet.get("full_text") or tweet.get("text", "")

        # Skip retweets and replies to others
        if content.startswith("RT @"):
            continue
        if content.startswith("@") and not tweet.get("in_reply_to_user_id") == "":
            continue

        # Clean URLs and mentions for cleaner text
        content = re.sub(r"https://t\.co/\S+", "", content).strip()
        content = re.sub(r"@\w+", "", content).strip()

        if len(content) < 15:
            continue

        entries.append(_make_entry(
            question  = "",
            answer    = content,
            platform  = "twitter",
            extra_tags= ["post", "tweet"],
        ))

    return entries


# ── LinkedIn ──────────────────────────────────────────────────────────────────

def _parse_linkedin_posts(text: str) -> list[dict]:
    """Parse LinkedIn posts.csv export."""
    entries = []
    try:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            # LinkedIn export columns vary — try common ones
            content = (
                row.get("ShareCommentary") or
                row.get("Content") or
                row.get("Text") or
                row.get("Description") or ""
            )
            content = content.strip()
            if len(content) < 20:
                continue
            entries.append(_make_entry(
                question  = "",
                answer    = content,
                platform  = "linkedin",
                extra_tags= ["post"],
            ))
    except Exception:
        pass
    return entries


def _parse_linkedin_messages(text: str, user_handle: str | None) -> list[dict]:
    """Parse LinkedIn messages.csv export."""
    entries = []
    try:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        for i, row in enumerate(rows):
            sender  = (row.get("SENDER NAME") or row.get("From") or "").strip()
            content = (row.get("CONTENT") or row.get("Body") or "").strip()

            if not content or len(content) < 10:
                continue

            # If we know who the user is, only log their messages
            if user_handle and sender.lower() != user_handle.lower():
                continue

            # Use previous message as context/question if from different sender
            question = ""
            if i > 0:
                prev = rows[i-1]
                prev_sender  = (prev.get("SENDER NAME") or prev.get("From") or "").strip()
                prev_content = (prev.get("CONTENT") or prev.get("Body") or "").strip()
                if prev_sender.lower() != sender.lower() and prev_content:
                    question = prev_content

            entries.append(_make_entry(
                question  = question,
                answer    = content,
                platform  = "linkedin",
                extra_tags= ["message", "chat"],
            ))
    except Exception:
        pass
    return entries


# ── Instagram ─────────────────────────────────────────────────────────────────

def _parse_instagram(text: str, user_handle: str | None) -> list[dict]:
    """
    Parse Instagram JSON export.
    Handles both posts (media.json / content/posts_1.json)
    and direct messages (messages/inbox/*/message_1.json).
    """
    entries = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return entries

    # Posts format
    if isinstance(data, list) and data and "media" in data[0]:
        for item in data:
            for media in item.get("media", []):
                caption = media.get("title", "").strip()
                if len(caption) > 20:
                    entries.append(_make_entry(
                        question  = "",
                        answer    = caption,
                        platform  = "instagram",
                        extra_tags= ["post", "caption"],
                    ))
        return entries

    # DM format
    messages = data.get("messages", [])
    if messages:
        for i, msg in enumerate(messages):
            sender  = msg.get("sender_name", "").strip()
            content = msg.get("content", "").strip()

            if not content or len(content) < 10:
                continue
            if user_handle and sender.lower() != user_handle.lower():
                continue

            question = ""
            if i > 0:
                prev = messages[i-1]
                if prev.get("sender_name", "").lower() != sender.lower():
                    question = prev.get("content", "").strip()

            entries.append(_make_entry(
                question  = question,
                answer    = content,
                platform  = "instagram",
                extra_tags= ["dm", "chat"],
            ))

    return entries


# ── Telegram ──────────────────────────────────────────────────────────────────

def _parse_telegram(text: str, user_handle: str | None) -> list[dict]:
    """Parse Telegram export JSON (result.json)."""
    entries = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return entries

    messages = data.get("messages", [])

    for i, msg in enumerate(messages):
        if msg.get("type") != "message":
            continue

        sender  = str(msg.get("from", "")).strip()
        # content can be string or list of text entities
        raw     = msg.get("text", "")
        if isinstance(raw, list):
            content = " ".join(
                part if isinstance(part, str) else part.get("text", "")
                for part in raw
            ).strip()
        else:
            content = str(raw).strip()

        if not content or len(content) < 10:
            continue
        if user_handle and sender.lower() != user_handle.lower():
            continue

        question = ""
        if i > 0:
            prev = messages[i-1]
            if prev.get("type") == "message":
                prev_sender = str(prev.get("from", "")).strip()
                if prev_sender.lower() != sender.lower():
                    prev_raw = prev.get("text", "")
                    if isinstance(prev_raw, list):
                        question = " ".join(
                            p if isinstance(p, str) else p.get("text", "")
                            for p in prev_raw
                        ).strip()
                    else:
                        question = str(prev_raw).strip()

        entries.append(_make_entry(
            question  = question,
            answer    = content,
            platform  = "telegram",
            extra_tags= ["chat", "message"],
        ))

    return entries


# ── Generic CSV / JSON ────────────────────────────────────────────────────────

def _parse_generic_csv(text: str) -> list[dict]:
    """
    Generic CSV parser. Looks for text/content/message/post columns.
    First text-like column with content > 20 chars is used as answer.
    """
    entries = []
    TEXT_COLS = ["text", "content", "message", "post", "body",
                 "caption", "description", "comment", "reply"]
    try:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            content = ""
            for col in TEXT_COLS:
                for key in row:
                    if key.lower().strip() == col and len(row[key].strip()) > 20:
                        content = row[key].strip()
                        break
                if content:
                    break
            if content:
                entries.append(_make_entry(
                    question  = "",
                    answer    = content,
                    platform  = "generic",
                    extra_tags= ["imported"],
                ))
    except Exception:
        pass
    return entries


def _parse_generic_json(text: str) -> list[dict]:
    """
    Generic JSON parser.
    Accepts: list of strings, list of {text/content/message} dicts,
    or {posts: [...]} / {messages: [...]} wrappers.
    """
    entries = []
    TEXT_KEYS = ["text", "content", "message", "post", "body",
                 "caption", "description", "comment"]
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            # unwrap common container keys
            for key in ["posts", "messages", "data", "items", "tweets"]:
                if key in data:
                    data = data[key]
                    break

        if isinstance(data, list):
            for item in data:
                if isinstance(item, str) and len(item) > 20:
                    entries.append(_make_entry("", item, "generic", extra_tags=["imported"]))
                elif isinstance(item, dict):
                    for key in TEXT_KEYS:
                        val = item.get(key, "")
                        if isinstance(val, str) and len(val) > 20:
                            entries.append(_make_entry(
                                "", val, "generic", extra_tags=["imported"]
                            ))
                            break
    except Exception:
        pass
    return entries


# ══════════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════════

SUPPORTED_PLATFORMS = [
    "whatsapp", "twitter", "linkedin_posts", "linkedin_messages",
    "instagram", "telegram", "csv", "json",
]


def ingest(
    source:      str,
    platform:    str,
    config:      EngineConfig = default_config,
    user_handle: str | None   = None,
    verbose:     bool         = True,
) -> IngestResult:
    """
    Ingest social media content into the episodic log.

    Args:
        source:      raw text content of the export file
        platform:    one of: whatsapp | twitter | linkedin_posts |
                     linkedin_messages | instagram | telegram | csv | json
        config:      EngineConfig
        user_handle: your username/display name on the platform.
                     Used to identify YOUR messages in chat exports.
                     For posts-only platforms (Twitter, LinkedIn posts)
                     this is not needed.
        verbose:     print progress

    Returns:
        IngestResult with counts and any error messages.

    Example:
        from experience_engine import ingest
        with open("WhatsApp Chat.txt") as f:
            result = ingest(f.read(), platform="whatsapp", user_handle="Ashish")
        print(result.summary())
    """
    platform = platform.lower().strip()
    result   = IngestResult(platform=platform)

    # Parse
    try:
        if platform == "whatsapp":
            entries = _parse_whatsapp(source, user_handle)
        elif platform == "twitter":
            entries = _parse_twitter(source)
        elif platform == "linkedin_posts":
            entries = _parse_linkedin_posts(source)
        elif platform == "linkedin_messages":
            entries = _parse_linkedin_messages(source, user_handle)
        elif platform == "instagram":
            entries = _parse_instagram(source, user_handle)
        elif platform == "telegram":
            entries = _parse_telegram(source, user_handle)
        elif platform == "csv":
            entries = _parse_generic_csv(source)
        elif platform == "json":
            entries = _parse_generic_json(source)
        else:
            result.errors.append(f"Unknown platform '{platform}'. "
                                  f"Supported: {', '.join(SUPPORTED_PLATFORMS)}")
            return result
    except Exception as e:
        result.errors.append(f"Parse error: {e}")
        return result

    result.total_parsed = len(entries)

    # Write to log
    config.ensure_dirs()
    for entry in entries:
        if _write_entry(entry, config):
            result.total_ingested += 1
        else:
            result.skipped += 1

    if verbose:
        print(f"[ingest] {result.summary()}")

    return result


def ingest_file(
    filepath:    str | Path,
    platform:    str | None   = None,
    config:      EngineConfig = default_config,
    user_handle: str | None   = None,
    verbose:     bool         = True,
) -> IngestResult:
    """
    Ingest a social media export file into the episodic log.
    Platform is auto-detected from filename if not specified.

    Args:
        filepath:    path to the export file
        platform:    override platform detection
        config:      EngineConfig
        user_handle: your username on the platform
        verbose:     print progress

    Returns:
        IngestResult

    Example:
        from experience_engine import ingest_file
        result = ingest_file("tweets.js", user_handle="ashishluthara")
        print(result.summary())
    """
    path = Path(filepath)

    if not path.exists():
        r = IngestResult(platform=platform or "unknown")
        r.errors.append(f"File not found: {filepath}")
        return r

    # Auto-detect platform from filename
    if platform is None:
        name = path.name.lower()
        if "whatsapp" in name or name.endswith(".txt"):
            platform = "whatsapp"
        elif "tweet" in name or name == "tweets.js":
            platform = "twitter"
        elif "message" in name and name.endswith(".csv"):
            platform = "linkedin_messages"
        elif name.endswith(".csv"):
            platform = "linkedin_posts"
        elif "telegram" in name or "result" in name:
            platform = "telegram"
        elif name.endswith(".json"):
            platform = "instagram"
        else:
            platform = "json"

    text = path.read_text(encoding="utf-8", errors="ignore")
    return ingest(text, platform=platform, config=config,
                  user_handle=user_handle, verbose=verbose)
