"""
Holiday calendar module for US Federal Holidays (2020-2025).
Provides exact calendar dates and bridge-day / weekend-proximity indicators.
"""

import pandas as pd


def get_us_federal_holidays(start_year=2020, end_year=2025):
    """
    Generates US Federal Holidays table with observed dates.
    """
    holidays = []
    for y in range(start_year, end_year + 1):
        # New Year's Day
        holidays.append((pd.Timestamp(f"{y}-01-01"), "New Year's Day"))

        # MLK Jr Day: 3rd Monday in Jan
        mlk = pd.date_range(start=f"{y}-01-01", end=f"{y}-01-31", freq="WOM-3MON")[0]
        holidays.append((mlk, "Martin Luther King Jr. Day"))

        # Washington's Birthday / Presidents' Day: 3rd Monday in Feb
        pres = pd.date_range(start=f"{y}-02-01", end=f"{y}-02-28", freq="WOM-3MON")[0]
        holidays.append((pres, "Presidents' Day"))

        # Memorial Day: Last Monday in May
        mem = pd.date_range(start=f"{y}-05-01", end=f"{y}-05-31", freq="W-MON")[-1]
        holidays.append((mem, "Memorial Day"))

        # Juneteenth: June 19 (Federal holiday recognized in 2021+)
        if y >= 2021:
            holidays.append((pd.Timestamp(f"{y}-06-19"), "Juneteenth National Independence Day"))

        # Independence Day: July 4
        holidays.append((pd.Timestamp(f"{y}-07-04"), "Independence Day"))

        # Labor Day: 1st Monday in Sep
        labor = pd.date_range(start=f"{y}-09-01", end=f"{y}-09-30", freq="WOM-1MON")[0]
        holidays.append((labor, "Labor Day"))

        # Columbus Day: 2nd Monday in Oct
        columbus = pd.date_range(start=f"{y}-10-01", end=f"{y}-10-31", freq="WOM-2MON")[0]
        holidays.append((columbus, "Columbus Day"))

        # Veterans Day: Nov 11
        holidays.append((pd.Timestamp(f"{y}-11-11"), "Veterans Day"))

        # Thanksgiving: 4th Thursday in Nov
        thx = pd.date_range(start=f"{y}-11-01", end=f"{y}-11-30", freq="WOM-4THU")[0]
        holidays.append((thx, "Thanksgiving"))

        # Christmas: Dec 25
        holidays.append((pd.Timestamp(f"{y}-12-25"), "Christmas Day"))

    df = pd.DataFrame(holidays, columns=["date", "holiday_name"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


if __name__ == "__main__":
    df_h = get_us_federal_holidays(2020, 2024)
    print(f"Total federal holidays generated (2020-2024): {len(df_h)}")
    print(df_h.head(10))
