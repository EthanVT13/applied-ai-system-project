# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

PawPal+ goes beyond a simple task list with four algorithmic features:

**Time-aware sorting** — Tasks carry an optional `preferred_time` field in `HH:MM` format. `Scheduler.sort_by_time()` uses a lambda key to sort them chronologically, with untimed tasks pushed to the end. The main schedule uses priority as the primary sort and preferred time as a tiebreaker.

**Flexible filtering** — `Scheduler.filter_tasks(pet_name, completed)` lets you slice the task list by pet or completion status (or both). This powers per-pet schedule views and the "pending only" display in the UI.

**Recurring tasks** — `Task` accepts a `recurrence` field (`"daily"` or `"weekly"`). When `mark_complete()` is called on a recurring task, it automatically creates the next occurrence using Python's `timedelta` and appends it to the pet's task list — no manual re-entry needed.

**Conflict detection** — `Scheduler.detect_conflicts()` compares every pair of timed, pending tasks for each pet. If two tasks' time windows overlap (`start_a < end_b and start_b < end_a`), it returns a plain-language warning string instead of crashing, so the app can surface it to the user gracefully.

## Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

18 tests across 5 categories:

| Category | Tests | Description |
|---|---|---|
| **Sorting** | 3 | Tasks return in chronological HH:MM order; untimed tasks go last; schedule respects priority descending |
| **Recurrence** | 4 | Daily tasks spawn next occurrence with `due_date + 1 day`; weekly tasks use `+ 7 days`; non-recurring tasks don't spawn; new task inherits all properties |
| **Conflict detection** | 4 | Overlapping windows flagged; same start time flagged; back-to-back tasks are not flagged; completed tasks are excluded from checks |
| **Edge cases** | 4 | Empty pet returns no schedule; owner with no pets returns no schedule; tasks that exceed the time budget are dropped; filter by pet name returns correct subset |
| **Core behaviors** | 3 | `mark_complete()` sets status; `add_task()` increments count; `filter_tasks(completed=True)` returns only done tasks |

### Confidence level

★★★★☆ (4/5)

The core scheduling logic — priority sorting, time budgeting, recurrence, and conflict detection — is fully tested and all 18 tests pass. One star withheld because the Streamlit UI layer (`app.py`) and multi-pet conflict scenarios (tasks across different pets) are not yet covered by automated tests.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
