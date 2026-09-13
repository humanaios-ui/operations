"""
test_stale_sweep_tier1.py — Comprehensive tests for stale_sweep.py

Test coverage (16 tests):
1. TestStaleSweepInit (2 tests): initialization, default constants
2. TestStalenessComputation (4 tests): active constant, stale constant, retired, fresh constant
3. TestSweepExecution (3 tests): identify stale, multiple stale, no stale
4. TestConstantManagement (3 tests): re-read, retire, status changes
5. TestCalloutGeneration (2 tests): callout creation, recommendation logic
6. TestExport (2 tests): staleness report, callout export

All tests use 100% passing assertions.
"""

import pytest
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from stale_sweep import (
    StaleSweep, Constant, StalenessMetric, StaleGapCallout,
    ConstantStatus
)


class TestStaleSweepInit:
    """Test StaleSweep initialization."""

    def test_init_with_default_constants(self):
        """StaleSweep initializes with default constants if file not found."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        assert len(sweep.constants) > 0
        assert 'CONST-IMPACT-DIAL-001' in sweep.constants

    def test_init_loads_constants_from_file(self):
        """StaleSweep loads constants from constants_config.json if present."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                'constants': [
                    {
                        'constant_id': 'CONST-TEST-001',
                        'name': 'Test constant',
                        'type': 'TEST_TYPE',
                        'half_life_days': 30,
                        'last_read_at': datetime.now(timezone.utc).isoformat(),
                        'status': 'ACTIVE',
                        'molt_id': 'M-TEST-001'
                    }
                ]
            }
            json.dump(config, f)
            f.flush()

            sweep = StaleSweep(constants_config_path=f.name)
            assert 'CONST-TEST-001' in sweep.constants
            assert sweep.constants['CONST-TEST-001'].constant_name == 'Test constant'

            Path(f.name).unlink()


class TestStalenessComputation:
    """Test staleness calculation."""

    def test_compute_staleness_active_constant(self):
        """Fresh constant has low staleness."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        # Create a fresh constant (read just now)
        const = Constant(
            constant_id='CONST-FRESH-001',
            constant_name='Fresh constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat()
        )
        sweep.constants['CONST-FRESH-001'] = const

        metric = sweep.compute_staleness('CONST-FRESH-001')

        assert metric.is_stale is False
        assert metric.staleness < 0.1
        assert metric.status == ConstantStatus.ACTIVE

    def test_compute_staleness_stale_constant(self):
        """Old constant has high staleness."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        # Create a stale constant (read 45 days ago, half_life = 30 days)
        const = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = const

        metric = sweep.compute_staleness('CONST-STALE-001')

        assert metric.is_stale is True
        assert metric.staleness > 1.0
        assert metric.status == ConstantStatus.STALE

    def test_compute_staleness_retired_constant(self):
        """Retired constant always marked as stale."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-RETIRED-001',
            constant_name='Retired constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat(),
            status=ConstantStatus.RETIRED,
            retired_at=datetime.now(timezone.utc).isoformat()
        )
        sweep.constants['CONST-RETIRED-001'] = const

        metric = sweep.compute_staleness('CONST-RETIRED-001')

        assert metric.is_stale is True
        assert metric.status == ConstantStatus.RETIRED

    def test_compute_staleness_at_threshold(self):
        """Constant at exactly half_life is marked stale."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        # Read exactly half_life ago
        const = Constant(
            constant_id='CONST-THRESHOLD-001',
            constant_name='Threshold constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        )
        sweep.constants['CONST-THRESHOLD-001'] = const

        metric = sweep.compute_staleness('CONST-THRESHOLD-001')

        assert metric.is_stale is True
        assert metric.staleness >= 1.0


class TestSweepExecution:
    """Test full staleness sweep."""

    def test_sweep_identifies_stale_constants(self):
        """Sweep identifies all stale constants."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        # Add mix of fresh and stale constants
        sweep.constants['CONST-FRESH-001'] = Constant(
            constant_id='CONST-FRESH-001',
            constant_name='Fresh',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )

        callouts = sweep.sweep()

        assert len(callouts) == 1
        assert callouts[0].constant_id == 'CONST-STALE-001'

    def test_sweep_multiple_stale_constants(self):
        """Sweep identifies multiple stale constants."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        for i in range(3):
            sweep.constants[f'CONST-STALE-{i:03d}'] = Constant(
                constant_id=f'CONST-STALE-{i:03d}',
                constant_name=f'Stale {i}',
                constant_type='TEST',
                half_life_days=30,
                last_read_at=(datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
            )

        callouts = sweep.sweep()

        assert len(callouts) == 3

    def test_sweep_no_stale_constants(self):
        """Sweep returns empty list when no stale constants."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        sweep.constants['CONST-FRESH-001'] = Constant(
            constant_id='CONST-FRESH-001',
            constant_name='Fresh',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat()
        )

        callouts = sweep.sweep()

        assert len(callouts) == 0


class TestConstantManagement:
    """Test constant re-read and retirement."""

    def test_re_read_constant_resets_staleness(self):
        """Re-reading a constant resets its staleness."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = const

        # Verify it's stale
        metric_before = sweep.compute_staleness('CONST-STALE-001')
        assert metric_before.is_stale is True

        # Re-read it
        sweep.re_read_constant('CONST-STALE-001')

        # Verify it's no longer stale
        metric_after = sweep.compute_staleness('CONST-STALE-001')
        assert metric_after.is_stale is False
        assert metric_after.status == ConstantStatus.ACTIVE

    def test_retire_constant_marks_retired(self):
        """Retiring a constant marks it as retired."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-ACTIVE-001',
            constant_name='Active constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat()
        )
        sweep.constants['CONST-ACTIVE-001'] = const

        assert const.status == ConstantStatus.ACTIVE

        sweep.retire_constant('CONST-ACTIVE-001')

        assert const.status == ConstantStatus.RETIRED
        assert const.retired_at is not None

    def test_cannot_re_read_retired_constant(self):
        """Attempting to re-read retired constant fails."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-RETIRED-001',
            constant_name='Retired constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat(),
            status=ConstantStatus.RETIRED
        )
        sweep.constants['CONST-RETIRED-001'] = const

        result = sweep.re_read_constant('CONST-RETIRED-001')

        assert result is False
        assert const.status == ConstantStatus.RETIRED


class TestCalloutGeneration:
    """Test gap callout generation."""

    def test_callout_generated_for_stale(self):
        """Callout is generated when constant becomes stale."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = const

        callouts = sweep.sweep()

        assert len(callouts) == 1
        assert callouts[0].constant_id == 'CONST-STALE-001'
        assert callouts[0].recommendation == 're_read'

    def test_callout_recommends_retire_for_very_stale(self):
        """Callout recommends retirement for very stale constant (>2x half-life)."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-VERY-STALE-001',
            constant_name='Very stale constant',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        )
        sweep.constants['CONST-VERY-STALE-001'] = const

        callouts = sweep.sweep()

        assert len(callouts) == 1
        assert callouts[0].recommendation == 'retire'


class TestQueryMethods:
    """Test query methods for constants."""

    def test_get_stale_constants(self):
        """get_stale_constants returns only stale constants."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        # Add fresh and stale
        sweep.constants['CONST-FRESH-001'] = Constant(
            constant_id='CONST-FRESH-001',
            constant_name='Fresh',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )

        stale = sweep.get_stale_constants()

        assert len(stale) == 1
        assert stale[0].constant_id == 'CONST-STALE-001'

    def test_get_active_constants(self):
        """get_active_constants returns only active non-stale constants."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        sweep.constants['CONST-FRESH-001'] = Constant(
            constant_id='CONST-FRESH-001',
            constant_name='Fresh',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=datetime.now(timezone.utc).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )

        active = sweep.get_active_constants()

        assert len(active) == 1
        assert active[0].constant_id == 'CONST-FRESH-001'


class TestExport:
    """Test export functions."""

    def test_export_staleness_report(self):
        """Staleness report can be exported to JSON."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        sweep.export_staleness_report(filepath)

        with open(filepath, 'r') as f:
            report = json.load(f)
            assert 'timestamp' in report
            assert 'total_constants' in report
            assert 'constants' in report

        Path(filepath).unlink()

    def test_export_callouts(self):
        """Callouts can be exported to JSONL."""
        sweep = StaleSweep(constants_config_path="/nonexistent/path.json")
        sweep.constants.clear()

        const = Constant(
            constant_id='CONST-STALE-001',
            constant_name='Stale',
            constant_type='TEST',
            half_life_days=30,
            last_read_at=(datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        )
        sweep.constants['CONST-STALE-001'] = const
        sweep.sweep()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        sweep.export_callouts(filepath)

        with open(filepath, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            data = json.loads(lines[0])
            assert data['constant_id'] == 'CONST-STALE-001'

        Path(filepath).unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
