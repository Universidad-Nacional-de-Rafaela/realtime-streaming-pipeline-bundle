CREATE KEYSPACE IF NOT EXISTS rt
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS rt.sensor_readings (
  event_id text PRIMARY KEY,
  device_id text,
  ts timestamp,
  temperature_c double,
  humidity_pct double
);
