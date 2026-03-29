import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# --- Owner & Pet Setup ---
st.subheader("Owner & Pet Info")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=90)
preferences = st.text_input("Preferences (e.g. morning walks)", value="morning walks")

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Pet age", min_value=0, max_value=30, value=3)
special_needs = st.text_input("Special needs (optional)", value="")

if st.button("Set up owner & pet"):
    owner = Owner(name=owner_name, available_minutes=int(available_minutes), preferences=preferences)
    pet = Pet(name=pet_name, species=species, age=age, special_needs=special_needs)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.scheduler = Scheduler(owner=owner)
    st.success(f"Created owner {owner.name} with pet {pet.get_info()}")

st.divider()

# --- Add Tasks ---
st.subheader("Add Tasks")

if st.session_state.pet is None:
    st.info("Set up an owner and pet above before adding tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.slider("Priority (1=low, 5=high)", min_value=1, max_value=5, value=3)

    category = st.selectbox("Category", ["walk", "feeding", "meds", "play", "grooming", "other"])
    description = st.text_input("Description (optional)", value="")

    if st.button("Add task"):
        task = Task(
            name=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            description=description,
        )
        st.session_state.scheduler.add_task(task, st.session_state.pet)
        st.success(f"Added task: {task.name} ({task.duration_minutes} min, priority {task.priority})")

    # Show current tasks
    all_tasks = st.session_state.pet.tasks
    if all_tasks:
        st.write("Current tasks:")
        st.table([
            {
                "Task": t.name,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Category": t.category,
                "Completed": t.completed,
            }
            for t in all_tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.scheduler is None:
        st.warning("Set up an owner and pet first.")
    elif not st.session_state.pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        plan = st.session_state.scheduler.explain_plan()
        st.success("Schedule generated!")
        st.code(plan, language=None)
