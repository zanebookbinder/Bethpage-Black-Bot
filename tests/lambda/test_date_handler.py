from datetime import datetime, timedelta
from freezegun import freeze_time
from lambda_helpers.date_handler import DateHandler


class TestGetDaySuffix:
    def setup_method(self):
        self.dh = DateHandler()

    def test_st_suffix(self):
        assert self.dh.get_day_suffix(1) == "st"
        assert self.dh.get_day_suffix(21) == "st"
        assert self.dh.get_day_suffix(31) == "st"

    def test_nd_suffix(self):
        assert self.dh.get_day_suffix(2) == "nd"
        assert self.dh.get_day_suffix(22) == "nd"

    def test_rd_suffix(self):
        assert self.dh.get_day_suffix(3) == "rd"
        assert self.dh.get_day_suffix(23) == "rd"

    def test_th_suffix(self):
        assert self.dh.get_day_suffix(4) == "th"
        assert self.dh.get_day_suffix(10) == "th"
        assert self.dh.get_day_suffix(14) == "th"
        assert self.dh.get_day_suffix(20) == "th"

    def test_teens_always_th(self):
        assert self.dh.get_day_suffix(11) == "th"
        assert self.dh.get_day_suffix(12) == "th"
        assert self.dh.get_day_suffix(13) == "th"


class TestStripOrdinalSuffix:
    def setup_method(self):
        self.dh = DateHandler()

    def test_strip_st(self):
        assert self.dh.strip_ordinal_suffix("1st") == "1"
        assert self.dh.strip_ordinal_suffix("21st") == "21"

    def test_strip_nd(self):
        assert self.dh.strip_ordinal_suffix("22nd") == "22"

    def test_strip_rd(self):
        assert self.dh.strip_ordinal_suffix("3rd") == "3"

    def test_strip_th(self):
        assert self.dh.strip_ordinal_suffix("13th") == "13"

    def test_no_suffix(self):
        assert self.dh.strip_ordinal_suffix("15") == "15"


class TestGetDateFromDayNumber:
    def setup_method(self):
        self.dh = DateHandler()

    @freeze_time("2026-03-10")
    def test_today(self):
        result = self.dh.get_date_from_day_number("10")
        assert result is not None
        assert "10th" in result
        assert "March" in result
        assert "Tuesday" in result

    @freeze_time("2026-03-10")
    def test_tomorrow(self):
        result = self.dh.get_date_from_day_number("11")
        assert result is not None
        assert "11th" in result

    @freeze_time("2026-03-10")
    def test_day_not_in_range(self):
        result = self.dh.get_date_from_day_number("25")
        assert result is None

    @freeze_time("2026-03-01")
    def test_first_day(self):
        result = self.dh.get_date_from_day_number("1")
        assert result is not None
        assert "1st" in result

    def test_non_digit(self):
        result = self.dh.get_date_from_day_number("abc")
        assert result is None
