from monitoring.run_monitors import MonitoringReport, format_freshness_alert_message, write_markdown


def test_format_freshness_alert_message_no_events():
    msg = format_freshness_alert_message(None, 24.0)
    assert "no events found" in msg.lower()
    assert "24.0" in msg


def test_write_markdown_handles_none_lag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report: MonitoringReport = {
        "freshness": {
            "max_event_ts": None,
            "lag_hours": None,
            "threshold_hours": 24.0,
            "status": "FAIL",
        },
        "anomaly": [],
        "alerts": [{"type": "freshness", "severity": "high", "message": "x"}],
    }
    p = write_markdown(report)
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert "Freshness" in text
