# Self-Assessment Guide

**How to build your cognitive profile from your own social media data.**

This guide walks you through exporting your data from every supported platform,
running it through the pipeline, and reading your cognitive assessment.

---

## Overview

```
Export from platforms  →  experience-ingest  →  experience-reflect
                                                        ↓
experience-show        ←  experience-synthesize  ←  beliefs.json
```

The more platforms you ingest, the richer your profile. Twitter posts reveal
what you think unprompted. WhatsApp reveals how you respond under pressure.
LinkedIn reveals how you present yourself professionally. Together they show
the gaps between all three — which is where the most useful patterns live.

---

## Step 1: Export Your Data

### WhatsApp
1. Open any active chat on your phone
2. Tap **⋮ (three dots)** → **More** → **Export Chat**
3. Choose **Without Media**
4. Send the `.txt` file to your computer (email or Google Drive)

> **Tip:** Export your most active chat first — the one where you write the most,
> not just receive. Your responses reveal more than messages you read silently.

---

### Twitter / X
1. Go to **Settings** → **Your Account** → **Download an archive of your data**
2. Click **Request archive**
3. Twitter emails you a download link — usually within 24 hours
4. Download and unzip the archive
5. Find `tweets.js` inside the `data/` folder

> **Tip:** Only your original tweets are used. Retweets and replies to others
> are automatically filtered out — only your unprompted thoughts are ingested.

---

### LinkedIn Posts
1. Go to **Settings** → **Data Privacy** → **Get a copy of your data**
2. Select **Posts** (you can select Messages separately in the next step)
3. Click **Request archive**
4. LinkedIn emails you a download link within 24 hours
5. Download and unzip — find `posts.csv`

---

### LinkedIn Messages
1. Same process as above — **Settings** → **Data Privacy** → **Get a copy of your data**
2. Select **Messages**
3. Download and unzip — find `messages.csv`

---

### Telegram
> Must use **Telegram Desktop** — the phone app does not support export.

1. Open **Telegram Desktop**
2. Go to **Settings** → **Advanced** → **Export Telegram Data**
3. Uncheck everything **except** Personal chats
4. Set export format to **JSON**
5. Click **Export**
6. Find `result.json` in the exported folder

---

### Instagram
1. Go to **Settings** → **Your Activity** → **Download Your Information**
2. Select **Messages** and **Posts**
3. Set format to **JSON**
4. Instagram emails you a download link — can take up to 48 hours
5. Download and unzip — find the JSON files inside `messages/inbox/` or `content/`

---

## Step 2: Ingest Your Data

Open your terminal and navigate to your project folder. Run one command per platform.

> **Important:** Replace `"Your Name"` with exactly how your name appears in that app —
> this is how the engine identifies *your* messages in group chats and conversations.

```bash
# WhatsApp
experience-ingest "WhatsApp Chat.txt" --platform whatsapp --user "Ashish"

# Twitter
experience-ingest tweets.js --platform twitter

# LinkedIn posts
experience-ingest posts.csv --platform linkedin_posts

# LinkedIn messages
experience-ingest messages.csv --platform linkedin_messages --user "Ashish Luthara"

# Telegram
experience-ingest result.json --platform telegram --user "Ashish"

# Instagram
experience-ingest messages.json --platform instagram --user "ashishluthara"
```

Each command prints a summary when done:
```
[whatsapp] 312 ingested | 14 skipped | 326 total parsed
[twitter]  847 ingested | 23 skipped | 870 total parsed
```

**Skipped** entries are very short messages (under 15 characters), system
messages, or entries the parser couldn't read cleanly. This is normal.

---

## Step 3: Extract Beliefs (V1)

```bash
experience-reflect
```

This reads your ingested log and extracts domain-level beliefs — your goals,
values, preferences, and recurring themes. Takes 1–3 minutes depending on
log size and your machine.

To analyse more data at once (recommended if you ingested 500+ entries):
```bash
experience-reflect --window 200
```

---

## Step 4: Extract Cognitive Patterns (V2)

```bash
experience-synthesize
```

This is the deeper pass. It reads your beliefs and abstracts them into
cross-domain cognitive patterns — how you think, not just what you think.
Produces your decision archetype and surfaces active cognitive tensions.

---

## Step 5: Read Your Assessment

```bash
experience-show
```

This prints your full cognitive profile. Read slowly. The most useful output
is usually the **tensions** section — these are the contradictions in how you
think that you have likely never explicitly named.

View sections individually:
```bash
experience-show --beliefs     # domain knowledge, values, preferences
experience-show --patterns    # cognitive signature + decision archetype
experience-show --tensions    # active contradictions between beliefs
```

---

## Step 6: Test the Transfer Engine

This is the most revealing step. Give it a real decision you are currently facing
and watch the engine apply your cognitive patterns to it:

```bash
experience-synthesize --transfer "I am deciding whether to quit my job and build this full time"
```

```bash
experience-synthesize --transfer "I am choosing between going deep on one skill or staying broad"
```

```bash
experience-synthesize --transfer "I want to launch a product but I do not feel ready yet"
```

```bash
experience-synthesize --transfer "I am deciding which city to move to"
```

The response uses your specific cognitive patterns — not generic advice.
It names your archetype, applies it to the situation, and flags where your
instinct might work against you.

---

## What to Expect

Assessment quality scales with data volume:

| Data volume | Assessment depth |
|---|---|
| Under 50 messages | Thin — surface observations only |
| 50–200 messages | Useful — 2–3 solid patterns emerge |
| 200–500 messages | Strong — decision archetype becomes clear |
| 500+ messages | Deep — tensions and transfer hypotheses become reliable |

**Highest signal sources, ranked:**

1. **Twitter posts** — unprompted thoughts, highest signal per entry
2. **LinkedIn posts** — how you present ideas publicly
3. **Telegram / WhatsApp** — how you reason in conversation
4. **LinkedIn messages** — professional communication style

Running at least two sources from different contexts (personal + professional,
or public posts + private chats) produces the most accurate profile because
it reveals the gap between how you think publicly and privately.

---

## Troubleshooting

**Patterns feel generic or obvious**
Run reflection with a larger window:
```bash
experience-reflect --window 200
experience-synthesize
```

**"File not found" error**
Make sure you are running the command from the same folder where the export
file is saved. Use `ls` (Mac/Linux) or `dir` (Windows) to check.

**Platform not auto-detected**
Add `--platform` explicitly:
```bash
experience-ingest myfile.txt --platform whatsapp --user "Your Name"
```

**Ollama not running**
```bash
ollama serve
# in a separate terminal:
experience-reflect
```

**Name not matching in chat exports**
Check the exact spelling in your export file — open it in a text editor and
find a message you sent. Copy your name exactly as it appears, including
spaces and capitalisation, and pass it as `--user`.

---

## Privacy Note

All data stays on your machine. Nothing is sent to any server.
The `experience/` folder contains your full profile — treat it like a personal journal.
Add it to `.gitignore` if you are pushing this project to GitHub:

```
experience/
```

This is already included in the default `.gitignore` of this repo.
