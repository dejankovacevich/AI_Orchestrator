"""Bidirectional YAML round-trip for WorkPackets.

``work_packets.structured_yaml`` is the durable form of the full pydantic
model. We write the YAML on create/update and rebuild from it on read so
schema changes don't require column migrations.
"""

from __future__ import annotations

import yaml

from assistant_core.schemas import WorkPacket


def serialize_work_packet(packet: WorkPacket) -> str:
    """Serialize a WorkPacket as a stable, key-ordered YAML string."""
    return yaml.safe_dump(packet.model_dump(mode="json"), sort_keys=False)


def deserialize_work_packet(structured_yaml: str) -> WorkPacket:
    """Rebuild a WorkPacket from its YAML representation."""
    return WorkPacket.model_validate(yaml.safe_load(structured_yaml) or {})


__all__ = ["serialize_work_packet", "deserialize_work_packet"]
