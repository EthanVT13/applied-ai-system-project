from pawpal_system import Owner, Pet, Task, Scheduler

# Create owner
alex = Owner(name="Alex", available_minutes=90, preferences="morning walks")

# Create pets
buddy = Pet(name="Buddy", species="Dog", age=3)
luna = Pet(name="Luna", species="Cat", age=5, special_needs="daily eye drops")

alex.add_pet(buddy)
alex.add_pet(luna)

# Add tasks to Buddy
buddy.add_task(Task(
    name="Morning Walk",
    duration_minutes=30,
    priority=5,
    category="walk",
    description="30-minute walk around the block"
))
buddy.add_task(Task(
    name="Breakfast",
    duration_minutes=10,
    priority=4,
    category="feeding",
    description="1 cup dry kibble"
))

# Add tasks to Luna
luna.add_task(Task(
    name="Eye Drops",
    duration_minutes=5,
    priority=5,
    category="meds",
    description="2 drops in each eye, morning"
))
luna.add_task(Task(
    name="Playtime",
    duration_minutes=20,
    priority=2,
    category="play",
    description="Feather wand or laser pointer"
))

# Run scheduler
scheduler = Scheduler(owner=alex)

print("=" * 45)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 45)
print(scheduler.explain_plan())
print("=" * 45)
