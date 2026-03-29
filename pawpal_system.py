from dataclasses import dataclass
from typing import List


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""

    def get_info(self) -> str:
        pass


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int
    category: str  # e.g., "walk", "feeding", "meds"

    def is_high_priority(self) -> bool:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: str = ""):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_available_time(self) -> int:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks: List[Task] = []

    def generate_schedule(self) -> List[Task]:
        pass

    def explain_plan(self) -> str:
        pass
