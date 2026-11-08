"""Shared plan builder. Pins are real hashes of the code under test."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pins import code_pins
from src.writer import public_fingerprint


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def make_plan(key, **over):
    t = datetime.now(timezone.utc)
    plan = {
        'task': {'artifact_id': 'config01', 'baseline': '50', 'proposed': '55',
                 'min_allowed': '0', 'max_allowed': '100', 'max_delta': '10'},
        'run_id': 'TEST_001', 'episode_id': 'E001',
        'writer_pubkey_sha256': public_fingerprint(key),
        'allowed_actor': 'A', 'action': 'WRITE_NUMERIC_ARTIFACT',
        'protocol': 'SWARM_HOST_V2', 'non_scored': True, 'tool_policy': 'ALLOW',
        'window': {'not_before': iso(t - timedelta(hours=1)), 'not_after': iso(t + timedelta(hours=1))},
        'protocol_pins': {
            'provider': 'SYNTHETIC_NONE', 'model_a': 'SYNTHETIC_A', 'model_b': 'SYNTHETIC_B',
            'settings_sha256': '1' * 64, 'prompts_sha256': '2' * 64, **code_pins(),
        },
    }
    plan.update(over)
    return plan
