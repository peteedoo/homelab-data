# ADHD Planner MVP

A lightweight, single-file-style web app for ADHD-friendly daily planning. Built as a static site with no backend and no build step.

## Core ideas

- **Low friction capture**: a big, always-visible input so tasks don't get lost.
- **Energy-aware planning**: tag tasks by the energy level they require.
- **One-thing-at-a-time focus**: a "Focus" view that shows only the next best task.
- **Break things down**: split overwhelming tasks into small, checkable subtasks.
- **Calm UI**: soft colors, generous spacing, minimal distractions.
- **Private by default**: all data stays in the browser's `localStorage`.

## Files

- `index.html` — page shell
- `styles.css` — calm, accessible styling
- `app.js` — app logic and `localStorage` persistence

## Run locally

```bash
cd projects/adhd-planner
python3 -m http.server 8080
```

Then open <http://localhost:8080>.

## Features (MVP)

- Add tasks with title, priority, energy level, and optional duration.
- Mark tasks done; clear completed tasks.
- Add subtasks to break a task into smaller steps.
- **Focus view**: shows the single best next task based on priority and energy.
- **Energy filter**: see only tasks that match your current energy level.
- Progress bar and encouraging messages.
- Export/import your data as JSON for backup.
- Keyboard friendly (Tab/Enter/Esc).

## Tech stack

- HTML5
- CSS3 (custom properties, no framework)
- Vanilla ES6 modules
- Browser `localStorage`

## Future ideas (not in MVP)

- Recurring tasks
- Time-blocking / calendar view
- Drag-to-reorder
- Pomodoro timer integration
- Cloud sync
