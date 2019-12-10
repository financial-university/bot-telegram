import requests
import datetime
import logging

from urllib.parse import quote
from app.utils.cache import timed_cache
from app.ruz.schemas import ScheduleSchema
from marshmallow import ValidationError

SCHEDULE_SCHEMA = ScheduleSchema()

log = logging.getLogger(__name__)


class Data:
    """
    Объект данных, полученных с портала
    """

    data: any
    has_error: bool
    error_text: str

    def __init__(self, data: any, has_error: bool = False, error: str = None) -> None:
        self.data = data
        self.has_error = has_error
        self.error_text = error

    @classmethod
    def error(cls, error: str) -> 'Data':
        return cls(data={}, has_error=True, error=error)


def date_name(date: datetime) -> str:
    """
    Определяет день недели по дате

    :param date:
    :return:
    """

    return ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"][date.weekday()]


@timed_cache(minutes=180)
def get_group(group_name: str, return_all_groups: bool = False) -> Data:
    """
    Запрашивает группу у сервера

    :param return_all_groups:
    :param group_name:
    :return: id группы в Data
    """

    try:
        request = requests.get(f"http://ruz.fa.ru/api/search?term={quote(group_name)}&type=group", timeout=2)
    except requests.exceptions.ReadTimeout:
        return Data.error('Timeout error')
    found_group = request.json()
    if not found_group:
        return Data.error('Not found')
    elif return_all_groups is True and len(found_group) > 1:
        return Data({group["label"].strip(): group["id"] for group in found_group})
    else:
        return Data((found_group[0]['label'].strip(), found_group[0]['id']))


@timed_cache(minutes=180)
def get_teacher(teacher_name: str) -> list or None:
    """
    Поиск преподователя

    :param teacher_name:
    :return: [(id, name), ...]
    """

    try:
        request = requests.get(f"http://ruz.fa.ru/api/search?term={quote(teacher_name)}&type=lecturer", timeout=2)
    except requests.exceptions.ReadTimeout:
        return Data.error('Timeout error')
    teachers = [(i['id'], i['label']) for i in request.json() if i['id']]
    return Data(teachers)


@timed_cache(minutes=2)
def format_schedule(user, start_day: int = 0, days: int = 1, group_id: int = None,
                    teacher_id: int = None, date: datetime = None,
                    text: str = "") -> str or None:
    """
    Форматирует расписание к виду который отправляет бот

    :param group_id:
    :param teacher_id: id преподователя
    :param text: начальная строка, к которой прибавляется расписание
    :param start_day: начальная дата в количестве дней от сейчас
    :param days: количество дней
    :param date: дата для расписания на любой один день
    :param user:
    :return: строку расписания
    """

    if date is None:
        date_start = datetime.datetime.now() + datetime.timedelta(days=start_day)
        date_end = date_start + datetime.timedelta(days=days)
    else:
        date_start = date
        date_end = date

    if teacher_id is None and group_id is None:
        if user.role == "student":
            schedule = get_schedule(user.search_id, date_start, date_end, type='group')
        elif user.role == "teacher":
            schedule = get_schedule(user.search_id, date_start, date_end, type='lecturer')
        else:
            schedule = get_schedule(user.search_id, date_start, date_end, type='group')
    elif teacher_id:
        schedule = get_schedule(teacher_id, date_start, date_end, type='lecturer')
    elif group_id:
        schedule = get_schedule(group_id, date_start, date_end, type='group')
    else:
        schedule = get_schedule(user.search_id, date_start, date_end, type='lecturer')

    if schedule in ('Connection error', 'Server error', 'Not found', 'Refreshes', 'Error'):
        return schedule
    if schedule is None:
        return None
    else:
        schedule = schedule.data
    if date is None:
        date = datetime.datetime.today()
        date += datetime.timedelta(days=start_day)
    for _ in range(days):
        text_date = date.strftime('%d.%m.%Y')
        text += f"📅 {date_name(date)}, {text_date}\n"
        if text_date in schedule:
            selected_days = set()
            for lesson in sorted(schedule[text_date], key=lambda x: x['time_start']):
                if lesson['time_start'] in selected_days:
                    text += "\n"
                else:
                    text += f"\n⏱{lesson['time_start']} – {lesson['time_end']}⏱\n"
                    selected_days.add(lesson['time_start'])
                text += f"*{lesson['name']}*\n"
                if lesson['type']:
                    text += f"{lesson['type']}\n"
                if (teacher_id is not None or user.show_groups) and lesson['groups']:
                    if lesson['groups']:
                        text += "Группы: "
                        text += f"{', '.join(lesson['groups'])}\n"
                if teacher_id is not None:
                    if lesson['audience']:
                        text += f"Кабинет: {lesson['audience']}, "
                    text += f"{lesson['location']}"
                if user.search_id is not None and teacher_id is None:
                    if lesson['audience']:
                        text += f"Где: {lesson['audience']}"
                    if user.show_location is True and lesson['location'] is not None:
                        text += f", _{lesson['location']}_\n"
                    else:
                        text += "\n"
                    if "teachers_name" in lesson:
                        text += f"Кто: {lesson['teachers_name']}"
                text += "\n"
        else:
            text += f"Нет пар\n"
        text += "\n"
        date += datetime.timedelta(days=1)
    return text


def get_schedule(id: str, date_start: datetime = None, date_end: datetime = None, type: str = 'group') -> Data:
    """
    Запрашивает расписание у сервера

    :param id:
    :param date_start:
    :param date_end:
    :param type: 'group' 'lecturer'
    :return: {'dd.mm.yyyy': {'time_start': , 'time_end': , 'name': , 'type': , 'groups': , 'audience': , 'location': ,
                             'teachers_name': }}
    """

    if not date_start:
        date_start = datetime.datetime.today()
    if not date_end:
        date_end = datetime.datetime.today() + datetime.timedelta(days=1)
    url = f"http://ruz.fa.ru/api/schedule/{type}/{id}?start={date_start.strftime('%Y.%m.%d')}" \
          f"&finish={date_end.strftime('%Y.%m.%d')}&lng=1"
    try:
        request = requests.get(url)
    except TimeoutError:
        return Data.error('Timeout error')
    request_json = request.json()
    try:
        res = SCHEDULE_SCHEMA.load({'pairs': request_json})
        return Data(res)
    except ValidationError as e:
        log.warning('Validation error in get_schedule for %s %s - %r', type, id, e)
        return Data.error('validation error')
