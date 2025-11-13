from app.spark.transforms import normalize_record, is_valid

def test_normalize_ok():
    rec = {"event_id": "1", "device_id": "Sensor-01", "ts": "2024-01-01T00:00:00Z", "temperature_c": "25.5", "humidity_pct": 40}
    out = normalize_record(rec)
    assert out["device_id"] == "sensor-01"
    assert out["temperature_c"] == 25.5
    assert is_valid(out) is True

def test_normalize_missing_fields():
    rec = {"event_id": "", "device_id": "", "ts": "", "temperature_c": None, "humidity_pct": None}
    out = normalize_record(rec)
    assert is_valid(out) is False
