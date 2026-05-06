#!/usr/bin/env python3
"""
Relationship Care System — interim operational layer for PER-64/PER-33
Mirrors the @ola-turmo/paperclip-relationships plugin data model.
Replace with plugin tools once plugin is enabled (PER-92).

Data files:
  contacts.csv          — Contact records
  interactions.csv       — Interaction logs
  birthdays.csv          — Birthday reminders
  gift_ideas.csv         — Gift ideas
  social_events.csv      — Social calendar
  reconnect_items.csv    — Reconnect tracking
  family_logistics.csv  — Family logistics
  eldercare_checkins.csv — Eldercare check-ins
  runtime.json           — Runtime state (last digest dates)
"""

import csv
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

DATA_DIR = Path(__file__).parent
RUNTIME_FILE = DATA_DIR / "runtime.json"

# --- Tier/category constants (mirrors plugin) ---
RELATIONSHIP_TIERS = ["close", "friend", "acquaintance", "family", "colleague", "professional"]
RELATIONSHIP_CATEGORIES = ["personal", "professional", "family", "health", "community"]
INTERACTION_TYPES = ["call", "video", "in_person", "message", "gift", "event", "other"]
GIFT_STATUSES = ["idea", "purchased", "given"]
FAMILY_LOGISTICS_TYPES = ["transport", "schedule", "healthcare", "financial", "other"]
SCORE_VALUES = [1, 2, 3, 4, 5]

DEFAULT_RECONNECT_LAG_DAYS = 45
DEFAULT_BIRTHDAY_LOOKAHEAD_DAYS = 30
DEFAULT_BIRTHDAY_REMINDER_DAYS = [14, 7, 1]

# --- Helpers ---

def today_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")

def now_iso() -> str:
    return datetime.utcnow().isoformat()

def generate_id() -> str:
    return f"{int(datetime.utcnow().timestamp() * 1000)}-{os.urandom(4).hex()}"

def days_since(iso_date: Optional[str]) -> int:
    if not iso_date:
        return 9999
    try:
        d = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return (datetime.utcnow() - d.replace(tzinfo=None)).days
    except Exception:
        return 9999

def days_until_birthday(mm_dd: str) -> int:
    """Days until next occurrence of MM-DD birthday."""
    today = date.today()
    try:
        bday_this = date(today.year, int(mm_dd[0:2]), int(mm_dd[3:5]))
    except ValueError:
        return 9999
    if bday_this < today:
        bday_this = date(today.year + 1, int(mm_dd[0:2]), int(mm_dd[3:5]))
    return (bday_this - today).days

def load_csv(name: str) -> list[dict]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save_csv(name: str, rows: list[dict], fieldnames: list[str]) -> None:
    path = DATA_DIR / name
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def load_runtime() -> dict:
    if RUNTIME_FILE.exists():
        with open(RUNTIME_FILE) as f:
            return json.load(f)
    return {}

def save_runtime(state: dict) -> None:
    RUNTIME_FILE.write_text(json.dumps(state, indent=2))

def load_contacts() -> list[dict]:
    return load_csv("contacts.csv")

def load_interactions() -> list[dict]:
    return load_csv("interactions.csv")

def load_birthdays() -> list[dict]:
    return load_csv("birthdays.csv")

def load_reconnect_items() -> list[dict]:
    return load_csv("reconnect_items.csv")

# --- Contact actions ---

CONTACT_FIELDS = [
    "id", "name", "relationship", "category", "birthday", "anniversary",
    "phone", "email", "handle", "notes", "tags",
    "lastContactedAt", "reminderFrequencyDays", "createdAt", "updatedAt"
]

def add_contact(
    name: str,
    relationship: str = "acquaintance",
    category: str = "personal",
    birthday: str = "",
    anniversary: str = "",
    phone: str = "",
    email: str = "",
    handle: str = "",
    notes: str = "",
    tags: str = "",
    reminderFrequencyDays: int = DEFAULT_RECONNECT_LAG_DAYS,
) -> dict:
    contacts = load_contacts()
    now = now_iso()
    contact = {
        "id": generate_id(),
        "name": name,
        "relationship": relationship,
        "category": category,
        "birthday": birthday,
        "anniversary": anniversary,
        "phone": phone,
        "email": email,
        "handle": handle,
        "notes": notes,
        "tags": tags,
        "lastContactedAt": "",
        "reminderFrequencyDays": str(reminderFrequencyDays),
        "createdAt": now,
        "updatedAt": "",
    }
    contacts.append(contact)
    save_csv("contacts.csv", contacts, CONTACT_FIELDS)
    # Sync birthday
    if birthday:
        add_birthdayReminder(contact["id"], birthday)
    return contact

def update_contact(contact_id: str, **updates) -> Optional[dict]:
    contacts = load_contacts()
    for i, c in enumerate(contacts):
        if c["id"] == contact_id:
            for k, v in updates.items():
                if v is not None and k not in ("id", "createdAt"):
                    c[k] = v
            c["updatedAt"] = now_iso()
            if "birthday" in updates and updates["birthday"]:
                upsert_birthday_reminder(contact_id, updates["birthday"])
            elif "birthday" in updates and updates["birthday"] == "":
                # Remove birthday
                birthdays = load_birthdays()
                birthdays = [b for b in birthdays if b.get("contactId") != contact_id]
                save_csv("birthdays.csv", birthdays, ["id","contactId","date","reminderDaysBefore","lastSentYear","createdAt","updatedAt"])
            save_csv("contacts.csv", contacts, CONTACT_FIELDS)
            return c
    return None

def get_contact(contact_id: str) -> Optional[dict]:
    contacts = load_contacts()
    return next((c for c in contacts if c["id"] == contact_id), None)

def get_contacts(tier: str = "", category: str = "", tag: str = "", query: str = "") -> list[dict]:
    contacts = load_contacts()
    result = []
    for c in contacts:
        if tier and c.get("relationship") != tier:
            continue
        if category and c.get("category") != category:
            continue
        if tag and tag not in (c.get("tags") or ""):
            continue
        if query:
            q = query.lower()
            haystack = " ".join([
                c.get("name",""), c.get("notes",""), c.get("tags","")
            ]).lower()
            if q not in haystack:
                continue
        result.append(c)
    # Sort newest first
    result.sort(key=lambda x: x.get("updatedAt") or x.get("createdAt") or "", reverse=True)
    return result

# --- Interaction actions ---

INTERACTION_FIELDS = [
    "id", "contactId", "type", "occurredAt", "durationMinutes",
    "summary", "topics", "giftGiven", "location", "notes",
    "followUpItems", "quality", "createdAt", "updatedAt"
]

def log_interaction(
    contact_id: str,
    interaction_type: str = "other",
    occurred_at: str = "",
    duration_minutes: int = 0,
    summary: str = "",
    topics: str = "",
    gift_given: str = "",
    location: str = "",
    notes: str = "",
    follow_up_items: str = "",
    quality: int = 3,
) -> dict:
    contacts = load_contacts()
    if not any(c["id"] == contact_id for c in contacts):
        raise ValueError(f"Contact {contact_id} not found")
    now = now_iso()
    interaction = {
        "id": generate_id(),
        "contactId": contact_id,
        "type": interaction_type,
        "occurredAt": occurred_at or today_iso(),
        "durationMinutes": str(duration_minutes),
        "summary": summary,
        "topics": topics,
        "giftGiven": gift_given,
        "location": location,
        "notes": notes,
        "followUpItems": follow_up_items,
        "quality": str(quality),
        "createdAt": now,
        "updatedAt": "",
    }
    interactions = load_interactions()
    interactions.append(interaction)
    save_csv("interactions.csv", interactions, INTERACTION_FIELDS)
    # Update contact lastContactedAt
    update_contact(contact_id, lastContactedAt=interaction["occurredAt"])
    # Auto-resolve stale reconnect items
    resolve_stale_reconnect(contact_id)
    return interaction

def get_interactions(contact_id: str = "") -> list[dict]:
    interactions = load_interactions()
    if contact_id:
        interactions = [i for i in interactions if i.get("contactId") == contact_id]
    interactions.sort(key=lambda x: x.get("occurredAt") or "", reverse=True)
    return interactions

# --- Birthday actions ---

BIRTHDAY_FIELDS = ["id", "contactId", "date", "reminderDaysBefore", "lastSentYear", "createdAt", "updatedAt"]

def add_birthdayReminder(contact_id: str, birthday_mm_dd: str) -> dict:
    birthdays = load_birthdays()
    for b in birthdays:
        if b.get("contactId") == contact_id:
            b["date"] = birthday_mm_dd
            save_csv("birthdays.csv", birthdays, BIRTHDAY_FIELDS)
            return b
    reminder: dict = {
        "id": generate_id(),
        "contactId": contact_id,
        "date": birthday_mm_dd,
        "reminderDaysBefore": ",".join(map(str, DEFAULT_BIRTHDAY_REMINDER_DAYS)),
        "lastSentYear": "",
        "createdAt": now_iso(),
        "updatedAt": "",
    }
    birthdays.append(reminder)
    save_csv("birthdays.csv", birthdays, BIRTHDAY_FIELDS)
    return reminder

def upsert_birthday_reminder(contact_id: str, birthday_mm_dd: str) -> dict:
    birthdays = load_birthdays()
    for b in birthdays:
        if b.get("contactId") == contact_id:
            b["date"] = birthday_mm_dd
            b["updatedAt"] = now_iso()
            save_csv("birthdays.csv", birthdays, BIRTHDAY_FIELDS)
            return b
    return add_birthdayReminder(contact_id, birthday_mm_dd)

def get_upcoming_birthdays(within_days: int = DEFAULT_BIRTHDAY_LOOKAHEAD_DAYS) -> list[dict]:
    birthdays = load_birthdays()
    contacts = load_contacts()
    contact_map = {c["id"]: c for c in contacts}
    results = []
    for b in birthdays:
        days = days_until_birthday(b.get("date", ""))
        if days <= within_days:
            contact = contact_map.get(b.get("contactId"), {})
            results.append({
                **b,
                "contactName": contact.get("name", "Unknown"),
                "daysUntil": days,
                "occurrenceDate": f"{(date.today() + timedelta(days=days)).isoformat()}",
            })
    results.sort(key=lambda x: x["daysUntil"])
    return results

# --- Reconnect actions ---

RECONNECT_FIELDS = [
    "id", "contactId", "reason", "suggestedOutreach", "addedAt",
    "lastAttemptedAt", "attempts", "completed", "completedAt", "source", "updatedAt"
]

def build_suggested_outreach(contact: dict) -> str:
    tier = contact.get("relationship", "")
    if tier == "family":
        return "Check in personally and ask about logistics, wellbeing, and anything practical they need help with."
    elif tier == "close":
        return "Send a warm catch-up message that references a recent topic and suggest dedicated time together."
    elif tier in ("professional", "colleague"):
        return "Send a short update, mention your last conversation, and ask how things are going on their side."
    else:
        return "Send a light personal note referencing a shared memory, current season, or upcoming occasion."

def add_to_reconnect_list(contact_id: str, reason: str, suggested_outreach: str = "") -> dict:
    contacts = load_contacts()
    contact = next((c for c in contacts if c["id"] == contact_id), None)
    if not contact:
        raise ValueError(f"Contact {contact_id} not found")
    items = load_reconnect_items()
    # Don't add duplicate open items
    if any(i.get("contactId") == contact_id and i.get("completed") != "True" for i in items):
        return next(i for i in items if i.get("contactId") == contact_id and i.get("completed") != "True")
    item: dict = {
        "id": generate_id(),
        "contactId": contact_id,
        "reason": reason,
        "suggestedOutreach": suggested_outreach or build_suggested_outreach(contact),
        "addedAt": today_iso(),
        "lastAttemptedAt": "",
        "attempts": "0",
        "completed": "False",
        "completedAt": "",
        "source": "manual",
        "updatedAt": "",
    }
    items.append(item)
    save_csv("reconnect_items.csv", items, RECONNECT_FIELDS)
    return item

def get_reconnect_list(include_completed: bool = False) -> list[dict]:
    items = load_reconnect_items()
    contacts = load_contacts()
    contact_map = {c["id"]: c for c in contacts}
    if not include_completed:
        items = [i for i in items if i.get("completed") != "True"]
    items.sort(key=lambda x: x.get("addedAt") or "", reverse=True)
    for item in items:
        item["_contact"] = contact_map.get(item.get("contactId"), {})
    return items

def resolve_stale_reconnect(contact_id: str) -> int:
    """Mark auto-generated reconnect items for a contact as completed after fresh interaction."""
    items = load_reconnect_items()
    changed = 0
    contact = get_contact(contact_id)
    lag = int(contact.get("reminderFrequencyDays", str(DEFAULT_RECONNECT_LAG_DAYS))) if contact else DEFAULT_RECONNECT_LAG_DAYS
    for item in items:
        if item.get("contactId") == contact_id and item.get("source") == "automatic" and item.get("completed") != "True":
            # Only resolve if truly fresh
            days = days_since(contact.get("lastContactedAt") if contact else None)
            if days < lag:
                item["completed"] = "True"
                item["completedAt"] = today_iso()
                item["updatedAt"] = now_iso()
                changed += 1
    if changed:
        save_csv("reconnect_items.csv", items, RECONNECT_FIELDS)
    return changed

def refresh_reconnect_list(default_lag_days: int = DEFAULT_RECONNECT_LAG_DAYS) -> dict:
    """Scan contacts and auto-generate reconnect items for stale ones."""
    contacts = load_contacts()
    items = load_reconnect_items()
    created = []
    resolved = []
    for contact in contacts:
        lag = int(contact.get("reminderFrequencyDays") or str(default_lag_days))
        stale = days_since(contact.get("lastContactedAt") or contact.get("createdAt", "")) >= lag
        existing_open = [i for i in items if i.get("contactId") == contact["id"] and i.get("completed") != "True"]
        if stale and not existing_open:
            item = {
                "id": generate_id(),
                "contactId": contact["id"],
                "reason": f"No logged interaction in {days_since(contact.get('lastContactedAt') or contact.get('createdAt',''))} days",
                "suggestedOutreach": build_suggested_outreach(contact),
                "addedAt": today_iso(),
                "lastAttemptedAt": "",
                "attempts": "0",
                "completed": "False",
                "completedAt": "",
                "source": "automatic",
                "updatedAt": "",
            }
            items.append(item)
            created.append(item)
        elif not stale and existing_open:
            for i in existing_open:
                if i.get("source") == "automatic":
                    i["completed"] = "True"
                    i["completedAt"] = today_iso()
                    i["updatedAt"] = now_iso()
                    resolved.append(i)
    save_csv("reconnect_items.csv", items, RECONNECT_FIELDS)
    return {"created": created, "resolved": resolved}

# --- Weekly digest generator ---

def generate_weekly_digest() -> str:
    """Generate a human-readable weekly relationship digest for operator review."""
    contacts = load_contacts()
    birthdays = get_upcoming_birthdays()
    reconnect = get_reconnect_list(include_completed=False)
    interactions = load_interactions()

    today_str = today_iso()
    runtime = load_runtime()
    last_digest = runtime.get("lastWeeklyDigestDate", "")

    # Stale contacts (no interaction in 14+ days)
    stale_14 = [c for c in contacts if days_since(c.get("lastContactedAt") or c.get("createdAt","")) >= 14]

    # Contacts reached in last 7 days
    recent = [c for c in contacts if days_since(c.get("lastContactedAt","")) <= 7]

    lines = [
        f"# Relationship Care Digest — {today_str}",
        f"_Generated by PER-64 interim system. Replace with plugin digest once PER-92 is resolved._",
        "",
        "## Dashboard",
        f"- Total contacts: {len(contacts)}",
        f"- Contacts reached in last 7 days: {len(recent)}",
        f"- Stale contacts (14+ days no contact): {len(stale_14)}",
        f"- Active reconnect items: {len(reconnect)}",
        f"- Upcoming birthdays (next {DEFAULT_BIRTHDAY_LOOKAHEAD_DAYS} days): {len(birthdays)}",
        "",
    ]

    # Birthdays section
    if birthdays:
        lines.append("## Upcoming Birthdays")
        for b in birthdays:
            marker = "🎂 TODAY" if b["daysUntil"] == 0 else f"in {b['daysUntil']} days"
            reminder_days = b.get("reminderDaysBefore", "")
            lines.append(f"- **{b['contactName']}**: {marker} ({b['date']}) — remind {reminder_days or '14,7,1'} days before")
        lines.append("")
    else:
        lines.append("## Upcoming Birthdays")
        lines.append("- None in the next 30 days.")
        lines.append("")

    # Reconnect section
    if reconnect:
        lines.append("## Reconnect List")
        for item in reconnect:
            contact = item.get("_contact", {})
            name = contact.get("name", "Unknown")
            tier = contact.get("relationship", "")
            days_stale = days_since(contact.get("lastContactedAt") or contact.get("createdAt",""))
            lines.append(f"- **{name}** ({tier}) — {days_stale} days since last contact")
            lines.append(f"  Reason: {item.get('reason','—')}")
            lines.append(f"  Suggested: {item.get('suggestedOutreach','—')}")
            lines.append(f"  Attempts: {item.get('attempts','0')}, Source: {item.get('source','manual')}")
        lines.append("")
    else:
        lines.append("## Reconnect List")
        lines.append("- No open reconnect items. All relationships are fresh.")
        lines.append("")

    # Stale contacts section
    if stale_14:
        lines.append("## Stale Contacts (14+ days)")
        for c in sorted(stale_14, key=lambda x: days_since(x.get("lastContactedAt") or x.get("createdAt","")), reverse=True):
            name = c.get("name","?")
            tier = c.get("relationship","?")
            days = days_since(c.get("lastContactedAt") or c.get("createdAt",""))
            notes = c.get("notes","")
            lines.append(f"- **{name}** ({tier}) — {days} days, notes: {notes[:80]}")
        lines.append("")

    # Last 5 interactions
    lines.append("## Recent Interactions")
    recent_ints = interactions[:5]
    if recent_ints:
        for i in recent_ints:
            contact = next((c for c in contacts if c["id"] == i.get("contactId")), {})
            cname = contact.get("name","?") if contact else "?"
            lines.append(f"- {i.get('occurredAt','?')} | {cname} | {i.get('type','?')} | {i.get('summary','—')[:60]}")
    else:
        lines.append("- No interactions logged yet.")
    lines.append("")

    # Operator action items
    lines.append("## Operator Action Items")
    action_items = []
    for b in birthdays:
        if b["daysUntil"] <= 7:
            action_items.append(f"- Birthday: **{b['contactName']}** {'TODAY' if b['daysUntil']==0 else 'soon (' + str(b['daysUntil']) + ' days)'}")
    for item in reconnect[:5]:
        contact = item.get("_contact", {})
        action_items.append(f"- Reach out: **{contact.get('name','?')}** — {item.get('suggestedOutreach','—')[:80]}")
    if not action_items:
        lines.append("- No urgent action items. Relationships are well-maintained.")
    else:
        lines.extend(action_items)
    lines.append("")
    lines.append(f"_Last digest: {last_digest or 'Never'}_")

    return "\n".join(lines)


def mark_digest_sent() -> None:
    runtime = load_runtime()
    runtime["lastWeeklyDigestDate"] = today_iso()
    save_runtime(runtime)


# --- CLI entrypoint ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Relationship Care System")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("digest", help="Generate weekly relationship digest")
    p.add_argument("--output", "-o", help="Output file path")

    p = sub.add_parser("add-contact", help="Add a new contact")
    p.add_argument("--name", required=True)
    p.add_argument("--relationship", default="acquaintance")
    p.add_argument("--category", default="personal")
    p.add_argument("--birthday", default="")  # MM-DD
    p.add_argument("--phone", default="")
    p.add_argument("--email", default="")
    p.add_argument("--tags", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--lag", type=int, default=DEFAULT_RECONNECT_LAG_DAYS, dest="reminderFrequencyDays")

    p = sub.add_parser("log-interaction", help="Log an interaction")
    p.add_argument("--contact-id", required=True)
    p.add_argument("--type", default="other")
    p.add_argument("--occurred-at", default="")
    p.add_argument("--summary", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--quality", type=int, default=3)
    p.add_argument("--topics", default="")
    p.add_argument("--location", default="")

    p = sub.add_parser("list-contacts", help="List contacts")
    p.add_argument("--tier", default="")
    p.add_argument("--query", default="")

    p = sub.add_parser("reconnect", help="Refresh and show reconnect list")
    p.add_argument("--include-completed", action="store_true")

    p = sub.add_parser("birthdays", help="Show upcoming birthdays")
    p.add_argument("--days", type=int, default=30)

    args = parser.parse_args()

    if args.cmd == "digest":
        digest = generate_weekly_digest()
        if args.output:
            Path(args.output).write_text(digest)
            print(f"Digest written to {args.output}")
        else:
            print(digest)
        mark_digest_sent()

    elif args.cmd == "add-contact":
        result = add_contact(
            name=args.name,
            relationship=args.relationship,
            category=args.category,
            birthday=args.birthday,
            phone=args.phone,
            email=args.email,
            tags=args.tags,
            notes=args.notes,
            reminderFrequencyDays=args.reminderFrequencyDays,
        )
        print(f"Contact added: {result['id']} — {result['name']}")

    elif args.cmd == "log-interaction":
        result = log_interaction(
            contact_id=args.contact_id,
            interaction_type=args.type,
            occurred_at=args.occurred_at or today_iso(),
            summary=args.summary,
            notes=args.notes,
            quality=args.quality,
            topics=args.topics,
            location=args.location,
        )
        print(f"Interaction logged: {result['id']}")

    elif args.cmd == "list-contacts":
        contacts = get_contacts(tier=args.tier, query=args.query)
        for c in contacts:
            days = days_since(c.get("lastContactedAt") or c.get("createdAt",""))
            print(f"{c['id'][:12]} | {c['name']} | {c['relationship']} | {c['category']} | {days}d stale | {c.get('birthday','')}")

    elif args.cmd == "reconnect":
        result = refresh_reconnect_list()
        print(f"Created: {len(result['created'])}, Resolved: {len(result['resolved'])}")
        items = get_reconnect_list(include_completed=args.include_completed)
        for item in items:
            contact = item.get("_contact", {})
            print(f"- {contact.get('name','?')} ({item.get('source','?')}) attempts={item.get('attempts','0')} reason={item.get('reason','—')[:50]}")

    elif args.cmd == "birthdays":
        birthdays = get_upcoming_birthdays(within_days=args.days)
        for b in birthdays:
            print(f"{b['contactName']} | {b['date']} | in {b['daysUntil']} days")

    else:
        parser.print_help()
