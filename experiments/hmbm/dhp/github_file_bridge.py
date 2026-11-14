#!/usr/bin/env python3
"""DHP connector-native GitHub file bridge contract.

This module defines the only admissible transformation between an immutable
GitHub artifact reference and a downstream reusable connector file handle.
It deliberately does NOT parse or reserialize artifact content.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Protocol, Mapping, Any
import hashlib, re

HEX40=re.compile(r"^[a-f0-9]{40}$")
HEX64=re.compile(r"^[a-f0-9]{64}$")

@dataclass(frozen=True)
class GithubImmutableSource:
    repository: str
    commit_sha: str
    path: str
    blob_sha: str
    sha256: str
    byte_length: int
    media_type: str = "application/json"

@dataclass(frozen=True)
class ConnectorFileReference:
    download_url: str
    file_id: str
    mime_type: str
    file_name: str

@dataclass(frozen=True)
class BridgeReceipt:
    bridge_version: str
    source: GithubImmutableSource
    output: ConnectorFileReference
    verified_sha256: str
    verified_byte_length: int
    semantic_transformation: bool = False

class FileHandleProvider(Protocol):
    def materialize(self, source: GithubImmutableSource) -> tuple[bytes, ConnectorFileReference]:
        """Return exact source bytes plus a provider-native reusable file handle."""

def validate_source(source: GithubImmutableSource) -> list[str]:
    errors=[]
    if "/" not in source.repository: errors.append("repository")
    if not HEX40.fullmatch(source.commit_sha): errors.append("commit_sha")
    if not HEX40.fullmatch(source.blob_sha): errors.append("blob_sha")
    if not HEX64.fullmatch(source.sha256): errors.append("sha256")
    if not source.path or source.path.startswith("/"): errors.append("path")
    if source.byte_length <= 0: errors.append("byte_length")
    if source.media_type != "application/json": errors.append("media_type")
    return errors

def verify_bytes(source: GithubImmutableSource, data: bytes) -> str:
    errors=validate_source(source)
    if errors: raise ValueError("invalid_source:"+",".join(errors))
    if len(data) != source.byte_length:
        raise ValueError(f"byte_length_mismatch:{len(data)}!={source.byte_length}")
    got=hashlib.sha256(data).hexdigest()
    if got != source.sha256:
        raise ValueError(f"sha256_mismatch:{got}!={source.sha256}")
    return got

def bridge(source: GithubImmutableSource, provider: FileHandleProvider) -> BridgeReceipt:
    data, handle = provider.materialize(source)
    got=verify_bytes(source, data)
    if not handle.file_id or not handle.download_url:
        raise ValueError("provider_returned_nonreusable_handle")
    if handle.mime_type != source.media_type:
        raise ValueError("mime_type_mismatch")
    return BridgeReceipt(
        bridge_version="DHP-CONNECTOR-FILE-BRIDGE-1",
        source=source,
        output=handle,
        verified_sha256=got,
        verified_byte_length=len(data),
        semantic_transformation=False,
    )

def receipt_json(receipt: BridgeReceipt) -> Mapping[str, Any]:
    return asdict(receipt)
