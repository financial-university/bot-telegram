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
        res = dict()
        for pairs in data['pairs']:
            for time_start, pair in pairs.items():
                if pair['date'] in res:
                    for save_pair in res[pair['date']]:
                        if save_pair['time_start'] == pair['time_start'] and save_pair['name'] == pair['name']:
                            save_pair['audience'] = f"{save_pair['audience']}, {pair['audience']}"
                            print(save_pair['groups'].union(pair['groups']))
                            save_pair['groups'] = save_pair['groups'].union(pair['groups'])
                            save_pair['teachers_name'] = f"{save_pair['teachers_name']}, {pair['teachers_name']}"
                            break
                    else:
                        res[pair['date']] = res[pair['date']] + [pair]
                else:
                    res[pair['date']] = [pair]
        return {date: sorted(pairs, key=lambda x: x['time_start']) for date, pairs in res.items()}