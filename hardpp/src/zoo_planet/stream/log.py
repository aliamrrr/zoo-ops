"""Zoo events (feedings, births, transfers) flow through a log read by consumer groups."""

from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Record:
    partition: int
    offset: int
    key: str
    value: Any


class PartitionedLog:
    def __init__(self, partitions: int) -> None:
        self.partitions: list[list[Record]] = [[] for _ in range(partitions)]
        self._next = itertools.count()
        self._lock = threading.Lock()

    def append(self, key: str, value: Any) -> Record:
        with self._lock:
            partition = next(self._next) % len(self.partitions)
            record = Record(partition, len(self.partitions[partition]), key, value)
            self.partitions[partition].append(record)
            return record

    def read(self, partition: int, offset: int, max_records: int) -> list[Record]:
        with self._lock:
            return self.partitions[partition][offset : offset + max_records]


class ConsumerGroup:
    def __init__(self, log: PartitionedLog, name: str) -> None:
        self._log = log
        self.name = name
        self.members: list[str] = []
        self.assignment: dict[str, list[int]] = {}
        self.committed: dict[int, int] = {p: 0 for p in range(len(log.partitions))}

    def join(self, member: str) -> None:
        self.members.append(member)
        if len(self.members) == 1:
            self.assignment[member] = list(range(len(self._log.partitions)))
        else:
            self.assignment[member] = []

    def leave(self, member: str) -> None:
        self.members.remove(member)

    def poll(self, member: str, max_records: int = 10) -> list[Record]:
        records: list[Record] = []
        for partition in self.assignment.get(member, []):
            batch = self._log.read(partition, self.committed[partition], max_records)
            self.committed[partition] += len(batch)
            records.extend(batch)
        return records

    def commit(self, member: str, partition: int, next_offset: int) -> None:
        self.committed[partition] = max(self.committed[partition], next_offset)
