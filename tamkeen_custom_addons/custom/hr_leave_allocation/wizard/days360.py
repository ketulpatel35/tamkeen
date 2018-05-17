import calendar
# DATE_FORMAT = '%Y-%m-%d'


def get_date_diff_days360(start_date, end_date):
    start_day = start_date.day
    start_month = start_date.month
    start_year = start_date.year
    end_day = end_date.day
    end_month = end_date.month
    end_year = end_date.year

    if (start_day == 31 or (start_month == 2 and (start_day == 29 or (
            start_day == 28 and not calendar.isleap(start_year))))):
        start_day = 30
    if end_day == 31:
        if start_day != 30:
            end_day = 1
            if end_month == 12:
                end_year += 1
                end_month = 1
            else:
                end_month += 1
        else:
            end_day = 30

    return (
        end_day + end_month * 30 + end_year * 360 -
        start_day - start_month * 30 - start_year * 360
    )
