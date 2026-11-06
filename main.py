
from pawpal_system import Owner, Pet, CareTask, ScheduleEntry, DeferredTask
from datetime import time



myDog = Pet("Buddy", "Dog")
myDog2 = Pet("Grumpy", "Dog")
myOwner = Owner("Alice", time(9, 0), 180)
myTask = CareTask("Morning walk", 20, "high", "Buddy")
firstEntry = ScheduleEntry(myTask, time(9, 0), time(9, 20), "Scheduled task")
secondTask = CareTask("Feed", 10, "medium", "Grumpy")
thirdTask = CareTask("Vet visit", 60, "high", "Buddy")

print(f"Today's schedule for {myOwner.name}: \n")
print(firstEntry)
print(secondTask)
print(thirdTask)
