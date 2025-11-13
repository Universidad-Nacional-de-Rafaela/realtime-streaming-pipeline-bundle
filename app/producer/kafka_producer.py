import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

TOPIC = "sensors.events"
BROKERS = "localhost:29092"

def make_event():
    return {
        "event_id": str(int(time.time() * 1000)) + "-" + str(random.randint(1000, 9999)),
        "device_id": f"sensor-{random.randint(1, 50)}",
        "ts": datetime.utcnow().isoformat(),
        "temperature_c": round(random.uniform(18, 32), 2),
        "humidity_pct": round(random.uniform(20, 80), 2),
    }

def main():
    producer = KafkaProducer(
        bootstrap_servers=BROKERS.split(","),
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        linger_ms=50,
        retries=3,
        enable_idempotence=True,
    )
    print(f"Producing to topic {TOPIC} at {BROKERS} ... Ctrl+C to stop")
    try:
        while True:
            evt = make_event()
            producer.send(TOPIC, value=evt)
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    main()
