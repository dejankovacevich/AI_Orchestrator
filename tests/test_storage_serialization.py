from assistant_core.schemas import WorkPacket
from assistant_core.storage import deserialize_work_packet, serialize_work_packet


def test_work_packet_serialization_preserves_extended_fields():
    packet = WorkPacket(
        title="Morning prep",
        objective="Prepare a brief.",
        desired_outputs=["01_MORNING_BRIEF.md"],
        source_paths=["~/LocalAI/inbox/notes"],
        audience="private user",
        cloud_policy={"allowed": False, "explicit": True},
    )

    restored = deserialize_work_packet(serialize_work_packet(packet))

    assert restored.id == packet.id
    assert restored.desired_outputs == ["01_MORNING_BRIEF.md"]
    assert restored.source_paths == ["~/LocalAI/inbox/notes"]
    assert restored.audience == "private user"
    assert restored.cloud_policy == {"allowed": False, "explicit": True}
