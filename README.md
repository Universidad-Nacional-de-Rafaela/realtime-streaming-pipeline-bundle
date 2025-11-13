# Realtime Streaming Pipeline (Demo)

A simple data streaming pipeline demo for educational purposes, showcasing how to build an end-to-end real-time data processing system.

## Architecture

```
Kafka Producer → Kafka Topic → Spark Streaming → Cassandra
                                                      ↓
                                          Airflow (monitoring)
```

**Data Flow:**
1. Python producer generates synthetic IoT sensor data (temperature & humidity)
2. Messages are published to Kafka topic `sensors.events`
3. Spark Structured Streaming reads, validates, and transforms data
4. Processed data is written to Cassandra
5. Airflow performs sanity checks on the infrastructure

## Stack
- **Kafka + Zookeeper** - Message broker for streaming data
- **Spark Structured Streaming** - Real-time data processing
- **Cassandra** - NoSQL database for storing sensor readings
- **Airflow** - Workflow orchestration and sanity checks
- **Docker Compose** - Container orchestration

## Prerequisites

- Docker 20+ and Docker Compose 1.29+
- Python 3.9+ (for running producer and tests locally)
- At least 4GB RAM available for Docker

## Quickstart

### 1. Start the services
```bash
docker compose up -d
```

Wait for all containers to start (this may take 1-2 minutes).

### 2. Initialize the pipeline
Run the automated setup script:
```bash
./scripts/init.sh
```

This will:
- Wait for Kafka and Cassandra to be ready
- Create the Kafka topic
- Load the Cassandra schema

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the producer
```bash
python app/producer/kafka_producer.py
```

The producer will start sending sensor events to Kafka (5 events/second). Press Ctrl+C to stop.

### 5. Verify data flow

**Check Spark logs:**
```bash
docker logs -f realtime_streaming_pipeline_bundle-spark-1
```

**Query Cassandra:**
```bash
docker exec -it realtime_streaming_pipeline_bundle-cassandra-1 cqlsh
```

Then run:
```sql
SELECT * FROM rt.sensor_readings LIMIT 5;
```

You should see sensor readings with timestamps, device IDs, temperature, and humidity data.

## Manual Setup (Alternative)

If you prefer to set up manually instead of using the init script:

1. **Start services:** `docker compose up -d`

2. **Create Kafka topic:**
```bash
docker exec realtime_streaming_pipeline_bundle-kafka-1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --create --topic sensors.events \
  --partitions 1 --replication-factor 1
```

3. **Load Cassandra schema:**
```bash
docker exec -i realtime_streaming_pipeline_bundle-cassandra-1 cqlsh < cassandra/schema.cql
```

## Services & Ports

| Service | Port | Access |
|---------|------|--------|
| Kafka (internal) | 9092 | From containers |
| Kafka (external) | 29092 | From host machine |
| Cassandra | 9042 | CQL native protocol |
| Airflow Web UI | 8080 | http://localhost:8080 (admin/admin) |
| Zookeeper | 2181 | Kafka coordination |

## Tests

Run unit tests for data transformations:
```bash
pytest app/spark/tests/test_transforms.py
```

## Troubleshooting

### Containers won't start
```bash
# Check container status
docker compose ps

# View logs for a specific service
docker compose logs spark
docker compose logs kafka
docker compose logs cassandra
```

### Kafka topic not found
```bash
# List all topics
docker exec realtime_streaming_pipeline_bundle-kafka-1 kafka-topics \
  --bootstrap-server localhost:9092 --list
```

### Cassandra connection refused
Cassandra takes ~30 seconds to start. Wait a bit and try again:
```bash
# Check if Cassandra is ready
docker exec realtime_streaming_pipeline_bundle-cassandra-1 cqlsh -e "DESCRIBE KEYSPACES"
```

### Spark job not processing data
1. Check if producer is running
2. Verify Kafka has messages:
```bash
docker exec realtime_streaming_pipeline_bundle-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensors.events --from-beginning --max-messages 5
```

### Reset everything
To start fresh:
```bash
docker compose down -v
docker compose up -d
./scripts/init.sh
```

## Project Structure

```
.
├── app/
│   ├── producer/
│   │   └── kafka_producer.py      # Generates sensor events
│   └── spark/
│       ├── streaming_job.py       # Main Spark streaming application
│       ├── transforms.py          # Data transformation logic
│       └── tests/
│           └── test_transforms.py # Unit tests
├── airflow/
│   ├── dags/
│   │   └── sanity_checks_dag.py   # Infrastructure health checks
│   └── requirements.txt           # Airflow dependencies
├── cassandra/
│   └── schema.cql                 # Database schema
├── scripts/
│   └── init.sh                    # Automated setup script
├── docker-compose.yml             # Service definitions
├── requirements.txt               # Python dependencies
└── README.md
```

## Learning Resources

This demo illustrates several important concepts:

- **Stream Processing**: Real-time data processing with Spark Structured Streaming
- **Message Queues**: Using Kafka as a buffer between producer and consumer
- **Data Validation**: Cleaning and validating streaming data
- **Data Persistence**: Storing processed data in Cassandra
- **Orchestration**: Using Airflow for monitoring and scheduling
- **Containerization**: Running a multi-service architecture with Docker

## Cleanup

Stop all services and remove volumes:
```bash
docker compose down -v
```
