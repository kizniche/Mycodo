# coding=utf-8
"""Unit tests for InfluxDB 1.x manual aggregation helpers.

These tests use synthetic table/record objects (no live InfluxDB required)
to verify window alignment, timestamp selection, and correctness for
_manual_aggregate_mean, _manual_calculate_mean, and _manual_calculate_sum.
"""
import datetime

import pytest

from mycodo.utils.influx import (
    _ManualRecord,
    _ManualTable,
    _manual_aggregate_mean,
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
# _manual_aggregate_mean
# ---------------------------------------------------------------------------

class TestManualAggregateMean:
    """
    Windows are epoch-aligned: aligned_start = floor(epoch / group_sec) * group_sec
    The aggregated record's timestamp is the window *end*: aligned_start + group_sec.
    """

    GROUP_SEC = 60  # 1-minute windows

    def _epoch_to_dt(self, epoch):
        return datetime.datetime.fromtimestamp(epoch, tz=UTC)

    def test_empty_input_returns_empty_list(self):
        assert _manual_aggregate_mean([], self.GROUP_SEC) == []

    def test_empty_table_returns_empty_list(self):
        tables = [_ManualTable([])]
        assert _manual_aggregate_mean(tables, self.GROUP_SEC) == []

    def test_all_none_values_returns_empty_list(self):
        ts = self._epoch_to_dt(1000)
        tables = _make_tables([(ts, None)])
        assert _manual_aggregate_mean(tables, self.GROUP_SEC) == []

    def test_single_point_in_one_window(self):
        # epoch=1000 → aligned_start=floor(1000/60)*60=960 → window_end=1020
        epoch = 1000
        ts = self._epoch_to_dt(epoch)
        tables = _make_tables([(ts, 7.5)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        assert len(result) == 1
        assert len(result[0].records) == 1
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(7.5)
        expected_window_end = datetime.datetime.fromtimestamp(960 + 60, tz=UTC)
        assert record.values['_time'] == expected_window_end

    def test_multiple_points_in_same_window_mean(self):
        # epochs 1000 and 1010 both fall in window [960, 1020)
        ts1 = self._epoch_to_dt(1000)
        ts2 = self._epoch_to_dt(1010)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        assert len(result) == 1
        record = result[0].records[0]
        assert record.values['_value'] == pytest.approx(15.0)  # (10+20)/2
        expected_window_end = datetime.datetime.fromtimestamp(960 + 60, tz=UTC)
        assert record.values['_time'] == expected_window_end

    def test_points_in_multiple_windows(self):
        # epoch 1000 → window [960, 1020), window_end=1020
        # epoch 1080 → window [1080, 1140), window_end=1140
        ts1 = self._epoch_to_dt(1000)
        ts2 = self._epoch_to_dt(1010)
        ts3 = self._epoch_to_dt(1080)
        ts4 = self._epoch_to_dt(1090)
        tables = _make_tables([(ts1, 10.0), (ts2, 30.0), (ts3, 5.0), (ts4, 15.0)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        assert len(result) == 1
        assert len(result[0].records) == 2

        rec0 = result[0].records[0]
        assert rec0.values['_value'] == pytest.approx(20.0)  # (10+30)/2
        assert rec0.values['_time'] == datetime.datetime.fromtimestamp(1020, tz=UTC)

        rec1 = result[0].records[1]
        assert rec1.values['_value'] == pytest.approx(10.0)  # (5+15)/2
        assert rec1.values['_time'] == datetime.datetime.fromtimestamp(1140, tz=UTC)

    def test_epoch_aligned_boundary_point_starts_new_window(self):
        # A point exactly on a window boundary (epoch=1020) starts the NEXT window [1020, 1080)
        ts_before = self._epoch_to_dt(1019)  # window [960, 1020)
        ts_on = self._epoch_to_dt(1020)      # window [1020, 1080)
        tables = _make_tables([(ts_before, 3.0), (ts_on, 9.0)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        assert len(result[0].records) == 2

        rec0 = result[0].records[0]
        assert rec0.values['_value'] == pytest.approx(3.0)
        assert rec0.values['_time'] == datetime.datetime.fromtimestamp(1020, tz=UTC)

        rec1 = result[0].records[1]
        assert rec1.values['_value'] == pytest.approx(9.0)
        assert rec1.values['_time'] == datetime.datetime.fromtimestamp(1080, tz=UTC)

    def test_skips_none_values(self):
        ts1 = self._epoch_to_dt(1000)
        ts2 = self._epoch_to_dt(1010)
        tables = _make_tables([(ts1, None), (ts2, 20.0)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        assert len(result[0].records) == 1
        assert result[0].records[0].values['_value'] == pytest.approx(20.0)

    def test_timezone_preserved_in_result(self):
        """Window-end timestamps should carry the same timezone as the input."""
        epoch = 1000
        ts = self._epoch_to_dt(epoch)
        assert ts.tzinfo is not None
        tables = _make_tables([(ts, 1.0)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        result_time = result[0].records[0].values['_time']
        assert result_time.tzinfo == UTC

    def test_results_sorted_by_window(self):
        """Even with unsorted input, output windows are in ascending order."""
        ts_late = self._epoch_to_dt(1090)
        ts_early = self._epoch_to_dt(1000)
        tables = _make_tables([(ts_late, 99.0), (ts_early, 1.0)])
        result = _manual_aggregate_mean(tables, self.GROUP_SEC)
        times = [r.values['_time'] for r in result[0].records]
        assert times == sorted(times)


# ---------------------------------------------------------------------------
# Integration: value + group_sec combinations should NOT use _manual_aggregate_mean
# ---------------------------------------------------------------------------

class TestManualAggregateMeanNotCalledWithExplicitValue:
    """
    Verify that _manual_calculate_mean and _manual_calculate_sum return a single
    scalar result (not per-window), which is the correct behaviour when value=
    "MEAN"/"SUM" is combined with group_sec — the manual aggregate should not
    override the explicit aggregation.
    """

    def test_mean_returns_single_value_not_per_window(self):
        # Three points spread across two 60-second windows
        ts1 = datetime.datetime.fromtimestamp(1000, tz=UTC)
        ts2 = datetime.datetime.fromtimestamp(1010, tz=UTC)
        ts3 = datetime.datetime.fromtimestamp(1080, tz=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0), (ts3, 30.0)])
        result = _manual_calculate_mean(tables)
        # Should be ONE record with overall mean, not two windowed means
        assert len(result[0].records) == 1
        assert result[0].records[0].values['_value'] == pytest.approx(20.0)

    def test_sum_returns_single_value_not_per_window(self):
        ts1 = datetime.datetime.fromtimestamp(1000, tz=UTC)
        ts2 = datetime.datetime.fromtimestamp(1010, tz=UTC)
        ts3 = datetime.datetime.fromtimestamp(1080, tz=UTC)
        tables = _make_tables([(ts1, 10.0), (ts2, 20.0), (ts3, 30.0)])
        result = _manual_calculate_sum(tables)
        assert len(result[0].records) == 1
        assert result[0].records[0].values['_value'] == pytest.approx(60.0)
