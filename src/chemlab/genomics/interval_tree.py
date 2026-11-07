"""
Interval tree for efficient genomic range queries.

Provides O(log n) interval queries for genomic coordinates.
Used for finding genes, variants, and features in genomic regions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from bisect import bisect_left, bisect_right


@dataclass(slots=True)
class Interval:
    """Genomic interval with associated data."""
    start: int
    end: int
    data: Any

    def __lt__(self, other: Interval) -> bool:
        return self.start < other.start

    def overlaps(self, start: int, end: int) -> bool:
        """Check if interval overlaps query range."""
        return not (self.end < start or self.start > end)

    def contains(self, position: int) -> bool:
        """Check if interval contains position."""
        return self.start <= position <= self.end


class IntervalTree:
    """
    Interval tree for efficient range queries.

    Uses a simple sorted list with binary search for O(log n + k) queries,
    where k is the number of overlapping intervals.
    """

    def __init__(self) -> None:
        self._intervals: list[Interval] = []
        self._starts: list[int] = []
        self._ends: list[int] = []

    def add(self, start: int, end: int, data: Any) -> None:
        """Add an interval to the tree."""
        interval = Interval(start, end, data)
        # Insert maintaining sort order
        idx = bisect_right(self._starts, start)
        self._intervals.insert(idx, interval)
        self._starts.insert(idx, start)
        self._ends.insert(idx, end)

    def add_many(self, intervals: list[tuple[int, int, Any]]) -> None:
        """Add multiple intervals efficiently."""
        for start, end, data in intervals:
            self.add(start, end, data)
        # Re-sort if bulk added
        self._intervals.sort()
        self._starts = [i.start for i in self._intervals]
        self._ends = [i.end for i in self._intervals]

    def query(self, start: int, end: int) -> list[tuple[int, int, Any]]:
        """
        Find all intervals overlapping [start, end].

        Returns list of (start, end, data) tuples.
        """
        if not self._intervals:
            return []

        # Find first interval that could overlap
        # An interval overlaps if its end >= query_start
        # We can binary search on ends
        left = bisect_left(self._ends, start)

        results = []
        for i in range(left, len(self._intervals)):
            interval = self._intervals[i]
            if interval.start > end:
                break
            if interval.overlaps(start, end):
                results.append((interval.start, interval.end, interval.data))

        return results

    def query_point(self, position: int) -> list[tuple[int, int, Any]]:
        """
        Find all intervals containing a single position.

        Returns list of (start, end, data) tuples.
        """
        if not self._intervals:
            return []

        # Find first interval that could contain position
        left = bisect_left(self._ends, position)

        results = []
        for i in range(left, len(self._intervals)):
            interval = self._intervals[i]
            if interval.start > position:
                break
            if interval.contains(position):
                results.append((interval.start, interval.end, interval.data))

        return results

    def query_nearest(
        self,
        position: int,
        max_distance: int | None = None
    ) -> list[tuple[int, int, Any, int]]:
        """
        Find intervals nearest to a position.

        Returns list of (start, end, data, distance) tuples, sorted by distance.
        """
        if not self._intervals:
            return []

        results = []
        for interval in self._intervals:
            if interval.start <= position <= interval.end:
                distance = 0
            elif position < interval.start:
                distance = interval.start - position
            else:  # position > interval.end
                distance = position - interval.end

            if max_distance is None or distance <= max_distance:
                results.append((interval.start, interval.end, interval.data, distance))

        results.sort(key=lambda x: x[3])
        return results

    def __len__(self) -> int:
        return len(self._intervals)

    def __bool__(self) -> bool:
        return bool(self._intervals)

    def clear(self) -> None:
        """Remove all intervals."""
        self._intervals.clear()
        self._starts.clear()
        self._ends.clear()

    def get_all(self) -> list[tuple[int, int, Any]]:
        """Get all intervals."""
        return [(i.start, i.end, i.data) for i in self._intervals]


class GenomicIntervalTree:
    """
    Chromosome-aware interval tree for genomic data.

    Maintains separate interval trees per chromosome for efficient
    genomic coordinate queries.
    """

    def __init__(self) -> None:
        self._trees: dict[str, IntervalTree] = {}

    def _get_tree(self, chromosome: str) -> IntervalTree:
        """Get or create tree for chromosome."""
        if chromosome not in self._trees:
            self._trees[chromosome] = IntervalTree()
        return self._trees[chromosome]

    def add_interval(
        self,
        chromosome: str,
        start: int,
        end: int,
        data: Any
    ) -> None:
        """Add an interval to the chromosome-specific tree."""
        tree = self._get_tree(chromosome)
        tree.add(start, end, data)

    def add_many(
        self,
        intervals: list[tuple[str, int, int, Any]]
    ) -> None:
        """Add multiple intervals efficiently."""
        # Group by chromosome
        by_chrom: dict[str, list[tuple[int, int, Any]]] = {}
        for chrom, start, end, data in intervals:
            by_chrom.setdefault(chrom, []).append((start, end, data))

        # Add to each tree
        for chrom, chrom_intervals in by_chrom.items():
            tree = self._get_tree(chrom)
            tree.add_many(chrom_intervals)

    def query(
        self,
        chromosome: str,
        start: int,
        end: int
    ) -> list[tuple[int, int, Any]]:
        """
        Query intervals on a chromosome overlapping [start, end].

        Returns list of (start, end, data) tuples.
        """
        if chromosome not in self._trees:
            return []
        return self._trees[chromosome].query(start, end)

    def query_point(
        self,
        chromosome: str,
        position: int
    ) -> list[tuple[int, int, Any]]:
        """Query intervals containing a single position on a chromosome."""
        if chromosome not in self._trees:
            return []
        return self._trees[chromosome].query_point(position)

    def query_nearest(
        self,
        chromosome: str,
        position: int,
        max_distance: int | None = None
    ) -> list[tuple[int, int, Any, int]]:
        """Find nearest intervals to a position on a chromosome."""
        if chromosome not in self._trees:
            return []
        return self._trees[chromosome].query_nearest(position, max_distance)

    def get_chromosomes(self) -> list[str]:
        """Get list of chromosomes with data."""
        return list(self._trees.keys())

    def get_tree(self, chromosome: str) -> IntervalTree | None:
        """Get the interval tree for a chromosome."""
        return self._trees.get(chromosome)

    def clear(self) -> None:
        """Clear all data."""
        self._trees.clear()

    def __len__(self) -> int:
        return sum(len(t) for t in self._trees.values())

    def __contains__(self, chromosome: str) -> bool:
        return chromosome in self._trees


class GenomicIndex:
    """
    Multi-track genomic index for fast queries.

    Supports multiple feature types (genes, variants, regulatory regions, etc.)
    on the same genomic coordinates.
    """

    def __init__(self) -> None:
        self._tracks: dict[str, GenomicIntervalTree] = {}

    def add_track(self, track_name: str) -> GenomicIntervalTree:
        """Create or get a named track."""
        if track_name not in self._tracks:
            self._tracks[track_name] = GenomicIntervalTree()
        return self._tracks[track_name]

    def get_track(self, track_name: str) -> GenomicIntervalTree | None:
        """Get a track by name."""
        return self._tracks.get(track_name)

    def query_all(
        self,
        chromosome: str,
        start: int,
        end: int
    ) -> dict[str, list[tuple[int, int, Any]]]:
        """
        Query all tracks for a region.

        Returns dict of track_name -> list of (start, end, data).
        """
        results = {}
        for track_name, track in self._tracks.items():
            intervals = track.query(chromosome, start, end)
            if intervals:
                results[track_name] = intervals
        return results

    def query_point_all(
        self,
        chromosome: str,
        position: int
    ) -> dict[str, list[tuple[int, int, Any]]]:
        """Query all tracks at a single position."""
        results = {}
        for track_name, track in self._tracks.items():
            intervals = track.query_point(chromosome, position)
            if intervals:
                results[track_name] = intervals
        return results

    def get_track_names(self) -> list[str]:
        """Get all track names."""
        return list(self._tracks.keys())

    def clear(self) -> None:
        """Clear all tracks."""
        self._tracks.clear()