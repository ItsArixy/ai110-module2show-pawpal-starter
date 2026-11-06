from datetime import time

import pytest

from pawpal_system import CareTask, Owner, PawPalPlanner, Pet


def make_planner(
    availability_minutes: int = 60,
    tasks: list[CareTask] | None = None,
) -> PawPalPlanner:
    return PawPalPlanner(
        owner=Owner("Jordan", time(8, 0), availability_minutes),
        pets=[Pet("Mochi", "dog")],
        tasks=tasks or [],
    )


def test_schedule_orders_by_priority_and_keeps_same_priority_order() -> None:
    planner = make_planner(
        tasks=[
            CareTask("Walk", 20, "medium", "Mochi"),
            CareTask("Medication", 5, "high", "Mochi"),
            CareTask("Feed", 10, "high", "Mochi"),
        ]
    )

    schedule = planner.build_schedule()

    assert [entry.task.title for entry in schedule.entries] == [
        "Medication",
        "Feed",
        "Walk",
    ]
    assert schedule.entries[0].starts_at.time() == time(8, 0)
    assert schedule.entries[-1].ends_at.time() == time(8, 35)
    assert schedule.planned_minutes == 35
    assert schedule.remaining_minutes == 25


def test_schedule_defers_tasks_that_do_not_fit_but_keeps_fitting_tasks() -> None:
    planner = make_planner(
        availability_minutes=25,
        tasks=[
            CareTask("Long walk", 30, "high", "Mochi"),
            CareTask("Feed", 10, "medium", "Mochi"),
            CareTask("Brush", 15, "low", "Mochi"),
        ],
    )

    schedule = planner.build_schedule()

    assert [entry.task.title for entry in schedule.entries] == ["Feed", "Brush"]
    assert [item.task.title for item in schedule.deferred_tasks] == ["Long walk"]
    assert "only 25 minutes remain" in schedule.deferred_tasks[0].reason


def test_task_must_be_assigned_to_registered_pet() -> None:
    planner = make_planner()

    with pytest.raises(ValueError, match="Unknown pet assignment"):
        planner.add_task(CareTask("Walk", 20, "high", "Rex"))


def test_task_can_be_updated_and_invalid_assignment_does_not_replace_it() -> None:
    original = CareTask("Walk", 20, "high", "Mochi")
    planner = make_planner(tasks=[original])

    planner.update_task(0, CareTask("Short walk", 10, "medium", "Mochi"))

    assert planner.tasks[0].title == "Short walk"
    with pytest.raises(ValueError, match="Unknown pet assignment"):
        planner.update_task(0, CareTask("Walk", 20, "high", "Rex"))
    assert planner.tasks[0].title == "Short walk"


def test_pet_names_are_unique_without_case_sensitivity() -> None:
    planner = make_planner()

    with pytest.raises(ValueError, match="already registered"):
        planner.add_pet(Pet("mochi", "cat"))


@pytest.mark.parametrize(
    ("task_args", "message"),
    [
        (("", 10, "high", "Mochi"), "title cannot be empty"),
        (("Walk", 0, "high", "Mochi"), "duration must be greater than zero"),
        (("Walk", 10, "urgent", "Mochi"), "Priority must be low, medium, or high"),
    ],
)
def test_invalid_task_data_is_rejected(
    task_args: tuple[str, int, str, str],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CareTask(*task_args)
