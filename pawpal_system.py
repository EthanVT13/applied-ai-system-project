from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int        # 1 (low) to 5 (high)
    category: str        # e.g., "walk", "feeding", "meds"
    description: str = ""
    completed: bool = False
    pet: Optional[Pet] = field(default=None, repr=False)

    def is_high_priority(self) -> bool:
        """Return True if the task priority is 4 or above."""
        return self.priority >= 4

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


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

    def generate_schedule(self) -> List[Task]:
        """Return a priority-sorted list of tasks that fit within the owner's available time."""
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        sorted_tasks = sorted(pending, key=lambda t: t.priority, reverse=True)

        schedule = []
        time_used = 0
        available = self.owner.get_available_time()

        for task in sorted_tasks:
            if time_used + task.duration_minutes <= available:
                schedule.append(task)
                time_used += task.duration_minutes

        return schedule

    def explain_plan(self) -> str:
        """Generate a human-readable summary of today's schedule for the owner."""
        schedule = self.generate_schedule()

        if not schedule:
            return f"{self.owner.name} has no tasks scheduled for today."

        total_minutes = sum(t.duration_minutes for t in schedule)
        lines = [
            f"Daily schedule for {self.owner.name}",
            f"Time used: {total_minutes} min of {self.owner.get_available_time()} available",
            "",
        ]

        for i, task in enumerate(schedule, 1):
            pet_name = task.pet.name if task.pet else "Unknown"
            priority_label = "HIGH" if task.is_high_priority() else "normal"
            lines.append(
                f"  {i}. [{priority_label}] {task.name} for {pet_name}"
                f" — {task.duration_minutes} min ({task.category})"
            )
            if task.description:
                lines.append(f"     {task.description}")

        remaining = self.owner.get_available_time() - total_minutes
        lines.append(f"\n  {remaining} min remaining after scheduled tasks.")

        if self.owner.preferences:
            lines.append(f"  Preference note: {self.owner.preferences}")

        return "\n".join(lines)
