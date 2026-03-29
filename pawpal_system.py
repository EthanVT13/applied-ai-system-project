from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int        # 1 (low) to 5 (high)
    category: str        # e.g., "walk", "feeding", "meds"
    description: str = ""
    completed: bool = False
    preferred_time: str = ""        # "HH:MM" format, e.g. "08:00"
    recurrence: str = ""            # "", "daily", or "weekly"
    due_date: Optional[date] = None
    pet: Optional[Pet] = field(default=None, repr=False)

    def is_high_priority(self) -> bool:
        """Return True if the task priority is 4 or above."""
        return self.priority >= 4

    def mark_complete(self) -> None:
        """Mark this task complete and auto-schedule the next occurrence if recurring."""
        self.completed = True
        if self.recurrence and self.pet:
            base = self.due_date or date.today()
            if self.recurrence == "daily":
                next_due = base + timedelta(days=1)
            elif self.recurrence == "weekly":
                next_due = base + timedelta(weeks=1)
            else:
                return
            self.pet.add_task(Task(
                name=self.name,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                description=self.description,
                preferred_time=self.preferred_time,
                recurrence=self.recurrence,
                due_date=next_due,
            ))


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: List[Task] = field(default_factory=list)

    def get_info(self) -> str:
        """Return a formatted string with the pet's basic details and any special needs."""
        info = f"{self.name} ({self.species}, age {self.age})"
        if self.special_needs:
            info += f" — Special needs: {self.special_needs}"
        return info

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and set the task's pet reference."""
        task.pet = self
        self.tasks.append(task)


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: str = ""):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_available_time(self) -> int:
        """Return the owner's total available minutes for the day."""
        return self.available_minutes

    def get_all_tasks(self) -> List[Task]:
        """Return a flat list of all tasks across every pet the owner has."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def add_task(self, task: Task, pet: Pet) -> None:
        """Assign a task to the given pet and register it in that pet's task list."""
        pet.add_task(task)

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by preferred_time in HH:MM format; tasks with no time go last."""
        return sorted(
            tasks,
            key=lambda t: t.preferred_time if t.preferred_time else "99:99"
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Return tasks filtered by pet name and/or completion status."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet and t.pet.name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def generate_schedule(self, pet_name: Optional[str] = None) -> List[Task]:
        """Return a priority-sorted list of pending tasks that fit within the owner's available time."""
        pending = self.filter_tasks(pet_name=pet_name, completed=False)
        # Primary sort: priority descending; secondary sort: preferred_time ascending
        sorted_tasks = sorted(
            pending,
            key=lambda t: (-t.priority, t.preferred_time if t.preferred_time else "99:99")
        )

        schedule = []
        time_used = 0
        available = self.owner.get_available_time()

        for task in sorted_tasks:
            if time_used + task.duration_minutes <= available:
                schedule.append(task)
                time_used += task.duration_minutes

        return schedule

    def detect_conflicts(self) -> List[str]:
        """Return a list of warning messages for tasks whose time windows overlap on the same pet."""
        warnings = []
        for pet in self.owner.pets:
            timed = [t for t in pet.tasks if t.preferred_time and not t.completed]
            for i, a in enumerate(timed):
                for b in timed[i + 1:]:
                    a_start = int(a.preferred_time[:2]) * 60 + int(a.preferred_time[3:])
                    b_start = int(b.preferred_time[:2]) * 60 + int(b.preferred_time[3:])
                    a_end = a_start + a.duration_minutes
                    b_end = b_start + b.duration_minutes
                    if a_start < b_end and b_start < a_end:
                        warnings.append(
                            f"CONFLICT [{pet.name}]: '{a.name}' ({a.preferred_time}, "
                            f"{a.duration_minutes} min) overlaps '{b.name}' "
                            f"({b.preferred_time}, {b.duration_minutes} min)"
                        )
        return warnings

    def explain_plan(self, pet_name: Optional[str] = None) -> str:
        """Generate a human-readable summary of today's schedule for the owner."""
        schedule = self.generate_schedule(pet_name=pet_name)

        if not schedule:
            return f"{self.owner.name} has no tasks scheduled for today."

        total_minutes = sum(t.duration_minutes for t in schedule)
        lines = [
            f"Daily schedule for {self.owner.name}",
            f"Time used: {total_minutes} min of {self.owner.get_available_time()} available",
            "",
        ]

        for i, task in enumerate(schedule, 1):
            pet_name_label = task.pet.name if task.pet else "Unknown"
            priority_label = "HIGH" if task.is_high_priority() else "normal"
            time_label = f" @ {task.preferred_time}" if task.preferred_time else ""
            lines.append(
                f"  {i}. [{priority_label}] {task.name} for {pet_name_label}"
                f"{time_label} — {task.duration_minutes} min ({task.category})"
            )
            if task.description:
                lines.append(f"     {task.description}")

        remaining = self.owner.get_available_time() - total_minutes
        lines.append(f"\n  {remaining} min remaining after scheduled tasks.")

        if self.owner.preferences:
            lines.append(f"  Preference note: {self.owner.preferences}")

        return "\n".join(lines)
