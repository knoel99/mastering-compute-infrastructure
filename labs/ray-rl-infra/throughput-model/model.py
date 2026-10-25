"""Analytical model of an online actor-learner loop (lab 11.3).

Vocabulary (see chapter 6 of the course):
  N       number of actors
  m       environment steps per trajectory
  t_roll  time for one actor to produce one trajectory (seconds)
  t_sync  time for one actor to fetch the current weights (seconds)
  b       trajectories consumed by one learner update
  s_L     learner time for one update (seconds)

Everything here is a closed-form model: no randomness, no wall clock.
"""
import math


def sync_time(alpha_s, weight_bytes, bandwidth_Bps):
    """Hockney (alpha-beta) cost of one weight fetch: alpha + n / B."""
    return alpha_s + weight_bytes / bandwidth_Bps


def broadcast_time(alpha_s, weight_bytes, bandwidth_Bps, receivers, topology="star"):
    """Time for one source to deliver the weights to `receivers` nodes.

    star: the source sends to each receiver in turn on one link -> alpha + r n / B
    tree: binary relay, ceil(log2(r + 1)) rounds of (alpha + n / B)
    """
    if topology == "star":
        return alpha_s + receivers * weight_bytes / bandwidth_Bps
    if topology == "tree":
        return math.ceil(math.log2(receivers + 1)) * (alpha_s + weight_bytes / bandwidth_Bps)
    raise ValueError(topology)


def actor_cycle(t_roll, t_sync):
    """One actor, never blocked: fetch weights, then roll out."""
    return t_sync + t_roll


def production_rate(n_actors, m, t_roll, t_sync):
    """Environment steps per second if no actor ever waits."""
    return n_actors * m / actor_cycle(t_roll, t_sync)


def consumption_capacity(b, m, s_L):
    """Fresh environment steps per second the learner can ingest at full speed."""
    return b * m / s_L


def throughput(n_actors, m, t_roll, t_sync, b, s_L, replay_ratio=1.0):
    """Steady-state steps per second that reach the learner: min(P, C / R)."""
    return min(production_rate(n_actors, m, t_roll, t_sync),
               consumption_capacity(b, m, s_L) / replay_ratio)


def n_star(m, t_roll, t_sync, b, s_L, replay_ratio=1.0):
    """Real-valued number of actors at which production equals consumption."""
    return consumption_capacity(b, m, s_L) / replay_ratio * actor_cycle(t_roll, t_sync) / m


def actors_needed(m, t_roll, t_sync, b, s_L, replay_ratio=1.0):
    return math.ceil(n_star(m, t_roll, t_sync, b, s_L, replay_ratio) - 1e-9)


def learner_utilisation(n_actors, m, t_roll, t_sync, b, s_L):
    return min(1.0, production_rate(n_actors, m, t_roll, t_sync) / consumption_capacity(b, m, s_L))


def actor_utilisation(n_actors, m, t_roll, t_sync, b, s_L):
    p = production_rate(n_actors, m, t_roll, t_sync)
    return min(1.0, consumption_capacity(b, m, s_L) / p)


def lag_updates(n_actors, m, t_roll, t_sync, b, s_L, policy="block", queue_cap=None, credits=None):
    """Mean policy lag, in learner updates, of a trajectory when the learner takes it.

    Little's law reading: lag ~ (trajectories alive in the loop) / b.
      actor-bound (P <= C):  n_roll / b + (b - 1) / (2 b), n_roll = N t_roll / (t_roll + t_sync)
                             (an underestimate close to saturation, where the queue builds up)
      learner-bound, policy="block":  (N + Q) / b
                             N actors, each holding a finished trajectory while blocked, plus Q queued
      learner-bound, policy="credit": min(K, N + Q) / b
                             a credit is taken BEFORE the rollout and returned when the learner takes it;
                             credits are held by trajectories in flight or queued, not by actors
    A mean-field estimate, checked against the simulation (test_throughput.py), not a theorem.
    """
    cap = consumption_capacity(b, m, s_L)
    p = production_rate(n_actors, m, t_roll, t_sync)
    if p <= cap:
        n_roll = n_actors * t_roll / actor_cycle(t_roll, t_sync)
        return n_roll / b + (b - 1) / (2 * b)
    if policy == "block":
        if queue_cap is None:
            return math.inf  # unbounded queue: the lag grows without limit
        alive = n_actors + queue_cap
    elif policy == "credit":
        alive = n_actors + (queue_cap or 0) if credits is None else credits
        if queue_cap is not None:
            alive = min(alive, n_actors + queue_cap)
    else:
        raise ValueError(policy)
    return alive / b


def credit_throughput_ceiling(credits, m, t_roll, t_sync):
    """Upper bound on steps/s when at most `credits` trajectories may be alive: K m / (t_sync + t_roll)."""
    return credits * m / actor_cycle(t_roll, t_sync)


def credits_for_lag(target_lag, b):
    """Largest number of credits K whose learner-bound lag K / b stays at or under `target_lag` updates."""
    return math.floor(b * target_lag + 1e-9)


def replay_ratio(n_actors, m, t_roll, t_sync, b, s_L):
    """Times each fresh step is consumed on average if the learner never waits (>= 1 means reuse)."""
    return consumption_capacity(b, m, s_L) / production_rate(n_actors, m, t_roll, t_sync)


def cost_per_million_steps(price_per_hour_total, steps_per_s):
    """Money per 10^6 environment steps for a given hourly price of the whole loop."""
    return price_per_hour_total / 3600.0 / steps_per_s * 1e6
