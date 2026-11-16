"""Deterministic dependency ordering with cycle reporting."""

import heapq


def install_order(packages: dict) -> list:
    dependencies = {}
    for name, needs in packages.items():
        for need in needs:
            if need not in packages:
                raise KeyError(need)
        dependencies[name] = set(needs)

    dependents = {name: [] for name in dependencies}
    for name, needs in dependencies.items():
        for need in needs:
            dependents[need].append(name)
    waiting = {name: len(needs) for name, needs in dependencies.items()}
    ready = [name for name, count in waiting.items() if count == 0]
    heapq.heapify(ready)

    order = []
    while ready:
        name = heapq.heappop(ready)
        order.append(name)
        for dependent in dependents[name]:
            waiting[dependent] -= 1
            if waiting[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) == len(dependencies):
        return order

    done = set(order)
    path, seen = [], {}
    current = min(name for name in dependencies if name not in done)
    while current not in seen:
        seen[current] = len(path)
        path.append(current)
        current = min(need for need in dependencies[current] if need not in done)
    cycle = path[seen[current]:]
    start = cycle.index(min(cycle))
    cycle = cycle[start:] + cycle[:start]
    raise ValueError(" -> ".join(cycle + [cycle[0]]))
