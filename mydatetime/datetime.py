import time
import datetime


def get_time_now_str() -> str:
    return time.strftime('%H:%M %d-%m-%Y')


def get_time_now_datetime() -> datetime.datetime:
    return datetime.datetime.now()


def parse_time(line: str) -> datetime.datetime:
    return datetime.datetime.strptime(line, '%H:%M %d-%m-%Y')
