from typing import Dict, Any

def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    out["event_id"] = str(rec.get("event_id", "")).strip()
    out["device_id"] = str(rec.get("device_id", "")).strip().lower()
    out["ts"] = str(rec.get("ts", ""))
    try:
        out["temperature_c"] = float(rec.get("temperature_c", 0.0))
    except Exception:
        out["temperature_c"] = None
    try:
        out["humidity_pct"] = float(rec.get("humidity_pct", 0.0))
    except Exception:
        out["humidity_pct"] = None
    return out

def is_valid(out: Dict[str, Any]) -> bool:
    if not out["event_id"] or not out["device_id"] or not out["ts"]:
        return False
    if out["temperature_c"] is None or out["humidity_pct"] is None:
        return False
    return True
