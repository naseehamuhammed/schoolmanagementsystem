import random
from datetime import time
from .models import SchoolClass, Teacher, Timetable

def generate_weekly_timetable():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = [
        time(9, 0), time(10, 0), time(11, 0),
        time(12, 0), time(14, 0), time(15, 0)
    ]

    # Clear the existing timetable
    Timetable.objects.all().delete()

    school_classes = SchoolClass.objects.all()
    teachers = Teacher.objects.all()

    for school_class in school_classes:
        used_slots = {day: set() for day in days}  # Track used slots for each day
        for teacher in teachers:
            if not teacher.courses:
                continue  # Skip teachers without an assigned course

            course = teacher.courses  # Assuming one course per teacher
            for day in days:
                available_slots = [
                    slot for slot in time_slots if slot not in used_slots[day]
                ]

                if not available_slots:
                    continue  # No slots left for this day

                # Assign a random available slot
                slot = random.choice(available_slots)
                used_slots[day].add(slot)

                # Create timetable entry
                Timetable.objects.create(
                    teacher=teacher,
                    course=course,
                    school_class=school_class,
                    day=day,
                    time_slot=slot
                )

