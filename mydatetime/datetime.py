import time
import datetime


def get_time_now() -> str:
    return time.strftime('%H:%M %d-%m-%Y')


def parse_time(line: str) -> datetime.datetime:
    return datetime.datetime.strptime(line, '%H:%M %d-%m-%Y')
