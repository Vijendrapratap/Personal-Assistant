# Alfred Implementation Roadmap
## From Current State to Production-Ready PA

---

## Overview

This roadmap transforms Alfred from its current 60-65% complete state into a minimal, goal-oriented personal assistant inspired by Manus.ai's transparency, Motion's intelligence, and Sunsama's clean design.

### Guiding Principles

1. **Ship Fast, Iterate** - Get core experience working before polish
2. **Conversation First** - Every feature accessible via natural language
3. **Proactive > Reactive** - Alfred initiates, not just responds
4. **Minimal UI** - Remove friction, reduce cognitive load

---

## Phase 0: Foundation Cleanup
**Goal:** Stabilize existing code, prepare for redesign

### Tasks

- [ ] **0.1 Audit existing mobile screens**
  - Document what works, what to keep
  - Identify reusable components
  - Map current navigation to new structure

- [ ] **0.2 Set up new design tokens**
  - Create `theme/tokens.ts` with color/spacing/typography
  - Configure dark mode as default
  - Set up Manrope font

- [ ] **0.3 Install missing dependencies**
  - `react-native-reanimated` (animations)
  - `expo-av` (voice recording)
  - `zustand` (state management)
  - `expo-haptics` (feedback)

- [ ] **0.4 Backend health check**
  - Verify all existing endpoints work
  - Add missing `/dashboard/today` batch endpoint
  - Add `/proactive/cards` endpoint

### Deliverables
- Clean codebase ready for new UI
- Design tokens configured
- All dependencies installed

---

## Phase 1: Core Experience
**Goal:** Rebuild the 4 main screens with minimal, conversation-first design

### 1.1 Today Screen (Home)

**Priority: P0 - This is the heart of Alfred**

```
Components needed:
├── GreetingHeader (time-aware greeting + quick status)
├── FocusCard (THE most important thing)
├── ProactiveCardList (Alfred's suggestions)
├── UpcomingTimeline (next 3-4 hours)
├── HabitStatusRow (compact habit chips)
└── ConversationInput (universal input)
```

- [ ] **1.1.1 Create GreetingHeader component**
  - Personalized greeting based on time
  - One-line status summary
  - Alfred avatar with state

- [ ] **1.1.2 Create FocusCard component**
  - Highlights single priority
  - Context from past conversations
  - Quick actions (Start, Snooze, Done)

- [ ] **1.1.3 Create ProactiveCard component**
  - Support types: warning, insight, reminder, celebration
  - Dismissible/snoozable
  - Action buttons

- [ ] **1.1.4 Build Today screen**
  - Integrate all components
  - Pull-to-refresh
  - Connect to `/dashboard/today` endpoint

- [ ] **1.1.5 Implement Morning Briefing API**
  - Enhance existing `/dashboard/briefing/morning`
  - Add proactive cards to response
  - Include context for focus item

### 1.2 Do Screen (Tasks + Habits)

**Priority: P0**

```
Components needed:
├── ConversationInput (at top, not bottom)
├── ActiveTaskCard (what's in progress)
├── TaskList (grouped by status/due)
├── HabitChipRow (compact horizontal list)
└── ProjectQuickAccess (horizontal scroll)
```

- [ ] **1.2.1 Create TaskCard component**
  - Swipe actions (complete, start, snooze)
  - Priority color indicator
  - Project badge
  - Due time/date

- [ ] **1.2.2 Create HabitChip component**
  - Compact circular design
  - Streak badge (🔥 number)
  - Tap to log
  - Category emoji

- [ ] **1.2.3 Build Do screen**
  - Unified tasks + habits view
  - Filter by status (tabs)
  - Conversational task creation

- [ ] **1.2.4 Implement task quick-add via conversation**
  - Parse natural language input
  - Extract due date, priority, project
  - Show confirmation before creating

### 1.3 Focus Screen (Calendar + Voice)

**Priority: P0**

```
Components needed:
├── DayStrip (horizontal date selector)
├── TimelineView (vertical calendar)
├── EventCard (meeting/event display)
├── NowIndicator (current time line)
└── ConversationInput (schedule via voice)
```

- [ ] **1.3.1 Create DayStrip component**
  - Horizontal scroll through week
  - Active day highlighted
  - Event indicator dots

- [ ] **1.3.2 Create EventCard component**
  - Color-coded by category
  - Key info (time, location, attendees)
  - Pre-meeting context (from Alfred)

- [ ] **1.3.3 Create TimelineView component**
  - Hour grid with events
  - Now indicator with time
  - Tap to add event

- [ ] **1.3.4 Build Focus screen**
  - Calendar-first view
  - Voice input for scheduling
  - Protected focus time display

### 1.4 You Screen (Profile + Memory)

**Priority: P1**

```
Components needed:
├── ProfileHeader (avatar, name, email)
├── KnowledgeStats (what Alfred knows)
├── SettingsList (preferences)
└── DataControls (export, delete)
```

- [ ] **1.4.1 Create KnowledgeStats section**
  - Count of people, companies, projects
  - "Alfred knows X facts about you"
  - Tap to browse entities

- [ ] **1.4.2 Build You screen**
  - Profile display
  - Knowledge overview
  - Settings navigation

- [ ] **1.4.3 Build Settings screens**
  - Notifications preferences
  - Voice & language
  - Integrations (placeholder)
  - Privacy & data

### 1.5 Navigation & Tab Bar

- [ ] **1.5.1 Create custom tab bar**
  - 4 tabs: Today, Do, Focus, You
  - Center floating Alfred button
  - Active state indicators

- [ ] **1.5.2 Configure Expo Router**
  - Set up (tabs) layout
  - Configure deep linking
  - Add modal routes

### Phase 1 Deliverables
- 4 fully functional screens
- Unified design language
- Conversation input everywhere
- Basic proactive cards

---

## Phase 2: Voice & Transparency
**Goal:** Add voice interaction and show Alfred's thinking

### 2.1 Voice Interface

- [ ] **2.1.1 Create VoiceModal screen**
  - Full-screen modal design
  - Alfred avatar with listening state
  - Waveform visualization
  - Conversation history

- [ ] **2.1.2 Implement voice recording**
  - Use expo-av for recording
  - Handle permissions
  - Audio format optimization

- [ ] **2.1.3 Create voice API endpoints**
  - `POST /voice/transcribe` (Whisper)
  - `POST /voice/chat` (transcribe + respond)
  - Return thinking steps

- [ ] **2.1.4 Integrate voice throughout app**
  - Voice button in ConversationInput
  - Long-press Alfred FAB opens voice
  - Quick action chips in voice UI

### 2.2 Transparency Panel

- [ ] **2.2.1 Create TransparencyPanel component**
  - Shows step-by-step thinking
  - Animated step transitions
  - Expandable details

- [ ] **2.2.2 Implement streaming response API**
  - `POST /chat/stream` (SSE)
  - Stream thinking steps in real-time
  - Final response with actions taken

- [ ] **2.2.3 Integrate transparency in voice modal**
  - Show steps as Alfred thinks
  - Collapse when done
  - Reference in response

### Phase 2 Deliverables
- Voice input/output working
- Transparency panel showing Alfred's reasoning
- Users can see what Alfred is doing

---

## Phase 3: Proactive Intelligence
**Goal:** Alfred initiates conversations and suggestions

### 3.1 Proactive Engine

- [ ] **3.1.1 Implement stale project detection**
  - Query projects with no updates in X days
  - Generate warning cards
  - Allow snooze/dismiss

- [ ] **3.1.2 Implement streak risk detection**
  - Check habits not logged today
  - Time-based reminders
  - Celebration for milestones

- [ ] **3.1.3 Implement meeting prep**
  - Pre-meeting context gathering
  - Related notes/history
  - Suggested prep items

- [ ] **3.1.4 Create card management API**
  - `GET /proactive/cards`
  - `POST /proactive/dismiss`
  - `POST /proactive/snooze`

### 3.2 Background Workers

- [ ] **3.2.1 Set up APScheduler**
  - Configure scheduler in FastAPI
  - Add persistence for reliability

- [ ] **3.2.2 Implement morning briefing job**
  - Per-user scheduling based on preferences
  - Push notification trigger
  - Briefing cache (5 min TTL)

- [ ] **3.2.3 Implement evening review job**
  - Trigger review prompt at user's time
  - Generate daily summary
  - Push notification

- [ ] **3.2.4 Implement habit reminder job**
  - Per-habit time checking
  - Streak-aware messaging
  - Respect quiet hours

### 3.3 Evening Review Flow

- [ ] **3.3.1 Create EveningReview modal**
  - Show accomplishments
  - Show incomplete items
  - Input for blockers
  - Tomorrow planning
  - Mood check

- [ ] **3.3.2 Implement evening review API**
  - `GET /dashboard/briefing/evening`
  - `POST /dashboard/review` (save responses)
  - Learn from reflections

### Phase 3 Deliverables
- Proactive cards appearing in Today screen
- Push notifications for briefings/reviews
- Evening review flow working
- Alfred feels alive and attentive

---

## Phase 4: Knowledge & Memory
**Goal:** Alfred remembers everything and shows what it knows

### 4.1 Entity Management

- [ ] **4.1.1 Create entity extraction from conversations**
  - Detect people, companies, projects
  - Auto-create entities
  - Link to existing entities

- [ ] **4.1.2 Implement entity browser screens**
  - People list with relationship context
  - Company list with project links
  - Search functionality

- [ ] **4.1.3 Create entity detail view**
  - Timeline of interactions
  - Related entities
  - Key facts known

### 4.2 Knowledge Graph Integration

- [ ] **4.2.1 Wire up Neo4j to API**
  - Create entity relationships
  - Query related context
  - Power "Alfred knows" stats

- [ ] **4.2.2 Enhance chat with knowledge context**
  - Include relevant entity info
  - Reference past conversations
  - Build relationship context

### 4.3 Preference Learning

- [ ] **4.3.1 Implement preference extraction**
  - Detect stated preferences in chat
  - Store with confidence scores
  - Apply to future responses

- [ ] **4.3.2 Create preferences view**
  - Show learned preferences
  - Allow corrections
  - Confidence indicators

### Phase 4 Deliverables
- Entity browser working
- Knowledge graph powering context
- Preference learning active
- "Alfred knows X facts" is meaningful

---

## Phase 5: Polish & Optimization
**Goal:** Make it feel premium and performant

### 5.1 Animations & Microinteractions

- [ ] **5.1.1 Add Alfred avatar animations**
  - Idle: subtle breathing
  - Listening: pulsing glow
  - Thinking: orbiting dots
  - Speaking: waveform

- [ ] **5.1.2 Add screen transitions**
  - Smooth tab transitions
  - Modal slide-up animations
  - Card press feedback

- [ ] **5.1.3 Add haptic feedback**
  - Task completion
  - Habit logging
  - Button presses

### 5.2 Performance

- [ ] **5.2.1 Implement optimistic updates**
  - Task completion instant
  - Habit logging instant
  - Rollback on error

- [ ] **5.2.2 Add skeleton screens**
  - Today screen skeleton
  - Task list skeleton
  - Calendar skeleton

- [ ] **5.2.3 Optimize API calls**
  - Batch endpoints
  - Response caching
  - Prefetching

### 5.3 Offline Support

- [ ] **5.3.1 Implement local caching**
  - Cache today's briefing
  - Cache task list
  - Cache habits

- [ ] **5.3.2 Implement offline queue**
  - Queue actions when offline
  - Sync when connected
  - Conflict resolution

### Phase 5 Deliverables
- Smooth, delightful animations
- Fast, responsive UI
- Works offline

---

## Phase 6: Integrations (Future)
**Goal:** Connect to user's tools

### Planned Integrations

- [ ] Google Calendar sync
- [ ] Google/Outlook email awareness
- [ ] Slack status sync
- [ ] GitHub activity tracking
- [ ] Notion/Obsidian notes

---

## Sprint Planning Suggestion

### Sprint 1 (2 weeks)
- Phase 0 complete
- Today screen 80% done
- Do screen 50% done

### Sprint 2 (2 weeks)
- Today screen complete
- Do screen complete
- Focus screen 80% done

### Sprint 3 (2 weeks)
- Focus screen complete
- You screen complete
- Navigation polished

### Sprint 4 (2 weeks)
- Voice interface basic
- Transparency panel
- Core proactive cards

### Sprint 5 (2 weeks)
- Background workers
- Push notifications
- Evening review

### Sprint 6 (2 weeks)
- Entity management
- Knowledge integration
- Preference learning

### Sprint 7 (2 weeks)
- Animations
- Performance optimization
- Polish pass

---

## Success Metrics

### User Experience
| Metric | Target |
|--------|--------|
| Daily Active Usage | >70% |
| Morning Briefing Opens | >80% |
| Voice Usage | >30% of interactions |
| Task Creation Time | <10 seconds |

### Technical
| Metric | Target |
|--------|--------|
| App Launch Time | <2 seconds |
| API Response Time | <500ms |
| Crash Rate | <0.1% |
| Offline Reliability | 95% |

### Product
| Metric | Target |
|--------|--------|
| Proactive Card Engagement | >50% |
| Evening Review Completion | >60% |
| Streak Maintenance | >70% |
| User Satisfaction (NPS) | >50 |

---

## Dependencies & Risks

### Technical Risks
1. **Whisper API costs** - Monitor usage, consider local fallback
2. **Push notification reliability** - Test extensively on iOS/Android
3. **Neo4j complexity** - Start simple, scale gradually
4. **Streaming on mobile** - SSE can be tricky, have fallback

### Resource Risks
1. **Solo development** - Scope creep is the enemy
2. **Design iteration** - Get user feedback early
3. **Backend complexity** - Keep it simple initially

### Mitigation
- Build incrementally, ship often
- Get real users testing early
- Have fallbacks for complex features
- Prioritize ruthlessly

---

## Getting Started

1. Read `ALFRED_UI_DESIGN.md` for design system
2. Read `ALFRED_ARCHITECTURE.md` for technical details
3. Start with Phase 0 tasks
4. Ship Phase 1 to test users ASAP

---

*Document Version: 1.0*
*Last Updated: January 2025*
