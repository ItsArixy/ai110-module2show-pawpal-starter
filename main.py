
from pawpal_system import Owner, Pet, CareTask, ScheduleEntry, DeferredTask, PawPalPlanner, DailySchedule
from datetime import time



myDog = Pet("Buddy", "Dog")
myDog2 = Pet("Grumpy", "Dog")
myOwner = Owner("Alice", time(9, 0), 180)
myTask = CareTask("Morning walk", 20, "high", "Buddy")
firstEntry = ScheduleEntry(myTask, time(9, 0), time(9, 20), "Scheduled task")
secondTask = CareTask("Feed", 10, "medium", "Grumpy")
thirdTask = CareTask("Vet visit", 60, "high", "Buddy")

pawPalPlanner = PawPalPlanner(myOwner)
pawPalPlanner.add_pet(myDog)
pawPalPlanner.add_pet(myDog2)
pawPalPlanner.add_task(myTask)
pawPalPlanner.add_task(secondTask)
pawPalPlanner.add_task(thirdTask)

pawPalPlanner.build_schedule()

print(f"Today's schedule for {myOwner.name}: \n")
print("Scheduled tasks:")
pawPalPlanner
