from collections import defaultdict
from datetime import datetime

from marshmallow import fields, Schema, EXCLUDE, pre_load, post_load


class AudienceField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        # FIXME костыль
        return value.replace('_', '-').split('/')[-1]


class DateField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        return datetime.strptime(value, '%Y.%m.%d').strftime('%d.%m.%Y')


class Pair(Schema):
    @pre_load()
    def preload(self, data, many, **kwargs):
        data['groups'] = set((data['group'] or data['stream']).replace(' ', '').split(','))
        return data

    @post_load()
    def postload(self, data, **kwargs):
        return {data['time_start']: data}

    time_start = fields.String(data_key='beginLesson')
    time_end = fields.String(data_key='endLesson')
    name = fields.String(data_key='discipline')
    type = fields.String(data_key='kindOfWork')
    groups = fields.Raw()
    audience = AudienceField(data_key='auditorium')
    location = fields.String(data_key='building')
    teachers_name = fields.String(data_key='lecturer')
    date = DateField()

    class Meta:
        unknown = EXCLUDE


class ScheduleSchema(Schema):
    pairs = fields.List(fields.Nested(Pair()))

    @post_load()
    def postload(self, data, **kwargs):
        res = defaultdict(dict)
        for pairs in data['pairs']:
            for time_start, pair in pairs.items():
                if time_start in res[pair['date']]:
                    if res[pair['date']][time_start]['name'] == pair['name']:
                        added = res[pair['date']][time_start]
                        res[pair['date']][time_start].update(
                            dict(
                                audience=f"{added['audience']}, {pair['audience']}",
                                groups=added['groups'].union(pair['groups']),
                                teachers_name=f"{added['teachers_name']}, {pair['teachers_name']}"
                            ))
                        continue
                res[pair['date']].update({time_start: pair})
        return {date: sorted(pairs.values(), key=lambda x: x['time_start']) for date, pairs in res.items()}