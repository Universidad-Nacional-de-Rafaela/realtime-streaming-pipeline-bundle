# 🎓 Demostración para Estudiantes - Pipeline de Streaming en Tiempo Real

## 📋 Qué Verán los Estudiantes

Este documento muestra exactamente qué observarán los estudiantes en cada paso del pipeline.

---

## 🚀 **PASO 1: Iniciar los Servicios**

```bash
docker compose up -d
```

### Lo que verán:
```
✔ Container realtime_streaming_pipeline_bundle-zookeeper-1       Started
✔ Container realtime_streaming_pipeline_bundle-cassandra-1       Started
✔ Container realtime_streaming_pipeline_bundle-kafka-1           Started
✔ Container realtime_streaming_pipeline_bundle-spark-1           Started
✔ Container realtime_streaming_pipeline_bundle-airflow-webserver-1  Started
✔ Container realtime_streaming_pipeline_bundle-airflow-scheduler-1  Started
```

**Explicación:** 6 contenedores Docker se inician, cada uno ejecutando un componente del pipeline.

---

## 🔧 **PASO 2: Inicializar el Pipeline**

```bash
./scripts/init.sh
```

### Lo que verán:
```
🚀 Initializing Realtime Streaming Pipeline...
⏳ Waiting for Kafka to be ready...
✅ Kafka is ready
📝 Creating Kafka topic 'sensors.events'...
Created topic sensors.events.
✅ Kafka topic created
⏳ Waiting for Cassandra to be ready...
✅ Cassandra is ready
📝 Loading Cassandra schema...
✅ Cassandra schema loaded

🎉 Pipeline initialized successfully!
```

**Explicación:** El script espera a que los servicios estén listos y configura automáticamente:
- El topic de Kafka donde se enviarán los mensajes
- El schema de Cassandra donde se guardarán los datos procesados

---

## 📊 **PASO 3: Ejecutar el Productor**

```bash
python app/producer/kafka_producer.py
```

### Lo que verán:
```
Producing to topic sensors.events at localhost:29092 ... Ctrl+C to stop
```

**¿Qué está pasando?**
El productor está generando 5 eventos por segundo con datos simulados de sensores IoT:

```json
{
  "event_id": "1729107123456-7891",
  "device_id": "sensor-23",
  "ts": "2025-10-16T17:25:23.456000",
  "temperature_c": 24.57,
  "humidity_pct": 62.34
}
```

**Nota:** No verán cada evento individual impreso en pantalla (para no saturar la consola), pero el productor está enviando eventos continuamente a Kafka.

---

## 🔍 **PASO 4: Ver Spark Procesando en Tiempo Real**

```bash
docker logs -f realtime_streaming_pipeline_bundle-spark-1
```

### Lo que verán (logs de Spark):

```
25/10/16 17:30:30 INFO BlockManager: Initialized BlockManager
25/10/16 17:30:33 WARN ResolveWriteToStream: spark.sql.adaptive.enabled 
                   is not supported in streaming DataFrames
25/10/16 17:30:34 INFO KafkaSourceProvider: Kafka version: 3.4.1
25/10/16 17:30:35 INFO ConsumerConfig: ConsumerConfig values:
	bootstrap.servers = [kafka:9092]
	group.id = spark-kafka-source-...
25/10/16 17:30:36 INFO AbstractCoordinator: [Consumer] Discovered group coordinator
25/10/16 17:30:37 INFO KafkaSource: Initial offsets: 
	{"sensors.events":{"0":0}}
25/10/16 17:30:38 INFO MicroBatchExecution: Streaming query made progress:
	{
	  "batchId" : 0,
	  "numInputRows" : 25,
	  "processedRowsPerSecond" : 5.2
	}
```

**Explicación:** Spark está:
1. Conectándose a Kafka
2. Leyendo eventos del topic `sensors.events`
3. Procesando micro-batches (lotes pequeños de datos)
4. Aplicando transformaciones (normalización, validación)
5. Escribiendo en Cassandra

---

## 💾 **PASO 5: Ver los Datos Guardados en Cassandra**

```bash
docker exec -it realtime_streaming_pipeline_bundle-cassandra-1 cqlsh
```

Luego ejecutar:
```sql
SELECT * FROM rt.sensor_readings LIMIT 5;
```

### Lo que verán:

```
 event_id              | device_id  | humidity_pct | temperature_c | ts
-----------------------+------------+--------------+---------------+---------------------------------
 1729107123456-7891    | sensor-23  |        62.34 |         24.57 | 2025-10-16 17:25:23.456000+0000
 1729107123657-3421    | sensor-08  |        45.12 |         28.91 | 2025-10-16 17:25:23.657000+0000
 1729107123858-9012    | sensor-45  |        71.28 |         21.34 | 2025-10-16 17:25:23.858000+0000
 1729107124059-5643    | sensor-12  |        58.76 |         26.45 | 2025-10-16 17:25:24.059000+0000
 1729107124260-8234    | sensor-31  |        53.89 |         23.12 | 2025-10-16 17:25:24.260000+0000

(5 rows)
```

**Explicación:** Los datos procesados están siendo almacenados en tiempo real. Cada fila representa:
- **event_id**: Identificador único del evento
- **device_id**: Sensor que generó la lectura
- **humidity_pct**: Humedad en porcentaje
- **temperature_c**: Temperatura en Celsius
- **ts**: Timestamp del evento

---

## 📈 **PASO 6: Verificar Mensajes en Kafka (Opcional)**

```bash
docker exec realtime_streaming_pipeline_bundle-kafka-1 \
  kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensors.events \
  --from-beginning \
  --max-messages 3
```

### Lo que verán:

```json
{"event_id":"1729107123456-7891","device_id":"sensor-23","ts":"2025-10-16T17:25:23.456000","temperature_c":24.57,"humidity_pct":62.34}
{"event_id":"1729107123657-3421","device_id":"sensor-08","ts":"2025-10-16T17:25:23.657000","temperature_c":28.91,"humidity_pct":45.12}
{"event_id":"1729107123858-9012","device_id":"sensor-45","ts":"2025-10-16T17:25:23.858000","temperature_c":21.34,"humidity_pct":71.28}
```

**Explicación:** Los mensajes raw (sin procesar) que están en el topic de Kafka antes de ser procesados por Spark.

---

## 🖥️ **PASO 7: Ver Airflow UI (Opcional)**

Abrir navegador en: **http://localhost:8080**

**Login:**
- Usuario: `admin`
- Contraseña: `admin`

### Lo que verán:
- Dashboard de Airflow con el DAG `sanity_checks`
- El DAG ejecuta un chequeo diario de la salud de Cassandra
- Lista de tareas y su estado (success/failed)
- Historial de ejecuciones

**Explicación:** Airflow se usa para monitoreo y orquestación. El DAG de ejemplo verifica que Cassandra esté respondiendo correctamente.

---

## 📊 **PASO 8: Monitorear el Flujo Completo**

Los estudiantes pueden ejecutar múltiples terminales en paralelo para ver todo el flujo:

### **Terminal 1:** Productor generando datos
```bash
python app/producer/kafka_producer.py
```

### **Terminal 2:** Spark procesando
```bash
docker logs -f realtime_streaming_pipeline_bundle-spark-1
```

### **Terminal 3:** Query a Cassandra cada 5 segundos
```bash
watch -n 5 'docker exec realtime_streaming_pipeline_bundle-cassandra-1 \
  cqlsh -e "SELECT COUNT(*) FROM rt.sensor_readings;"'
```

### Lo que verán en Terminal 3:
```
 count
-------
   125

 count
-------
   150

 count
-------
   175
```

**El contador aumenta cada 5 segundos**, demostrando que los datos fluyen continuamente por el pipeline.

---

## 🎯 **Conceptos que los Estudiantes Aprenden**

### 1. **Arquitectura de Microservicios**
- Cada componente (Kafka, Spark, Cassandra) corre en su propio contenedor
- Los servicios se comunican entre sí a través de una red Docker

### 2. **Stream Processing**
- Los datos se procesan en tiempo real, no en batch
- Spark procesa micro-batches continuamente

### 3. **Message Queuing**
- Kafka actúa como buffer entre productor y consumidor
- Desacoplamiento: el productor no necesita esperar a que Spark procese

### 4. **Data Validation & Transformation**
- Spark valida y normaliza datos antes de guardarlos
- Transformaciones: lowercase device_id, parsing de tipos, validación de campos

### 5. **Persistencia NoSQL**
- Cassandra almacena datos con alta disponibilidad
- Schema flexible para datos de sensores

### 6. **Orquestación con Airflow**
- Monitoreo automatizado de la infraestructura
- DAGs para tareas programadas

---

## 🧪 **Experimentos para Estudiantes**

### Experimento 1: ¿Qué pasa si detenemos el productor?
```bash
# Detener productor (Ctrl+C)
# Observar: Spark sigue corriendo, esperando nuevos datos
# Reiniciar productor: Spark continúa procesando sin perder datos
```

### Experimento 2: Modificar frecuencia del productor
```python
# En kafka_producer.py, cambiar:
time.sleep(0.2)  # Original: 5 eventos/seg
time.sleep(1.0)  # Nuevo: 1 evento/seg
```

### Experimento 3: Ver datos inválidos siendo filtrados
```python
# En kafka_producer.py, agregar evento inválido:
{
    "event_id": "",  # Inválido: vacío
    "device_id": "sensor-99",
    "ts": "2025-01-01T00:00:00",
    "temperature_c": None,  # Inválido: None
    "humidity_pct": 50.0
}
# Este evento será rechazado por la validación de Spark
```

### Experimento 4: Consultas SQL en Cassandra
```sql
-- Temperatura promedio por sensor
SELECT device_id, AVG(temperature_c) as avg_temp 
FROM rt.sensor_readings 
GROUP BY device_id;

-- Sensores con humedad alta
SELECT * FROM rt.sensor_readings 
WHERE humidity_pct > 70.0 
ALLOW FILTERING;

-- Últimos 10 eventos
SELECT * FROM rt.sensor_readings 
LIMIT 10;
```

---

## ⚠️ **Problemas Comunes que Pueden Ver**

### Problema 1: "Cannot connect to Kafka"
**Causa:** Kafka aún no está listo
**Solución:** Esperar 30 segundos y reintentar

### Problema 2: "No module named 'kafka'"
**Causa:** No instalaron las dependencias de Python
**Solución:** `pip install -r requirements.txt`

### Problema 3: No ven datos en Cassandra
**Causa:** El productor no está corriendo
**Solución:** Verificar que `kafka_producer.py` esté ejecutándose

---

## 🏁 **Resumen del Flujo de Datos**

```
1️⃣  Producer (Python)
    ↓ Genera eventos JSON cada 200ms
    
2️⃣  Kafka Topic (sensors.events)
    ↓ Almacena mensajes temporalmente
    
3️⃣  Spark Streaming
    ↓ Lee desde Kafka
    ↓ Aplica transformaciones (normalize_record)
    ↓ Valida datos (is_valid)
    ↓ Convierte tipos de datos
    
4️⃣  Cassandra (rt.sensor_readings)
    ✓ Datos persistidos y consultables
```

---

## 📚 **Recursos Adicionales para Estudiantes**

- Ver el código del productor: `app/producer/kafka_producer.py`
- Ver transformaciones de Spark: `app/spark/transforms.py`
- Ver el job de Spark: `app/spark/streaming_job.py`
- Ver tests unitarios: `app/spark/tests/test_transforms.py`
- Ver DAG de Airflow: `airflow/dags/sanity_checks_dag.py`

---

## 🎓 **Preguntas de Reflexión para Estudiantes**

1. ¿Qué ventajas tiene procesar datos en streaming vs batch?
2. ¿Por qué usamos Kafka como intermediario en vez de conectar directamente el productor con Spark?
3. ¿Qué pasaría si Cassandra se cae momentáneamente?
4. ¿Cómo escalaríamos este sistema para millones de eventos por segundo?
5. ¿Qué otras transformaciones podrían aplicarse a los datos de sensores?


