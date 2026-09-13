"""
constants_registry.py — Constants Registry with Molt Integration

System constants stored in versioned files, each carrying molt_id of last change.
Constants are updated only through molts; each write is pinned to a ratified molt.

Constants (from system_graph v0.2):
- behavior_spec.json: dials, investor/business caps, thresholds
- integrity_modes.json: tier definitions, gate thresholds
- priority_weights.json: priority scoring weights, half-lives
- agent_caps.json: per-agent capacity limits
- adversarial_rubric.json: attack definitions and weighting
- brier_threshold.json: revert thresholds per constant type

Each constant carries:
- molt_id: ID of molt that set this version
- molted_at: ISO timestamp
- version: semantic version
- value: current value
- metadata: optional context
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ConstantLifecycle(Enum):
    """Lifecycle states of a constant."""
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    DEPRECATED = "DEPRECATED"
    FROZEN = "FROZEN"


@dataclass
class ConstantVersion:
    """A version of a constant."""
    molt_id: str
    version: str
    value: Any
    molted_at: str
    lifecycle: str
    metadata: Dict[str, Any]


@dataclass
class Constant:
    """A system constant with version history."""
    name: str
    type: str
    current_version: ConstantVersion
    prior_versions: list
    half_life_days: int


class ConstantsRegistry:
    """System Constants Registry with molt integration."""

    def __init__(self):
        self.constants = {}
        self.molt_id_index = {}  # molt_id → list of constants changed

    def create_constant(self, name: str, constant_type: str, initial_value: Any,
                       molt_id: str, half_life_days: int = 30) -> Dict[str, Any]:
        """Create a new constant with initial molt."""
        version = ConstantVersion(
            molt_id=molt_id,
            version="1.0.0",
            value=initial_value,
            molted_at=datetime.now().isoformat(),
            lifecycle=ConstantLifecycle.ACTIVE.value,
            metadata={'created': True},
        )

        constant = Constant(
            name=name,
            type=constant_type,
            current_version=version,
            prior_versions=[],
            half_life_days=half_life_days,
        )

        self.constants[name] = constant
        self.molt_id_index.setdefault(molt_id, []).append(name)

        return {
            'constant': name,
            'molt_id': molt_id,
            'version': '1.0.0',
            'status': 'CREATED',
        }

    def apply_molt_to_constant(self, molt_id: str, constant_name: str,
                               new_value: Any) -> Dict[str, Any]:
        """Apply a ratified molt to a constant."""
        if constant_name not in self.constants:
            return {
                'constant': constant_name,
                'status': 'NOT_FOUND',
                'error': f'Constant {constant_name} not registered',
            }

        constant = self.constants[constant_name]

        # Create new version
        old_version = constant.current_version
        new_version_str = self._increment_version(old_version.version)

        new_version = ConstantVersion(
            molt_id=molt_id,
            version=new_version_str,
            value=new_value,
            molted_at=datetime.now().isoformat(),
            lifecycle=ConstantLifecycle.ACTIVE.value,
            metadata={'prior_molt_id': old_version.molt_id},
        )

        # Move current to prior
        constant.prior_versions.append(old_version)
        constant.current_version = new_version

        # Index
        self.molt_id_index.setdefault(molt_id, []).append(constant_name)

        return {
            'constant': constant_name,
            'molt_id': molt_id,
            'prior_version': old_version.version,
            'new_version': new_version_str,
            'status': 'UPDATED',
        }

    def _increment_version(self, version_str: str) -> str:
        """Increment semantic version."""
        parts = version_str.split('.')
        if len(parts) != 3:
            return '1.0.0'
        parts[2] = str(int(parts[2]) + 1)
        return '.'.join(parts)

    def freeze_constant(self, constant_name: str) -> Dict[str, Any]:
        """Freeze a constant (no more molts allowed)."""
        if constant_name not in self.constants:
            return {'error': f'Constant {constant_name} not found'}

        self.constants[constant_name].current_version.lifecycle = ConstantLifecycle.FROZEN.value

        return {
            'constant': constant_name,
            'lifecycle': 'FROZEN',
            'status': 'FROZEN',
        }

    def deprecate_constant(self, constant_name: str) -> Dict[str, Any]:
        """Deprecate a constant."""
        if constant_name not in self.constants:
            return {'error': f'Constant {constant_name} not found'}

        self.constants[constant_name].current_version.lifecycle = ConstantLifecycle.DEPRECATED.value

        return {
            'constant': constant_name,
            'lifecycle': 'DEPRECATED',
            'status': 'DEPRECATED',
        }

    def get_constant(self, constant_name: str) -> Dict[str, Any]:
        """Retrieve current value of a constant."""
        if constant_name not in self.constants:
            return {'error': f'Constant {constant_name} not found'}

        constant = self.constants[constant_name]
        return asdict(constant)

    def get_constants_by_molt(self, molt_id: str) -> Dict[str, Any]:
        """Get all constants changed by a molt."""
        constants = self.molt_id_index.get(molt_id, [])
        return {
            'molt_id': molt_id,
            'constants_changed': len(constants),
            'constants': constants,
        }

    def export_active_constants(self) -> Dict[str, Any]:
        """Export all active constants as JSON."""
        active = {}
        for name, constant in self.constants.items():
            if constant.current_version.lifecycle == ConstantLifecycle.ACTIVE.value:
                active[name] = {
                    'value': constant.current_version.value,
                    'molt_id': constant.current_version.molt_id,
                    'version': constant.current_version.version,
                    'molted_at': constant.current_version.molted_at,
                }

        return active

    def export_registry(self) -> Dict[str, Any]:
        """Export full registry."""
        return {
            'constants': {
                name: asdict(constant)
                for name, constant in self.constants.items()
            },
            'total_constants': len(self.constants),
            'molt_index': self.molt_id_index,
        }
