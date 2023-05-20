import os
from dotenv import load_dotenv
import datetime


def calculate_fridays(day_displace):

    # gets number of fridays [start, end)
    def fridays_between(start, end):
        fridays = 0
        while start < end:
            if start.weekday() == 4:
                fridays += 1
            start += datetime.timedelta(days=1)
        return fridays

    # Get today's date
    today = datetime.datetime.now()

    # get displaced start date
    end_date = datetime.datetime(
        today.year, (today.month + (today.day >= day_displace)) % 12, day_displace)

    return 0 if (days := fridays_between(today, end_date)) == 0 else 1 / days


print(calculate_fridays(24))
