"""MCAP reader wrapper.

Isolates every call into the Foxglove `mcap` and `mcap_ros2` libraries
in one module so the rest of the package has no optional-dependency
surface. Downstream code operates on `DecodedMessage` instances only.

rosbag2 emits one `.mcap` chunk per run (or several under a bag
directory). Both layouts are accepted - pass either a file path or a
directory. When given a directory the reader concatenates chunks in
file-sorted order.

Two on-disk layouts are supported:

- Indexed MCAPs (summary + footer present) read via `mcap.reader`.
- Non-indexed / truncated MCAPs (interrupted recordings, or in-flight
  files) read via `mcap.stream_reader`. The fallback is automatic:
  partial-run MCAPs are a realistic failure mode during Tier-3
  bring-up, and we do not want the evaluation pipeline to crash on
  them - it should still surface whatever KPIs the partial run allows.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class DecodedMessage:
    topic: str
    log_time_ns: int
    publish_time_ns: int
    msg: Any


class McapReader:
    """Lazy MCAP iterator. One instance per report build."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path).resolve()
        self._chunks: tuple[Path, ...] = self._discover_chunks(self._path)
        if not self._chunks:
            raise FileNotFoundError(f"no .mcap chunks under {self._path}")
        self._topic_cache: frozenset[str] | None = None

    @staticmethod
    def _discover_chunks(path: Path) -> tuple[Path, ...]:
        if path.is_file() and path.suffix == ".mcap":
            return (path,)
        if path.is_dir():
            return tuple(sorted(path.glob("*.mcap")))
        return ()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def chunks(self) -> tuple[Path, ...]:
        return self._chunks

    def topics(self) -> frozenset[str]:
        """Set of topic names observed. Cached after first scan."""
        if self._topic_cache is not None:
            return self._topic_cache
        found: set[str] = set()
        for chunk in self._chunks:
            found.update(_channel_topics(chunk))
        self._topic_cache = frozenset(found)
        return self._topic_cache

    def iter_messages(self, topics: str | Iterable[str]) -> Iterator[DecodedMessage]:
        """Yield decoded ROS 2 messages for one or more topics.

        Topics absent from the MCAP silently yield nothing; callers are
        expected to check `.topics()` or rely on KPI-level "no messages"
        handling. That keeps individual KPI functions branchless.
        """
        topic_set = frozenset({topics}) if isinstance(topics, str) else frozenset(topics)
        if not topic_set:
            return
        for chunk in self._chunks:
            yield from _iter_decoded(chunk, topic_set)


def _channel_topics(chunk: Path) -> set[str]:
    """Return topics on channels in a single MCAP chunk.

    Uses the indexed summary when available, falls back to a linear
    record scan for non-indexed / truncated files.
    """
    from mcap.reader import make_reader

    try:
        with chunk.open("rb") as fp:
            reader = make_reader(fp)
            summary = reader.get_summary()
            if summary is not None:
                return {ch.topic for ch in summary.channels.values()}
    except Exception:
        # Non-indexed or truncated: fall through to linear scan.
        pass

    from mcap.records import Channel
    from mcap.stream_reader import StreamReader

    topics: set[str] = set()
    with chunk.open("rb") as fp:
        stream = StreamReader(fp)
        try:
            for rec in stream.records:
                if isinstance(rec, Channel):
                    topics.add(rec.topic)
        except Exception:
            # Truncated mid-record is tolerated; whatever channels we
            # saw before the break are already in `topics`.
            pass
    return topics


def _iter_decoded(chunk: Path, topic_filter: frozenset[str]) -> Iterator[DecodedMessage]:
    """Yield decoded messages for `topic_filter`, indexed or streaming."""
    indexed = _iter_decoded_indexed(chunk, topic_filter)
    if indexed is not None:
        yield from indexed
        return
    yield from _iter_decoded_streaming(chunk, topic_filter)


def _iter_decoded_indexed(
    chunk: Path, topic_filter: frozenset[str]
) -> Iterator[DecodedMessage] | None:
    """Return an iterator over decoded messages via the indexed reader.

    Returns None if the file is not seekable/indexed so the caller can
    fall back to the streaming path.
    """
    from mcap.reader import make_reader
    from mcap_ros2.decoder import DecoderFactory

    try:
        fp = chunk.open("rb")
        reader = make_reader(fp, decoder_factories=[DecoderFactory()])
        if reader.get_summary() is None:
            fp.close()
            return None
    except Exception:
        return None

    def _gen():
        try:
            for _schema, channel, message, ros_msg in reader.iter_decoded_messages(
                topics=list(topic_filter)
            ):
                yield DecodedMessage(
                    topic=channel.topic,
                    log_time_ns=message.log_time,
                    publish_time_ns=message.publish_time,
                    msg=ros_msg,
                )
        finally:
            fp.close()

    return _gen()


def _iter_decoded_streaming(
    chunk: Path, topic_filter: frozenset[str]
) -> Iterator[DecodedMessage]:
    """Decode messages via StreamReader (no summary required)."""
    from mcap.records import Channel, Message, Schema
    from mcap.stream_reader import StreamReader
    from mcap_ros2.decoder import DecoderFactory

    factory = DecoderFactory()
    schemas: dict[int, Schema] = {}
    channels: dict[int, Channel] = {}
    decoders: dict[int, Callable[[bytes], Any]] = {}

    with chunk.open("rb") as fp:
        stream = StreamReader(fp)
        try:
            for rec in stream.records:
                if isinstance(rec, Schema):
                    schemas[rec.id] = rec
                elif isinstance(rec, Channel):
                    channels[rec.id] = rec
                    if rec.topic not in topic_filter:
                        continue
                    schema = schemas.get(rec.schema_id)
                    if schema is None:
                        continue
                    decoder = factory.decoder_for(rec.message_encoding, schema)
                    if decoder is not None:
                        decoders[rec.id] = decoder
                elif isinstance(rec, Message):
                    decoder = decoders.get(rec.channel_id)
                    if decoder is None:
                        continue
                    channel = channels[rec.channel_id]
                    try:
                        ros_msg = decoder(rec.data)
                    except Exception:
                        continue
                    yield DecodedMessage(
                        topic=channel.topic,
                        log_time_ns=rec.log_time,
                        publish_time_ns=rec.publish_time,
                        msg=ros_msg,
                    )
        except Exception:
            # Truncated mid-record: stop gracefully.
            return
