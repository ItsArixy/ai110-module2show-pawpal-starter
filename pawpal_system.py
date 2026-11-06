"""Core domain models and daily scheduling logic for PawPal+."""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


_PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


@dataclass(frozen=True)
class Pet:
    name: str
    species: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Pet name cannot be empty.")
        if not self.species.strip():
            raise ValueError("Pet species cannot be empty.")


@dataclass(frozen=True)
class Owner:
    name: str
    availability_start: time = time(8, 0)
    availability_minutes: int = 120

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Owner name cannot be empty.")
        if not 0 <= self.availability_minutes <= 24 * 60:
            raise ValueError("Daily availability must be between 0 and 1440 minutes.")


@dataclass(frozen=True)
class CareTask:
    title: str
    duration_minutes: int
    priority: str
    pet_name: str

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Task title cannot be empty.")
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than zero.")
        if self.priority not in _PRIORITY_RANK:
            raise ValueError("Priority must be low, medium, or high.")
        if not self.pet_name.strip():
            raise ValueError("A task must be assigned to a pet.")


@dataclass(frozen=True)
class ScheduleEntry:
    task: CareTask
    starts_at: datetime
    ends_at: datetime
    reason: str


@dataclass(frozen=True)
class DeferredTask:
    task: CareTask
    reason: str


@dataclass(frozen=True)
class DailySchedule:
    owner: Owner
    entries: list[ScheduleEntry] = field(default_factory=list)
    deferred_tasks: list[DeferredTask] = field(default_factory=list)

    @property
    def planned_minutes(self) -> int:
        return sum(entry.task.duration_minutes for entry in self.entries)

    @property
    def remaining_minutes(self) -> int:
        return self.owner.availability_minutes - self.planned_minutes


class PawPalPlanner:
    """Keep an owner's pet-care data and build a time-bounded daily plan."""

    def __init__(
        self,
        owner: Owner,
        pets: list[Pet] | None = None,
        tasks: list[CareTask] | None = None,
    ) -> None:
        self.owner = owner
        self.pets: dict[str, Pet] = {}
        self.tasks: list[CareTask] = []

        for pet in pets or []:
            self.add_pet(pet)
        for task in tasks or []:
            self.add_task(task)

    def add_pet(self, pet: Pet) -> None:
        key = pet.name.casefold()
        if key in self.pets:
            raise ValueError(f"A pet named {pet.name!r} is already registered.")
        self.pets[key] = pet

    def add_task(self, task: CareTask) -> None:
        if task.pet_name.casefold() not in self.pets:
            raise ValueError(f"Unknown pet assignment: {task.pet_name}.")
        self.tasks.append(task)

    def update_task(self, index: int, task: CareTask) -> None:
        if not 0 <= index < len(self.tasks):
            raise IndexError("Task index is out of range.")
        if task.pet_name.casefold() not in self.pets:
            raise ValueError(f"Unknown pet assignment: {task.pet_name}.")
        self.tasks[index] = task

    def remove_task(self, index: int) -> CareTask:
        if not 0 <= index < len(self.tasks):
            raise IndexError("Task index is out of range.")
        return self.tasks.pop(index)

    def build_schedule(self) -> DailySchedule:
        ordered_tasks = sorted(
            enumerate(self.tasks),
            key=lambda item: (-_PRIORITY_RANK[item[1].priority], item[0]),
        )
        current_time = datetime.combine(date.today(), self.owner.availability_start)
        remaining_minutes = self.owner.availability_minutes
        entries: list[ScheduleEntry] = []
        deferred_tasks: list[DeferredTask] = []

        for _, task in ordered_tasks:
            if task.duration_minutes > remaining_minutes:
                deferred_tasks.append(
                    DeferredTask(
                        task=task,
                        reason=(
                            f"Needs {task.duration_minutes} minutes, but only "
                            f"{remaining_minutes} minutes remain."
                        ),
                    )
                )
                continue

            end_time = current_time + timedelta(minutes=task.duration_minutes)
            entries.append(
                ScheduleEntry(
                    task=task,
                    starts_at=current_time,
                    ends_at=end_time,
                    reason=(
                        f"Scheduled as a {task.priority}-priority task that fits "
                        "the remaining daily availability."
                    ),
                )
            )
            current_time = end_time
            remaining_minutes -= task.duration_minutes

        return DailySchedule(
            owner=self.owner,
            entries=entries,
            deferred_tasks=deferred_tasks,
        )
