"""Guard real review targets using filesystem glob semantics, including directory boundaries."""
import glob
import tempfile
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


class CodeRabbitCoverage(unittest.TestCase):
    def test_specialized_guidance_reaches_actual_targets(self):
        rules = yaml.safe_load((ROOT / '.coderabbit.yaml').read_text())['reviews']['path_instructions']
        cases = {
            'complete the intended journey': [
                'docs/INTENT_OS_GENERAL_USER_SPEC.md',
                'humanaios-funding-pipeline/resource-miner/resource_miner/opportunity_journey.py',
                'humanaios-funding-pipeline/resource-miner/intent-os.html',
            ],
            'Resource discovery is candidate retrieval': [
                'humanaios-resource-system/resource_system/gateway.py',
                'humanaios-funding-pipeline/resource-miner/app.py',
                'humanaios-funding-pipeline/resource-miner/resource_miner/sources/discounts.py',
            ],
            'Preserve original P1': [
                'architecture/witness-arena/HARMONIC_CHANNEL_SPEC_V0_1.md',
                'agent_coordination/acat_loop.py',
                'humanaios-funding-pipeline/resource-miner/on-track.html',
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            for paths in cases.values():
                for name in paths:
                    target = Path(temp) / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch()
            (Path(temp) / 'unrelated.py').touch()
            for guidance, paths in cases.items():
                patterns = [r['path'] for r in rules if guidance in r['instructions']]
                matches = {p for pattern in patterns for p in glob.glob(pattern, root_dir=temp, recursive=True)}
                for name in paths:
                    with self.subTest(guidance=guidance, path=name):
                        self.assertIn(name, matches)
                self.assertNotIn('unrelated.py', matches)


if __name__ == '__main__':
    unittest.main()
