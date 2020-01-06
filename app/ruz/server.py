import ssl
import certifi
import datetime
import logging
from asyncio import sleep
from urllib.parse import quote

import ujson
from aiocache import cached
from aiocache.serializers import PickleSerializer
from aiohttp import ClientSession, ClientError
from marshmallow import ValidationError

from app.ruz.schemas import ScheduleSchema, Data, Group, Teacher

SCHEDULE_SCHEMA = ScheduleSchema()

log = logging.getLogger(__name__)

ssl_context = ssl.create_default_context(cafile=certifi.where())


def date_name(date: datetime) -> str:
    """
    Определяет день недели по дате
    :param date:
    :return:
    """

    return [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ][date.weekday()]


# 1 час
@cached(ttl=3600, serializer=PickleSerializer())
async def get_group(group_name: str) -> Data:
    """
    Запрашивает группу у сервера

    :param group_name:
    :return: id группы в Data
    """

    try:
        async with ClientSession() as client:
            url = f"https://ruz.fa.ru/api/search?term={quote(group_name)}&type=group"
            request = await client.get(url, timeout=2, ssl=ssl_context,)
            response_json = await request.json(loads=ujson.loads)
    except (ClientError, TimeoutError):
        log.warning("Timeout error %s", url)
        return Data.error("Timeout error")
    if response_json:
        return Data(
            [
                Group(id=group["id"], name=group["label"].strip().upper())
                for group in response_json
            ]
        )
    return Data.error("Not found")


# 1 час
@cached(ttl=3600, serializer=PickleSerializer())
async def get_teacher(teacher_name: str) -> Data:
    """
    Поиск преподователя

    :param teacher_name:
    :return: Data
    """

    try:
        async with ClientSession() as client:
            url = (
                f"https://ruz.fa.ru/api/search?term={quote(teacher_name)}&type=lecturer"
            )
            response = await client.get(url, timeout=2, ssl=ssl_context,)
            response_json = await response.json(loads=ujson.loads)
    except (ClientError, TimeoutError):
        log.warning("Timeout error %s", url)
        return Data.error("Timeout error")
    if response_json:
        return Data(
            [Teacher(id=i["id"], name=i["label"]) for i in response_json if i["id"]]
        )
    return Data.error("Not found")


async def get_schedule(
    id: int, date_start: datetime = None, date_end: datetime = None, type: str = "group"
) -> Data:
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
    url = (
        f"https://ruz.fa.ru/api/schedule/{type}/{id}?start={date_start.strftime('%Y.%m.%d')}"
        f"&finish={date_end.strftime('%Y.%m.%d')}&lng=1"
    )
    try:
        async with ClientSession() as client:
            response = await client.get(url, ssl=ssl_context)
            response_json = await response.json(loads=ujson.loads)
    except (ClientError, TimeoutError):
        log.warning("Timeout error %s", url)
        return Data.error("Timeout error")
    try:
        res = SCHEDULE_SCHEMA.load({"pairs": response_json})
        return Data(res)
    except ValidationError as e:
        log.warning("Validation error in get_schedule for %s %s - %r", type, id, e)
        return Data.error("Validation error")


# 2 минуты
@cached(ttl=120, serializer=PickleSerializer())
async def format_schedule(
    id: int,
    type: str,
    start_day: int = 0,
    days: int = 1,
    show_groups: bool = False,
    show_location: bool = False,
) -> str or None:
    """
    Форматирует расписание к виду который отправляет бот


    :param id:
    :param type:
    :param start_day: начальная дата в количестве дней от сейчас
    :param days: количество дней
    :param show_location:
    :param show_groups:
    :return: строку расписания
    """

    text = str()
    date_start = datetime.datetime.now() + datetime.timedelta(days=start_day)
    date_end = date_start + datetime.timedelta(days=days)
    schedule = await get_schedule(
        id, date_start, date_end, type="lecturer" if type == "teacher" else "group"
    )
    if schedule.has_error:
        return None
    else:
        schedule = schedule.data
    date = datetime.datetime.today()
    date += datetime.timedelta(days=start_day)
    for _ in range(days):
        text_date = date.strftime("%d.%m.%Y")
        text += f"📅 {date_name(date)}, {text_date}\n"
        if text_date in schedule:
            selected_days = set()
            for lesson in sorted(schedule[text_date], key=lambda x: x["time_start"]):
                if lesson["time_start"] in selected_days:
                    text += "\n"
                else:
                    text += f"\n⏱{lesson['time_start']} – {lesson['time_end']}⏱\n"
                    selected_days.add(lesson["time_start"])
                text += f"*{lesson['name']}*\n"
                if lesson["type"]:
                    text += f"{lesson['type']}\n"
                if show_groups and lesson["groups"]:
                    if lesson["groups"]:
                        text += "Группы: "
                        text += f"{', '.join(lesson['groups'])}\n"
                if lesson["audience"]:
                    text += f"Где: {lesson['audience']}"
                if show_location and lesson["location"] is not None:
                    text += f", _{lesson['location']}_\n"
                else:
                    text += "\n"
                text += f"Кто: {lesson['teachers_name']}\n"
                if lesson["note"]:
                    text += f'Примечание: {lesson["note"]}\n'
        else:
            text += f"Нет пар\n"
        text += "\n"
        date += datetime.timedelta(days=1)
    return text
