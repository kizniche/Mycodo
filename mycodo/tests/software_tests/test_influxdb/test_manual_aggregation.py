# coding=utf-8
"""Unit tests for InfluxDB 1.x manual aggregation helpers.

These tests use synthetic table/record objects (no live InfluxDB required)
to verify correctness for _manual_calculate_mean and _manual_calculate_sum.
"""
import datetime

import pytest

from mycodo.utils.influx import (
    _ManualRecord,
    _ManualTable,
    _manual_calculate_mean,
    _manual_calculate_sum,
)

UTC = datetime.timezone.utc


def _make_tables(points):
    """Build a list of one _ManualTable from (datetime, value) pairs."""
    records = [_ManualRecord(ts, val) for ts, val in points]
    return [_ManualTable(records)]


# ---------------------------------------------------------------------------
# _manual_calculate_mean
# ---------------------------------------------------------------------------

class TestManualCalculateMean:
    def test_empty_input_returns_empty_list(self):
        assert _manual_calculate_mean([]) == []

    def test_empty_table_returns_empty_list(self):
        tables = [_ManualTable([])]
        assert _manual_calculate_mean(tables) == []

    def test_all_none_values_returns_empty_list(self):
        tables = _make_tables([(datetime.datetime(2024, 1, 1, tzinfo=UTC), None)])
        assert _manual_calculate_mean(tables) == []

    def test_single_point(self):
        ts = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        tables = _make_tables([(ts, 42.0)])
        result = _manual_calculate_mean(tables)
        assert len(result) == 1
        assert len(result[0].records) == 1
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(42.0)
        assert record.values['_time'] == ts

    def test_multiple_points_correct_mean(self):
        ts1 = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        ts2 = datetime.datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC)
        ts3 = datetime.datetime(2024, 1, 1, 0, 2, 0, tzinfo=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0), (ts3, 30.0)])
        result = _manual_calculate_mean(tables)
        assert len(result) == 1
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(20.0)  # (10+20+30)/3
        assert record.values['_time'] == ts3  # uses last timestamp

    def test_skips_none_values(self):
        ts1 = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        ts2 = datetime.datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC)
        ts3 = datetime.datetime(2024, 1, 1, 0, 2, 0, tzinfo=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, None), (ts3, 30.0)])
        result = _manual_calculate_mean(tables)
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(20.0)  # (10+30)/2


# ---------------------------------------------------------------------------
# _manual_calculate_sum
# ---------------------------------------------------------------------------

class TestManualCalculateSum:
    def test_empty_input_returns_empty_list(self):
        assert _manual_calculate_sum([]) == []

    def test_empty_table_returns_empty_list(self):
        tables = [_ManualTable([])]
        assert _manual_calculate_sum(tables) == []

    def test_all_none_values_returns_empty_list(self):
        tables = _make_tables([(datetime.datetime(2024, 1, 1, tzinfo=UTC), None)])
        assert _manual_calculate_sum(tables) == []

    def test_single_point(self):
        ts = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        tables = _make_tables([(ts, 5.0)])
        result = _manual_calculate_sum(tables)
        assert len(result) == 1
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(5.0)
        assert record.values['_time'] == ts

    def test_multiple_points_correct_sum(self):
        ts1 = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        ts2 = datetime.datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC)
        ts3 = datetime.datetime(2024, 1, 1, 0, 2, 0, tzinfo=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0), (ts3, 30.0)])
        result = _manual_calculate_sum(tables)
        assert len(result) == 1
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(60.0)
        assert record.values['_time'] == ts3  # uses last timestamp

    def test_skips_none_values(self):
        ts1 = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        ts2 = datetime.datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC)
        ts3 = datetime.datetime(2024, 1, 1, 0, 2, 0, tzinfo=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, None), (ts3, 30.0)])
        result = _manual_calculate_sum(tables)
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(40.0)


# ---------------------------------------------------------------------------
# Integration: value combinations return a single scalar
# ---------------------------------------------------------------------------

class TestManualCalculateScalars:
    """
    Verify that _manual_calculate_mean and _manual_calculate_sum each return a
    single scalar record regardless of how the input points are distributed over
    time — the per-window manual aggregation path is handled server-side.
    """

    def test_mean_returns_single_value(self):
        # Three points spread across two 60-second windows
        ts1 = datetime.datetime.fromtimestamp(1000, tz=UTC)
        ts2 = datetime.datetime.fromtimestamp(1010, tz=UTC)
        ts3 = datetime.datetime.fromtimestamp(1080, tz=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0), (ts3, 30.0)])
        result = _manual_calculate_mean(tables)
        # Should be ONE record with overall mean, not two windowed means
        assert len(result[0].records) == 1
        assert result[0].records[0].values['_value'] == pytest.approx(20.0)

    def test_sum_returns_single_value(self):
        ts1 = datetime.datetime.fromtimestamp(1000, tz=UTC)
        ts2 = datetime.datetime.fromtimestamp(1010, tz=UTC)
        ts3 = datetime.datetime.fromtimestamp(1080, tz=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0), (ts3, 30.0)])
        result = _manual_calculate_sum(tables)
        assert len(result[0].records) == 1
        assert result[0].records[0].values['_value'] == pytest.approx(60.0)
