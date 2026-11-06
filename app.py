import streamlit as st

from pawpal_system import CareTask, Owner, PawPalPlanner, Pet


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan pet care around your pets, priorities, and daily availability.")

if "planner" not in st.session_state:
    st.session_state.planner = PawPalPlanner(
        owner=Owner("Jordan"),
        pets=[Pet("Mochi", "dog")],
    )
    st.session_state.schedule = None

planner: PawPalPlanner = st.session_state.planner

st.subheader("Owner and pets")
owner_col, availability_col = st.columns(2)
with owner_col:
    owner_name = st.text_input("Owner name", value=planner.owner.name, key="owner_name")
    availability_start = st.time_input(
        "Day starts at",
        value=planner.owner.availability_start,
        key="availability_start",
    )
with availability_col:
    availability_minutes = st.number_input(
        "Available time today (minutes)",
        min_value=0,
        max_value=1440,
        step=15,
        value=planner.owner.availability_minutes,
        key="availability_minutes",
    )

if owner_name.strip():
    updated_owner = Owner(
        owner_name.strip(),
        availability_start,
        int(availability_minutes),
    )
    if updated_owner != planner.owner:
        planner.owner = updated_owner
        st.session_state.schedule = None
else:
    st.error("Owner name cannot be empty.")

with st.form("add_pet_form", clear_on_submit=True):
    pet_col, species_col = st.columns(2)
    with pet_col:
        new_pet_name = st.text_input("Pet name")
    with species_col:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    try:
        planner.add_pet(Pet(new_pet_name.strip(), new_pet_species))
        st.session_state.schedule = None
    except ValueError as error:
        st.error(str(error))

if planner.pets:
    st.table(
        [{"Pet": pet.name, "Species": pet.species} for pet in planner.pets.values()]
    )

st.subheader("Care tasks")
if planner.pets:
    pet_options = {pet.name: pet.name for pet in planner.pets.values()}
    task_col, duration_col, priority_col = st.columns(3)
    with task_col:
        task_title = st.text_input("Task title", value="Morning walk")
    with duration_col:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
    with priority_col:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    assigned_pet = st.selectbox("Assign to pet", list(pet_options))

    if st.button("Add task"):
        try:
            planner.add_task(
                CareTask(
                    task_title.strip(),
                    int(duration),
                    priority,
                    pet_options[assigned_pet],
                )
            )
            st.session_state.schedule = None
        except ValueError as error:
            st.error(str(error))
else:
    st.info("Add a pet before creating care tasks.")

if planner.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "Task": task.title,
                "Pet": task.pet_name,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
            }
            for task in planner.tasks
        ]
    )
    task_index = st.selectbox(
        "Task to edit or remove",
        range(len(planner.tasks)),
        format_func=lambda index: (
            f"{planner.tasks[index].title} — {planner.tasks[index].pet_name}"
        ),
        key="selected_task_index",
    )
    selected_task = planner.tasks[task_index]
    task_editor_key = (
        f"{task_index}_{selected_task.title}_{selected_task.duration_minutes}_"
        f"{selected_task.priority}_{selected_task.pet_name}"
    )
    edit_col, edit_duration_col, edit_priority_col = st.columns(3)
    with edit_col:
        edited_title = st.text_input(
            "Edit task title",
            value=selected_task.title,
            key=f"edit_title_{task_editor_key}",
        )
    with edit_duration_col:
        edited_duration = st.number_input(
            "Edit duration (minutes)",
            min_value=1,
            max_value=240,
            value=selected_task.duration_minutes,
            key=f"edit_duration_{task_editor_key}",
        )
    with edit_priority_col:
        edited_priority = st.selectbox(
            "Edit priority",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(selected_task.priority),
            key=f"edit_priority_{task_editor_key}",
        )
    edited_pet = st.selectbox(
        "Edit pet assignment",
        list(pet_options),
        index=list(pet_options).index(selected_task.pet_name),
        key=f"edit_pet_{task_editor_key}",
    )
    update_col, remove_col = st.columns(2)
    with update_col:
        update_clicked = st.button("Update selected task")
    with remove_col:
        remove_clicked = st.button("Remove selected task")

    if update_clicked:
        try:
            planner.update_task(
                task_index,
                CareTask(
                    edited_title.strip(),
                    int(edited_duration),
                    edited_priority,
                    pet_options[edited_pet],
                ),
            )
            st.session_state.schedule = None
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    if remove_clicked:
        planner.remove_task(task_index)
        st.session_state.schedule = None
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()
st.subheader("Daily schedule")
if st.button("Generate schedule", type="primary"):
    st.session_state.schedule = planner.build_schedule()

schedule = st.session_state.schedule
if schedule is not None:
    st.write(
        f"Plan for **{schedule.owner.name}** — "
        f"{schedule.planned_minutes} of {schedule.owner.availability_minutes} "
        "available minutes planned."
    )
    if schedule.entries:
        st.table(
            [
                {
                    "Time": f"{entry.starts_at:%H:%M}–{entry.ends_at:%H:%M}",
                    "Task": entry.task.title,
                    "Pet": entry.task.pet_name,
                    "Priority": entry.task.priority,
                    "Why": entry.reason,
                }
                for entry in schedule.entries
            ]
        )
    else:
        st.info("No tasks fit into today's available time.")

    if schedule.deferred_tasks:
        st.warning("Some tasks were deferred:")
        for deferred in schedule.deferred_tasks:
            st.write(
                f"- **{deferred.task.title}** ({deferred.task.pet_name}): "
                f"{deferred.reason}"
            )
