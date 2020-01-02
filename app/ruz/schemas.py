from datetime import datetime

from marshmallow import fields, Schema, EXCLUDE, pre_load, post_load


class DefaultString(fields.String):
    def deserialize(self, value, attr: str = None, data=None, **kwargs):
        if not value:
            return self.default
        output = self._deserialize(value, attr, data, **kwargs)
        self._validate(output)
        return output


class AudienceField(DefaultString):
    def _deserialize(self, value, attr, data, **kwargs):
        # FIXME костыль
        return value.replace("_", "-").split("/")[-1]


class DateField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        return datetime.strptime(value, "%Y.%m.%d").strftime("%d.%m.%Y")


class Pair(Schema):
    @pre_load()
    def pre_load(self, data, many, **kwargs):
        data["groups"] = set(
            (data["group"] or data["stream"] or "").replace(" ", "").split(",")
        )
        return data

    @post_load()
    def post_load(self, data, **kwargs):
        return {data["time_start"]: data}

    time_start = fields.String(data_key="beginLesson")
    time_end = fields.String(data_key="endLesson")
    name = DefaultString(data_key="discipline", default="Без названия")
    type = DefaultString(data_key="kindOfWork", default="")
    groups = fields.Raw()
    audience = AudienceField(data_key="auditorium", default="Без аудитории")
    location = DefaultString(data_key="building", default="")
    teachers_name = DefaultString(
        data_key="lecturer", default="Преподователь не определен"
    )
    date = DateField()
    note = fields.String(allow_none=True)

    class Meta:
        unknown = EXCLUDE


class ScheduleSchema(Schema):
    pairs = fields.List(fields.Nested(Pair()))

    @post_load()
    def post_load(self, data, **kwargs):
        res = dict()
        for pairs in data["pairs"]:
            for time_start, pair in pairs.items():
                if pair["date"] in res:
                    for save_pair in res[pair["date"]]:
                        if (
                            save_pair["time_start"] == pair["time_start"]
                            and save_pair["name"] == pair["name"]
                        ):
                            save_pair[
                                "audience"
                            ] = f"{save_pair['audience']}, {pair['audience']}"
                            save_pair["groups"] = save_pair["groups"].union(
                                pair["groups"]
                            )
                            save_pair[
                                "teachers_name"
                            ] = f"{save_pair['teachers_name']}, {pair['teachers_name']}"
                            break
                    else:
                        res[pair["date"]] = res[pair["date"]] + [pair]
                else:
                    res[pair["date"]] = [pair]
        return {
            date: sorted(pairs, key=lambda x: x["time_start"])
            for date, pairs in res.items()
        }
