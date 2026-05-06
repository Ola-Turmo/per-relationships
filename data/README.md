# Relationship Care System — Interim Operational Layer

## Overview

This is an interim Python system for PER-64 / PER-33 relationship tracking.
It mirrors the data model of `@ola-turmo/paperclip-relationships` plugin exactly.

**When PER-92 is resolved** (plugin enabled in Paperclip Board UI), 
replace this with the plugin's built-in digest and tools.

## Quick Start

```bash
# Add a contact
python3 relationships.py add-contact \
  --name "Jane Doe" \
  --relationship close \
  --category personal \
  --birthday "06-15" \
  --phone "+47 ... " \
  --email "jane@example.com" \
  --tags "norway,mentor" \
  --notes "Met at Cloudflare Oslo meetup 2025"

# Log an interaction
python3 relationships.py log-interaction \
  --contact-id <ID> \
  --type in_person \
  --summary "Caught up over coffee, discussed AI agent infra" \
  --topics "ai,cloudflare,infrastructure" \
  --quality 4

# List contacts
python3 relationships.py list-contacts
python3 relationships.py list-contacts --tier family
python3 relationships.py list-contacts --query "norway"

# Show reconnect list
python3 relationships.py reconnect

# Upcoming birthdays
python3 relationships.py birthdays --days 60

# Generate weekly digest
python3 relationships.py digest
python3 relationships.py digest -o /root/per-relationships/digest-2026-04-30.md
```

## Data Files

| File | Content |
|------|---------|
| `contacts.csv` | Name, tier, category, birthday (MM-DD), anniversary, contact info, tags, notes |
| `interactions.csv` | Contact interactions: type, date, quality (1-5), topics, notes, follow-ups |
| `birthdays.csv` | Birthday reminders with reminder-day settings |
| `reconnect_items.csv` | Manual and auto-generated reconnect tracking |
| `gift_ideas.csv` | Gift ideas per contact and occasion |
| `social_events.csv` | Social events with attendees |
| `family_logistics.csv` | Family logistics items |
| `eldercare_checkins.csv` | Eldercare wellbeing check-ins |
| `runtime.json` | Runtime state (last digest date) |

## Relationship Tiers

`close`, `friend`, `acquaintance`, `family`, `colleague`, `professional`

## Categories

`personal`, `professional`, `family`, `health`, `community`

## Interaction Types

`call`, `video`, `in_person`, `message`, `gift`, `event`, `other`

## Reconnect Lag

Default: 45 days. Family contacts: typically 14 days. Set per-contact with `--lag`.

## Cron Setup (replace with plugin jobs once PER-92 is resolved)

```bash
# Weekly digest — run every Sunday 10am
0 10 * * 0 cd /root/per-relationships/data && python3 relationships.py digest >> /root/per-relationships/digests/$(date +\%Y-\%m-\%d).md
```

## Plugin vs Interim Comparison

| Feature | Plugin | Interim |
|---------|--------|---------|
| Birthday reminders | Automated job at 9am | Manual digest |
| Reconnect auto-gen | agent.run.finished + daily job | Manual via `reconnect` command |
| State storage | Paperclip plugin state | CSV files |
| Human gate | Per company policy | Operator reviews digest |
| Installation | Enable in Board UI (PER-92) | Already working |

## PER Issue References

- PER-64: Build relationship care and follow-up loop — **this system is the interim deliverable**
- PER-33: Weekly relationship check-in tracking — use `relationships.py digest` for weekly review
- PER-92: Enable relationships plugin — **unblocks the production plugin solution**
