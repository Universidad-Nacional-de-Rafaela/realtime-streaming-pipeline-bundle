#!/bin/bash
# Wait for Cassandra to be ready
echo "Waiting for Cassandra to be ready..."
until cqlsh cassandra -e "describe cluster" > /dev/null 2>&1; do
  echo "Cassandra is unavailable - sleeping"
  sleep 5
done

echo "Cassandra is ready - executing schema initialization"
cqlsh cassandra -f /schema.cql
echo "Schema initialization complete"
