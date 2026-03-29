from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(minutes=120):
    return Owner(name="Alex", available_minutes=minutes)


def make_pet(name="Buddy"):
    return Pet(name=name, species="Dog", age=3)


def make_task(name="Walk", duration=20, priority=3, category="walk",
              preferred_time="", recurrence="", due_date=None):
    return Task(
        name=name,
        duration_minutes=duration,
        priority=priority,
        category=category,
        preferred_time=preferred_time,
        recurrence=recurrence,
        due_date=due_date,
    )


# ---------------------------------------------------------------------------
# Original tests (Phase 2)
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    pet.add_task(make_task("Afternoon", preferred_time="14:00"))
    pet.add_task(make_task("Morning",   preferred_time="08:00"))
    pet.add_task(make_task("Evening",   preferred_time="18:30"))

    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    times = [t.preferred_time for t in sorted_tasks]
    assert times == ["08:00", "14:00", "18:30"]


def test_sort_by_time_untimed_tasks_go_last():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    pet.add_task(make_task("No time"))
    pet.add_task(make_task("Early", preferred_time="07:00"))

    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    assert sorted_tasks[0].preferred_time == "07:00"
    assert sorted_tasks[-1].preferred_time == ""


def test_generate_schedule_priority_order():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    pet.add_task(make_task("Low",  priority=1))
    pet.add_task(make_task("High", priority=5))
    pet.add_task(make_task("Med",  priority=3))

    schedule = scheduler.generate_schedule()
    priorities = [t.priority for t in schedule]
    assert priorities == sorted(priorities, reverse=True)


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_recurrence_spawns_next_day():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)

    today = date.today()
    task = make_task("Eye Drops", recurrence="daily", due_date=today)
    pet.add_task(task)

    assert len(pet.tasks) == 1
    task.mark_complete()
    assert len(pet.tasks) == 2

    next_task = pet.tasks[-1]
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_weekly_recurrence_spawns_next_week():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)

    today = date.today()
    task = make_task("Heartworm Pill", recurrence="weekly", due_date=today)
    pet.add_task(task)

    task.mark_complete()
    next_task = pet.tasks[-1]
    assert next_task.due_date == today + timedelta(weeks=1)


def test_non_recurring_task_does_not_spawn():
    pet = make_pet()
    task = make_task("One-off")
    pet.add_task(task)

    task.mark_complete()
    assert len(pet.tasks) == 1  # no new task added


def test_recurrence_inherits_task_properties():
    pet = make_pet()
    task = make_task("Meds", duration=10, priority=5, category="meds",
                     preferred_time="08:00", recurrence="daily", due_date=date.today())
    pet.add_task(task)
    task.mark_complete()

    next_task = pet.tasks[-1]
    assert next_task.name == "Meds"
    assert next_task.duration_minutes == 10
    assert next_task.priority == 5
    assert next_task.preferred_time == "08:00"
    assert next_task.recurrence == "daily"


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_overlapping_tasks():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    # Walk: 08:00-08:30, Vet: 08:15-08:45 → overlap
    pet.add_task(make_task("Morning Walk", duration=30, preferred_time="08:00"))
    pet.add_task(make_task("Vet Call",     duration=30, preferred_time="08:15"))

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "Morning Walk" in conflicts[0]
    assert "Vet Call" in conflicts[0]


def test_detect_conflicts_same_start_time():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    pet.add_task(make_task("Task A", duration=20, preferred_time="09:00"))
    pet.add_task(make_task("Task B", duration=15, preferred_time="09:00"))

    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1


def test_detect_conflicts_no_overlap():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    # Walk: 08:00-08:30, Breakfast: 08:30-08:40 → back-to-back, no overlap
    pet.add_task(make_task("Walk",      duration=30, preferred_time="08:00"))
    pet.add_task(make_task("Breakfast", duration=10, preferred_time="08:30"))

    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


def test_completed_tasks_excluded_from_conflict_check():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    t1 = make_task("Done Task", duration=30, preferred_time="08:00")
    t2 = make_task("New Task",  duration=30, preferred_time="08:00")
    pet.add_task(t1)
    pet.add_task(t2)
    t1.mark_complete()

    # Only t2 is pending — no pair to conflict with
    conflicts = scheduler.detect_conflicts()
    assert conflicts == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_pet_no_schedule():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    assert scheduler.generate_schedule() == []


def test_owner_no_pets_no_schedule():
    owner = make_owner()
    scheduler = Scheduler(owner)
    assert scheduler.generate_schedule() == []


def test_tasks_exceeding_budget_are_dropped():
    owner = make_owner(minutes=30)
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    pet.add_task(make_task("Big Task",   duration=25, priority=5))
    pet.add_task(make_task("Small Task", duration=10, priority=4))
    # Total = 35 min, budget = 30 — Small Task should be dropped

    schedule = scheduler.generate_schedule()
    names = [t.name for t in schedule]
    assert "Big Task" in names
    assert "Small Task" not in names


def test_filter_by_pet_name():
    owner = make_owner()
    buddy = make_pet("Buddy")
    luna = Pet(name="Luna", species="Cat", age=2)
    owner.add_pet(buddy)
    owner.add_pet(luna)
    scheduler = Scheduler(owner)

    buddy.add_task(make_task("Walk"))
    luna.add_task(make_task("Meds"))

    buddy_tasks = scheduler.filter_tasks(pet_name="Buddy")
    assert len(buddy_tasks) == 1
    assert buddy_tasks[0].name == "Walk"


def test_filter_completed_only():
    owner = make_owner()
    pet = make_pet()
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    t1 = make_task("Done")
    t2 = make_task("Pending")
    pet.add_task(t1)
    pet.add_task(t2)
    t1.mark_complete()

    completed = scheduler.filter_tasks(completed=True)
    assert len(completed) == 1
    assert completed[0].name == "Done"
