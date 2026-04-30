import datetime
import os
import sys

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("JWT_SECRET", "a" * 32)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import chat_handler


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeFacultyTable:
    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        return _FakeResult([{"id": 1, "name": "manik"}])


class _FakeSupabase:
    def table(self, name):
        assert name == "faculty"
        return _FakeFacultyTable()


def test_faculty_schedule_query_is_not_substitution(monkeypatch):
    monkeypatch.setattr(chat_handler, "supabase", _FakeSupabase())

    message = "get schedule of manik"

    assert chat_handler._classify_chat_intent(message, "college-1") == "schedule"
    entities = chat_handler._extract_query_entities(message, "college-1")
    assert entities["faculty_name"] == "manik"
    assert entities["empty_only"] is False


def test_room_availability_query_uses_timetable_empty_rooms(monkeypatch):
    monkeypatch.setattr(chat_handler, "supabase", _FakeSupabase())

    message = "Available Rooms on Thu at 15:40"

    assert chat_handler._classify_chat_intent(message, "college-1") == "schedule"
    entities = chat_handler._extract_query_entities(message, "college-1")
    assert entities["day"] == "Thu"
    assert entities["time_slot"] == "15:40"
    assert entities["room_name"] is None
    assert entities["empty_only"] is True


def test_room_availability_afternoon_time_is_normalized(monkeypatch):
    monkeypatch.setattr(chat_handler, "supabase", _FakeSupabase())

    entities = chat_handler._extract_query_entities("available rooms on Tuesday at 3:40", "college-1")

    assert entities["day"] == "Tue"
    assert entities["time_slot"] == "15:40"
    assert entities["empty_only"] is True


def test_room_availability_today_defaults_to_current_day_and_time(monkeypatch):
    fixed_now = datetime.datetime(2026, 4, 30, 15, 40)

    class _FixedDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.replace(tzinfo=tz)

    monkeypatch.setattr(chat_handler.datetime, "datetime", _FixedDateTime)
    monkeypatch.setattr(chat_handler, "supabase", _FakeSupabase())

    entities = chat_handler._extract_query_entities("get list of empty rooms today", "college-1")

    assert entities["day"] == "Thu"
    assert entities["time_slot"] == "15:40"
    assert entities["empty_only"] is True
