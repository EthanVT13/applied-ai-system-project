from datetime import date
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart daily scheduling for your pets.")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Section 1: Owner & Pet Setup
# ---------------------------------------------------------------------------
with st.expander("1 — Owner & Pet Setup", expanded=st.session_state.owner is None):
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=90)
    preferences = st.text_input("Preferences (e.g. morning walks)", value="morning walks")

    st.divider()

    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
    age = st.number_input("Pet age", min_value=0, max_value=30, value=3)
    special_needs = st.text_input("Special needs (optional)", value="")

    if st.button("Set up owner & pet", type="primary"):
        owner = Owner(name=owner_name, available_minutes=int(available_minutes), preferences=preferences)
        pet = Pet(name=pet_name, species=species, age=int(age), special_needs=special_needs)
        owner.add_pet(pet)
        st.session_state.owner = owner
        st.session_state.pet = pet
        st.session_state.scheduler = Scheduler(owner=owner)
        st.success(f"Ready! Scheduling for **{owner.name}** with pet **{pet.get_info()}**.")

# ---------------------------------------------------------------------------
# Section 2: Add Tasks
# ---------------------------------------------------------------------------
with st.expander("2 — Add Tasks", expanded=False):
    if st.session_state.pet is None:
        st.info("Complete Owner & Pet Setup above first.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("Task name", value="Morning walk")
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            priority = st.slider("Priority (1 = low, 5 = high)", min_value=1, max_value=5, value=3)
        with col2:
            category = st.selectbox("Category", ["walk", "feeding", "meds", "play", "grooming", "other"])
            preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")
            recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])
            description = st.text_input("Description (optional)", value="")

        if st.button("Add task", type="primary"):
            task = Task(
                name=task_name,
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                preferred_time=preferred_time.strip(),
                recurrence="" if recurrence == "none" else recurrence,
                due_date=date.today() if recurrence != "none" else None,
                description=description,
            )
            st.session_state.scheduler.add_task(task, st.session_state.pet)
            st.success(f"Added: **{task.name}** ({task.duration_minutes} min, priority {task.priority})")

        # Current task table
        tasks = st.session_state.pet.tasks
        if tasks:
            st.markdown("**Current tasks:**")
            st.table([
                {
                    "Task": t.name,
                    "Min": t.duration_minutes,
                    "Priority": t.priority,
                    "Category": t.category,
                    "Time": t.preferred_time or "—",
                    "Recurs": t.recurrence or "—",
                    "Done": "✓" if t.completed else "",
                }
                for t in tasks
            ])
        else:
            st.info("No tasks yet.")

# ---------------------------------------------------------------------------
# Section 3: Generate Schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Today's Schedule")

if st.session_state.scheduler is None:
    st.info("Complete Owner & Pet Setup to get started.")
elif not st.session_state.pet.tasks:
    st.info("Add tasks above to generate a schedule.")
else:
    scheduler: Scheduler = st.session_state.scheduler

    # --- Conflict warnings (shown before the schedule) ---
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning("**Scheduling conflicts detected** — review before committing to this plan:")
        for c in conflicts:
            st.error(c)

    if st.button("Generate schedule", type="primary"):
        schedule = scheduler.generate_schedule()

        if not schedule:
            st.warning("No tasks fit within today's available time.")
        else:
            total = sum(t.duration_minutes for t in schedule)
            remaining = st.session_state.owner.get_available_time() - total

            col1, col2, col3 = st.columns(3)
            col1.metric("Tasks scheduled", len(schedule))
            col2.metric("Time used (min)", total)
            col3.metric("Time remaining (min)", remaining)

            st.markdown("---")

            # Display each task as a card-style block
            for i, task in enumerate(schedule, 1):
                pet_label = task.pet.name if task.pet else "Unknown"
                time_label = f" @ {task.preferred_time}" if task.preferred_time else ""
                recur_label = f" ↻ {task.recurrence}" if task.recurrence else ""
                priority_badge = "🔴 HIGH" if task.is_high_priority() else "🟡 normal"

                with st.container():
                    st.markdown(
                        f"**{i}. {task.name}** for {pet_label}{time_label}  \n"
                        f"{priority_badge} · {task.duration_minutes} min · {task.category}{recur_label}"
                    )
                    if task.description:
                        st.caption(task.description)

            st.markdown("---")
            if st.session_state.owner.preferences:
                st.info(f"Preference note: {st.session_state.owner.preferences}")

    # --- Sorted view ---
    with st.expander("View all tasks sorted by time"):
        all_tasks = st.session_state.pet.tasks
        if all_tasks:
            sorted_tasks = scheduler.sort_by_time(all_tasks)
            st.table([
                {
                    "Time": t.preferred_time or "—",
                    "Task": t.name,
                    "Priority": t.priority,
                    "Duration (min)": t.duration_minutes,
                    "Status": "Done ✓" if t.completed else "Pending",
                }
                for t in sorted_tasks
            ])

    # --- Filter: pending only ---
    with st.expander("View pending tasks only"):
        pending = scheduler.filter_tasks(completed=False)
        if pending:
            st.table([
                {
                    "Task": t.name,
                    "Pet": t.pet.name if t.pet else "—",
                    "Time": t.preferred_time or "—",
                    "Priority": t.priority,
                    "Recurs": t.recurrence or "—",
                }
                for t in pending
            ])
        else:
            st.success("All tasks are complete!")
