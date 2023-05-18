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
    displaced = datetime.datetime(today.year, today.month, day_displace)

    # Calculate the end date (a month from today)
    end_date = datetime.datetime(today.year, (today.month+1) % 12, today.day)

    return fridays_between(today, end_date) / fridays_between(displaced, end_date)


x = 2

print("Number of Fridays:", calculate_fridays(x))
