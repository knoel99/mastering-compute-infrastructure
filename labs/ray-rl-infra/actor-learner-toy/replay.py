"""A FIFO replay buffer of trajectories with uniform sampling (lab 11.2)."""
from collections import deque


class ReplayBuffer:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.items = deque(maxlen=capacity)
        self.inserted = 0

    def __len__(self):
        return len(self.items)

    def add(self, traj):
        self.items.append(traj)
        self.inserted += 1

    def sample(self, rng, k):
        """k trajectories drawn uniformly WITH replacement (the same item may come twice)."""
        if not self.items:
            raise ValueError("empty buffer")
        idx = rng.integers(0, len(self.items), size=k)
        return [self.items[i] for i in idx]

    def pop_oldest(self, k):
        """Queue mode: remove and return the k oldest trajectories (each used once)."""
        return [self.items.popleft() for _ in range(k)]

    def ages_in_versions(self, learner_version):
        return [learner_version - t["version"] for t in self.items]
