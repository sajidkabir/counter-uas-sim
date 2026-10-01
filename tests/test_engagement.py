"""The full chain: nothing is intercepted before it is detected."""

from counter_uas_sim.engagement import default_scenario, run_engagement


def test_demo_engagement_intercepts():
    result = run_engagement(default_scenario())
    assert result.outcome == "intercepted"
    assert result.intercepted
    assert result.miss_distance_m <= 15.0


def test_no_intercept_before_detection():
    result = run_engagement(default_scenario())
    assert result.detection_time_s is not None
    assert result.launch_time_s >= result.detection_time_s
    assert result.intercept_time_s >= result.detection_time_s
    assert "DETECTED" in result.event_log[0]
    launch_lines = [line for line in result.event_log if "LAUNCH" in line]
    assert len(launch_lines) == 1
