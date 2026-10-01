"""Example: one full engagement, detection to intercept, with the event log."""

from counter_uas_sim import default_scenario, run_engagement

result = run_engagement(default_scenario())
for line in result.event_log:
    print(line)
print(f"Outcome: {result.outcome}")
print(f"Miss distance: {result.miss_distance_m:.1f} m")
print(f"Intercept time: {result.intercept_time_s:.1f} s")
