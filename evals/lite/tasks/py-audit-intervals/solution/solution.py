"""A set of integers kept as merged half-open intervals."""


class IntervalSet:
    def __init__(self):
        self._items = []

    def add(self, start, end):
        if start > end:
            raise ValueError("start must not exceed end")
        if start == end:
            return
        merged, placed = [], False
        for low, high in self._items:
            if high < start:
                merged.append((low, high))
            elif end < low:
                if not placed:
                    merged.append((start, end))
                    placed = True
                merged.append((low, high))
            else:
                start, end = min(start, low), max(end, high)
        if not placed:
            merged.append((start, end))
        self._items = merged

    def remove(self, start, end):
        if start > end:
            raise ValueError("start must not exceed end")
        if start == end:
            return
        kept = []
        for low, high in self._items:
            if high <= start or end <= low:
                kept.append((low, high))
                continue
            if low < start:
                kept.append((low, start))
            if end < high:
                kept.append((end, high))
        self._items = kept

    def contains(self, value):
        return any(low <= value < high for low, high in self._items)

    def intervals(self):
        return list(self._items)

    def __len__(self):
        return sum(high - low for low, high in self._items)
