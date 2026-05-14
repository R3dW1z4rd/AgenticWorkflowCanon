# Discovery Workshop Facilitation Guide
*A practical playbook for consultants running discovery sessions with clients. Covers setup, facilitation techniques, client patterns, and how to use Miro and Google Suite effectively at each stage.*

---

## The Facilitation Mindset

Before opening any tool, internalize these principles:

**You are not taking an order. You are building shared understanding.**
Clients rarely know what they want with precision. They know the problem they feel, the outcome they desire, and often a rough idea of the solution. Your job is to translate all three into something buildable — and to catch the gaps before they become change requests.

**Silence is a signal, not a pause.**
When a client hesitates or gives a vague answer, don't fill the gap. Ask a follow-up. Vagueness at this stage is a risk that will manifest later as rework.

**Make it visual as early as possible.**
The moment you draw something — even a rough box diagram — the client will either say "yes, exactly" or "no, not like that." Both answers are enormously useful. Miro is your best tool for this.

**Separate the vision conversation from the process conversation.**
Clients can talk about their vision for hours. The operational/process conversation is harder and less exciting for them — but it's where your project will succeed or fail. Reserve deliberate time for it.

---

## Before the Session

### 1. Send a Pre-Session Brief (Google Docs)
Send the client a 1-page Google Doc 48 hours before the session. It should contain:
- The **objective** of the session in plain language ("By the end of this meeting, we will have a clear picture of the problem you're solving, who you're solving it for, and the core process the system needs to support")
- **3–5 things to think about** before arriving (not questions — prompts like "Think of a day in the life of the person who will use this product")
- A note that the session will be recorded for accuracy

> **Why this works:** It primes the client to think before arriving rather than cold-starting in the room. The session moves faster and answers are more considered.

### 2. Set Up Your Miro Board
Create a dedicated board for the client. Structure it as a left-to-right journey matching the checklist:

```
[Section 1: Context] → [Section 2: Users] → [Section 3: Core Loop] → [Section 4: Modules] → [Section 5: Data] → [Parking Lot]
```

**Pre-populate each section with:**
- A frame with the section title and a 1-line purpose description
- Empty sticky note clusters ready to fill
- A "🚩 Flag" sticky color (use red) for issues to revisit
- A "❓ Open" sticky color (use yellow) for unanswered questions

**Templates to have ready in Miro:**
- A blank **Core Business Loop** flow template (trigger → steps → outcome boxes connected by arrows)
- A blank **Actor/Role** table (role name, actions, what they see)
- A blank **Module List** with priority columns (Must / Should / Could)
- A **Parking Lot** frame at the far right for anything off-topic but worth keeping

### 3. Start the Google Meet Recording
Enable transcription in Google Meet. Do this at the start of every session without exception. Tell the client: *"I'm going to record this for accuracy so we don't miss anything — the recording is only for our internal reference."*

The transcript is your safety net. The Miro board is your working document.

---

## Running the Session

### Opening (5 minutes)
Start with this exact framing — it sets the tone for the whole session:

> *"Today we're not going to talk about features or screens. We're going to focus on three things: the problem you're solving, who you're solving it for, and how the solution will actually work in practice. Everything else we figure out from that."*

Then share your screen and show the Miro board structure. This tells the client there's a plan — it builds confidence and reduces tangents.

---

### Facilitation Technique: The 5-Layer Drill
Use this when a client gives a surface-level answer. Works on almost any question.

1. **State** — Ask the question directly and get their initial answer
2. **Reflect** — Repeat their answer back in your own words: *"So what I'm hearing is..."*
3. **Probe** — Ask "what does that mean in practice?" or "can you give me an example?"
4. **Challenge** — Introduce a scenario that tests the answer: *"What happens if...?"*
5. **Capture** — Write the refined answer on a sticky note, read it back, get confirmation

> **Example:**
> Client: *"We need a dashboard for our managers."*
> You: *"So managers need visibility over something — what specifically are they looking at today that isn't working?"*
> Client: *"They have to ask the team for updates manually every morning."*
> You: *"And what information do they need? Is it status, numbers, exceptions, all of the above?"*
> Now you have something to build with.

---

### Facilitation Technique: The Core Loop Sketch
Do this live in Miro after the Business Context section. Don't wait until you "have enough information."

1. Open the Core Loop template
2. Say: *"Let me try to draw what I'm hearing — tell me where I'm wrong"*
3. Place a box for the trigger: *"A [user type] wants to [do something]"*
4. Add 3–4 intermediate steps based on what you've heard
5. Place an outcome box: *"And the result is [outcome]"*
6. Ask: *"Is this roughly it?"*

The client will almost always correct you — and those corrections are your most valuable data. Wrong diagrams produce the right answers faster than open questions.

---

### Facilitation Technique: The Actor Walk-Through
Use this after you've identified the main roles. For each actor, run them through the same script:

> *"Walk me through a typical day for [role]. They arrive at work (or open the app). What do they do first? What does the system need to show them? What action do they take? What happens next?"*

Capture each step as a sticky note on the Miro board. By the time you've done this for 3 roles you'll have a rough map of the entire system from multiple perspectives.

---

### Facilitation Technique: The Newspaper Test
Use this to pressure-test whether the client has thought through the user experience.

> *"Imagine a journalist is writing about your product — what's the headline? What's the one sentence that explains what it does and why people use it?"*

If the client can answer this cleanly, they have a coherent product vision. If they can't, probe deeper before moving on. A product that can't be explained in one sentence hasn't been fully envisioned yet.

---

### Facilitation Technique: Dot Voting for Prioritization
When you have a list of modules or processes on the Miro board and need to prioritize:

1. Give the client 5 virtual dots (Miro's voting feature: **Play > Voting Session**)
2. Ask them to place their dots on the things they consider most critical for launch
3. Run a second round with 3 dots for "what would you cut if budget was tight"
4. The result gives you a clear Must / Should / Could split without a debate

> **Important:** Run the voting *after* all the sticky notes are on the board, not while you're still capturing. Premature prioritization shuts down options.

---

### Handling the Three Most Common Client Patterns

#### Pattern 1: The Feature Shower
*The client leads with a list of features instead of a problem.*

**What it sounds like:** *"We need a chatbot, a mobile app, QR codes, real-time tracking, and a loyalty program."*

**What to do:** Don't engage with the feature list yet. Park it explicitly:
> *"Those are great ideas — let's put them on the board and come back to them. Before we do, I want to understand what problem each of those is solving. Can you walk me through what's happening today that makes those feel necessary?"*

Use the Parking Lot in Miro to hold all feature requests. Review them at the end of the session and map each to a process or user need. Features without a process or a user need get flagged.

---

#### Pattern 2: The Underprepared Operator
*The client has a clear consumer product vision but hasn't thought through how it will be operated.*

**What it sounds like:** *"The user clicks a button and it just happens."*

**What to do:** Ask the operational question directly:
> *"When the user clicks that button — who on your side gets notified? What do they do? How long does it take? What happens if they're not available?"*

If the client doesn't have answers, make the gap explicit on the Miro board with a red flag:
> *"I'm going to flag this because the user experience depends on this operational step working reliably. We'll need to design this process before we can finalize the screens."*

---

#### Pattern 3: The Scope Expander
*Every answer reveals three new requirements. The scope keeps growing.*

**What it sounds like:** *"...and also, we'd need to handle X. Oh, and there's also the case where Y. Actually, now that I think about it, Z would be really important too."*

**What to do:** Don't shut it down — capture everything in the Parking Lot. Then at the natural break:
> *"We've captured a lot of great ideas. Let's do a quick round of prioritization so we can separate what needs to be in the first version versus what we plan for later."*

Run a dot vote. The Parking Lot becomes the v2 backlog.

---

## Section-Specific Facilitation Tips

### Business Context & Vision
- Start with *"Tell me about the problem"* not *"Tell me about the product"*
- If they jump to the product, redirect: *"Before we talk about the solution, help me understand the pain"*
- Use the **5-Layer Drill** on the first answer — it almost always reveals a richer problem

### Core Business Loop
- Draw it in Miro immediately, even if rough
- The loop should fit on a single sticky-note chain — if it takes more than 6 steps, you haven't found the core yet
- Ask: *"What is the ONE thing this system cannot fail to do?"*

### End-User Profile
- Ask for a real person, not a persona: *"Think of a specific customer you already have — describe them"*
- If they say *"anyone could use this"*, push back gently: *"Who would you most want to use it first?"*
- The Jobs-to-be-Done frame is powerful here: *"When someone uses this product, what job are they hiring it to do?"*

### Operational Process
- Use the Actor Walk-Through technique here
- For greenfield projects specifically, ask: *"If you had to run this manually tomorrow with a team of 3 people and no software — what would each person be doing?"*
- This question reveals the actual process the software needs to support, without the client needing to think in technical terms

### Data & Integrations
- Don't ask *"what integrations do you need"* — clients don't think in integrations
- Ask instead: *"What systems do your team use today? What information lives there that this product would need?"*
- Then: *"What information will this product generate that other systems would need?"*

### Assumptions & Risks (Greenfield only)
- The Assumption Log is best filled collaboratively in Miro
- For each assumption, ask: *"How confident are you in this, on a scale of 1–10?"*
- Anything below 7 gets a red flag and a "how would we validate this?" note

---

## Closing the Session (15 minutes)

Reserve the last 15 minutes for three things:

**1. Board Review**
Walk the client through the Miro board from left to right. For each section: *"Does this accurately capture what we discussed?"* Correct anything on the spot.

**2. Open Questions Review**
Read out every yellow sticky (open question). For each one:
- Can it be answered now?
- Who is responsible for answering it?
- Does it need to be answered before the next session?

**3. Summary & Next Step**
Fill the Discovery Summary block live on the screen. Read it back to the client. Then confirm:
> *"Based on today's session, the next step is [X]. We'll send you a copy of this board and a written summary within 24 hours."*

---

## After the Session

### Within 24 Hours

1. **Export the Miro board** as a PDF snapshot (File > Export > PDF) and attach it to the project folder in Google Drive
2. **Run the Google Meet transcript** through your summarization workflow to extract:
   - Key decisions made
   - Open questions and owners
   - Any commitments made by either side
3. **Fill the Discovery Checklist** document in Google Docs using the Miro board and transcript as sources — this is the artifact that feeds the Proposal Agent
4. **Send the client** a Google Doc summary with:
   - The filled Discovery Summary block
   - The open question list with owners and due dates
   - The confirmed next step

### Miro Board Hygiene
After the session, before sharing:
- Convert rough sticky notes into clean text
- Group related stickies into labeled clusters
- Move all Parking Lot items into a dedicated section with a "v2 / TBD" tag
- Add the Core Loop as a clean diagram (not just stickies)

---

## Quick Reference Card

| Situation | Technique |
|-----------|-----------|
| Client gives vague answers | 5-Layer Drill |
| Client jumps to features | Park it, redirect to problem |
| Need to map any process | Actor Walk-Through |
| Client hasn't thought through operations | "If you ran this manually..." |
| Too many modules, can't prioritize | Dot Voting |
| Client can't explain the product simply | Newspaper Test |
| Something is undefined and risky | Red flag sticky + owner + due date |
| Session is going off-track | "Let me capture that in the Parking Lot and bring us back to [section]" |

---

## Miro Board Setup Checklist

- [ ] Board created and named: `[Client Name] — Discovery — [Date]`
- [ ] Frames created for each checklist section
- [ ] Core Loop template placed and ready
- [ ] Actor/Role table placed and ready
- [ ] Module List with priority columns placed and ready
- [ ] Parking Lot frame at far right
- [ ] Sticky color convention set: 🟡 Open question / 🔴 Flag / 🟢 Confirmed / 🔵 General
- [ ] Voting session configured (Play > Voting)
- [ ] Board shared with client (View only during session, edit after)

## Google Suite Checklist

- [ ] Google Meet recording enabled
- [ ] Transcription enabled in Meet settings
- [ ] Pre-session brief sent 48h before (Google Docs)
- [ ] Google Drive folder created for client with subfolders: `/Discovery`, `/Proposals`, `/Briefs`
- [ ] Post-session summary template ready to fill (Google Docs)
