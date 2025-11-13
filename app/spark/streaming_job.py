import json
from pyspark.sql import SparkSession, functions as F, types as T
from transforms import normalize_record, is_valid

KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC = "sensors.events"
CHECKPOINT = "/tmp/chk/sensors"
CASSANDRA_HOST = "cassandra"
KEYSPACE = "rt"
TABLE = "sensor_readings"

def main():
    spark = (
        SparkSession.builder
        .appName("SensorsStreaming")
        .config("spark.cassandra.connection.host", CASSANDRA_HOST)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    df_raw = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "latest")
        .load()
        .selectExpr("CAST(value AS STRING) AS json_str")
    )

    normalize_udf = F.udf(lambda s: normalize_record(json.loads(s)), T.MapType(T.StringType(), T.StringType()))
    valid_udf = F.udf(lambda m: is_valid(m), T.BooleanType())

    df_norm = df_raw.withColumn("rec", normalize_udf(F.col("json_str")))
    df_valid = df_norm.where(valid_udf(F.col("rec")))

    df = df_valid.select(
        F.col("rec")["event_id"].alias("event_id"),
        F.col("rec")["device_id"].alias("device_id"),
        F.to_timestamp(F.col("rec")["ts"]).alias("ts"),
        F.col("rec")["temperature_c"].cast("double").alias("temperature_c"),
        F.col("rec")["humidity_pct"].cast("double").alias("humidity_pct"),
    )

    (
        df.writeStream
        .format("org.apache.spark.sql.cassandra")
        .option("checkpointLocation", CHECKPOINT)
        .option("keyspace", KEYSPACE)
        .option("table", TABLE)
        .outputMode("append")
        .start()
        .awaitTermination()
    )

if __name__ == "__main__":
    main()
