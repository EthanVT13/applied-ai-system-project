from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

alex = Owner(name="Alex", available_minutes=120, preferences="morning walks")

buddy = Pet(name="Buddy", species="Dog", age=3)
luna = Pet(name="Luna", species="Cat", age=5, special_needs="daily eye drops")

alex.add_pet(buddy)
alex.add_pet(luna)

# Tasks added OUT OF ORDER intentionally to test sorting
buddy.add_task(Task(
    name="Evening Walk",
    duration_minutes=25,
    priority=3,
    category="walk",
    preferred_time="18:00",
    description="Around the park after dinner"
))
buddy.add_task(Task(
    name="Breakfast",
    duration_minutes=10,
    priority=4,
    category="feeding",
    preferred_time="07:30",
    description="1 cup dry kibble"
))
buddy.add_task(Task(
    name="Morning Walk",
    duration_minutes=30,
    priority=5,
    category="walk",
    preferred_time="08:00",
    description="30-minute walk around the block"
))

luna.add_task(Task(
    name="Playtime",
    duration_minutes=20,
    priority=2,
    category="play",
    preferred_time="15:00",
    description="Feather wand or laser pointer"
))

# Recurring tasks
buddy.add_task(Task(
    name="Heartworm Pill",
    duration_minutes=5,
    priority=5,
    category="meds",
    preferred_time="09:00",
    recurrence="weekly",
    due_date=date.today(),
    description="Give with food"
))
luna.add_task(Task(
    name="Eye Drops",
    duration_minutes=5,
    priority=5,
    category="meds",
    preferred_time="08:30",
    recurrence="daily",
    due_date=date.today(),
    description="2 drops in each eye"
))

# Conflicting tasks: both start at 08:00, Buddy is only free for 30 min
# Morning Walk runs 08:00-08:30, Vet Check runs 08:15-08:45 → overlap
buddy.add_task(Task(
    name="Vet Check Call",
    duration_minutes=30,
    priority=4,
    category="other",
    preferred_time="08:15",
    description="Call vet to confirm appointment"
))

# Mark one task complete to test filtering
buddy.tasks[0].mark_complete()  # Evening Walk is done

scheduler = Scheduler(owner=alex)

SEP = "=" * 50

# --- Full schedule (priority + time sort) ---
print(SEP)
print("       PAWPAL+ — TODAY'S SCHEDULE")
print(SEP)
print(scheduler.explain_plan())

# --- Sorted by time only (ignores priority) ---
print(SEP)
print("  ALL TASKS SORTED BY TIME (HH:MM)")
print(SEP)
all_tasks = scheduler.owner.get_all_tasks()
for t in scheduler.sort_by_time(all_tasks):
    time_label = t.preferred_time if t.preferred_time else "no time"
    pet_name = t.pet.name if t.pet else "?"
    print(f"  {time_label}  {t.name} ({pet_name})")

# --- Filter: Buddy's tasks only ---
print(SEP)
print("  BUDDY'S TASKS ONLY")
print(SEP)
for t in scheduler.filter_tasks(pet_name="Buddy"):
    status = "done" if t.completed else "pending"
    print(f"  [{status}] {t.name} — {t.duration_minutes} min")

# --- Filter: pending tasks only ---
print(SEP)
print("  PENDING TASKS (not yet completed)")
print(SEP)
for t in scheduler.filter_tasks(completed=False):
    pet_name = t.pet.name if t.pet else "?"
    print(f"  {t.name} ({pet_name}) @ {t.preferred_time or 'no time'}")

# --- Conflict detection ---
print(SEP)
print("  CONFLICT DETECTION")
print(SEP)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  ⚠  {warning}")
else:
    print("  No conflicts detected.")

# --- Recurring task demo ---
print(SEP)
print("  RECURRING TASK DEMO")
print(SEP)
eye_drops = next(t for t in luna.tasks if t.name == "Eye Drops" and t.recurrence == "daily")
print(f"Before: Luna has {len(luna.tasks)} task(s)")
print(f"  Marking '{eye_drops.name}' complete (recurrence: {eye_drops.recurrence})")
eye_drops.mark_complete()
print(f"After:  Luna has {len(luna.tasks)} task(s)")
new_task = luna.tasks[-1]
print(f"  Next occurrence: '{new_task.name}' due {new_task.due_date}")

heartworm = next(t for t in buddy.tasks if t.name == "Heartworm Pill")
print(f"\nBefore: Buddy has {len(buddy.tasks)} task(s)")
print(f"  Marking '{heartworm.name}' complete (recurrence: {heartworm.recurrence})")
heartworm.mark_complete()
print(f"After:  Buddy has {len(buddy.tasks)} task(s)")
new_hw = buddy.tasks[-1]
print(f"  Next occurrence: '{new_hw.name}' due {new_hw.due_date}")
print(SEP)
