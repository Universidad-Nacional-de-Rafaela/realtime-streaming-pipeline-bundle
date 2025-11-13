#!/bin/bash
# Initialization script for the streaming pipeline
# This script waits for services to be ready and sets up Kafka topic and Cassandra schema

set -e

echo "🚀 Initializing Realtime Streaming Pipeline..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Wait for Kafka to be ready
echo -e "${YELLOW}⏳ Waiting for Kafka to be ready...${NC}"
max_attempts=30
attempt=0
until docker exec realtime_streaming_pipeline_bundle-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt+1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Kafka failed to start in time"
    exit 1
fi
echo -e "${GREEN}✅ Kafka is ready${NC}"

# Create Kafka topic
echo -e "${YELLOW}📝 Creating Kafka topic 'sensors.events'...${NC}"
docker exec realtime_streaming_pipeline_bundle-kafka-1 kafka-topics \
    --bootstrap-server localhost:9092 \
    --create --if-not-exists \
    --topic sensors.events \
    --partitions 1 \
    --replication-factor 1 || true
echo -e "${GREEN}✅ Kafka topic created${NC}"

# Wait for Cassandra to be ready
echo -e "${YELLOW}⏳ Waiting for Cassandra to be ready...${NC}"
attempt=0
until docker exec realtime_streaming_pipeline_bundle-cassandra-1 cqlsh -e "DESCRIBE KEYSPACES" &> /dev/null || [ $attempt -eq $max_attempts ]; do
    attempt=$((attempt+1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Cassandra failed to start in time"
    exit 1
fi
echo -e "${GREEN}✅ Cassandra is ready${NC}"

# Load Cassandra schema
echo -e "${YELLOW}📝 Loading Cassandra schema...${NC}"
docker exec -i realtime_streaming_pipeline_bundle-cassandra-1 cqlsh < cassandra/schema.cql
echo -e "${GREEN}✅ Cassandra schema loaded${NC}"

echo ""
echo -e "${GREEN}🎉 Pipeline initialized successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Install Python dependencies: pip install -r requirements.txt"
echo "  2. Run the producer: python app/producer/kafka_producer.py"
echo "  3. Check Spark logs: docker logs -f realtime_streaming_pipeline_bundle-spark-1"
echo "  4. Query Cassandra: docker exec -it realtime_streaming_pipeline_bundle-cassandra-1 cqlsh"
echo "     Then run: SELECT * FROM rt.sensor_readings LIMIT 5;"
echo ""


