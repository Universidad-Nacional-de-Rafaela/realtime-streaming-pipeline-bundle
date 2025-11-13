# 🎤 Speech para Alumnos - Pipeline de Streaming en Tiempo Real

---

## 📢 **INTRODUCCIÓN**

Buenos días/tardes. Hoy vamos a explorar juntos un **pipeline de procesamiento de datos en tiempo real**, una arquitectura fundamental en la industria moderna para manejar datos que se generan continuamente.

¿Han escuchado hablar de Netflix analizando qué ven en tiempo real? ¿O Uber procesando millones de viajes simultáneamente? ¿O sensores IoT enviando datos de temperatura constantemente? Todos estos sistemas utilizan arquitecturas similares a la que veremos hoy.

---

## 🎯 **¿QUÉ VAMOS A CONSTRUIR?**

Vamos a simular un sistema de **monitoreo de sensores IoT** que:
- Genera lecturas de temperatura y humedad
- Las procesa en tiempo real
- Las valida y transforma
- Las almacena para consultas posteriores

**La gran diferencia con sistemas tradicionales:** No esperamos a acumular datos para procesarlos al final del día (batch processing). Aquí procesamos **cada evento en el momento en que llega**.

---

## 🏗️ **ARQUITECTURA DEL SISTEMA**

Nuestro pipeline tiene 5 componentes principales. Voy a explicar cada uno:

### **1. Kafka + Zookeeper** 🚀
**¿Qué es?** Un sistema de mensajería distribuido (message broker).

**¿Para qué sirve?**
- Actúa como una **cola de mensajes** entre productores y consumidores
- Desacopla los componentes: el productor no necesita saber quién consume los datos
- Funciona como un buffer: si Spark se cae, los mensajes se quedan en Kafka esperando
- **Alta throughput**: puede manejar millones de mensajes por segundo

**Analogía:** Piensen en Kafka como un buzón inteligente. Los productores dejan mensajes (cartas), y los consumidores las recogen cuando están listos. Si el consumidor no está, las cartas esperan.

**Zookeeper:** Es el coordinador de Kafka. Mantiene la metadata y coordina los brokers.

---

### **2. Productor de Datos (Python)** 📊
**¿Qué es?** Un script Python que simula sensores IoT.

**¿Qué hace?**
- Genera 5 eventos por segundo (cada 200ms)
- Cada evento contiene:
  - `event_id`: identificador único
  - `device_id`: ID del sensor (sensor-1 a sensor-50)
  - `ts`: timestamp
  - `temperature_c`: temperatura en Celsius (18-32°C)
  - `humidity_pct`: humedad en porcentaje (20-80%)

**Ejemplo de evento:**
```json
{
  "event_id": "1729107123456-7891",
  "device_id": "sensor-23",
  "ts": "2025-10-16T17:25:23.456000",
  "temperature_c": 24.57,
  "humidity_pct": 62.34
}
```

**En la vida real:** Estos serían sensores físicos enviando datos desde fábricas, ciudades inteligentes, hospitales, etc.

---

### **3. Apache Spark Structured Streaming** ⚡
**¿Qué es?** El motor de procesamiento en tiempo real.

**¿Qué hace?**
1. **Lee** eventos desde el topic de Kafka (`sensors.events`)
2. **Transforma** los datos:
   - Normaliza el device_id a lowercase
   - Convierte tipos de datos (strings a float, etc.)
   - Parsea timestamps
3. **Valida** los datos:
   - Rechaza eventos con campos vacíos
   - Rechaza eventos con valores None o inválidos
4. **Escribe** los datos validados en Cassandra

**Concepto clave: Micro-batches**
Spark no procesa evento por evento. Agrupa eventos en **micro-batches** pequeños (ej: 2 segundos de datos) y los procesa juntos. Esto es más eficiente que procesar uno a uno.

**¿Por qué Spark?**
- Procesamiento distribuido (puede escalar a múltiples máquinas)
- APIs de alto nivel (fácil de programar)
- Tolerancia a fallos
- Integración con todo el ecosistema big data

---

### **4. Apache Cassandra** 💾
**¿Qué es?** Una base de datos NoSQL distribuida.

**¿Por qué Cassandra y no PostgreSQL?**
- **Alta disponibilidad**: no hay single point of failure
- **Escalabilidad lineal**: agregar nodos aumenta capacidad proporcionalmente
- **Escrituras muy rápidas**: optimizada para inserciones masivas
- **Modelo de datos flexible**: ideal para series temporales

**Nuestro schema:**
```sql
CREATE TABLE rt.sensor_readings (
  event_id text PRIMARY KEY,
  device_id text,
  ts timestamp,
  temperature_c double,
  humidity_pct double
);
```

**Explicación:**
- `event_id` es la PRIMARY KEY: cada evento es único
- Cassandra distribuye datos basándose en la PRIMARY KEY
- Perfecta para insert-heavy workloads (como datos de sensores)

---

### **5. Apache Airflow** 📅
**¿Qué es?** Una plataforma de orquestación de workflows.

**¿Para qué la usamos?**
- **Monitoreo**: ejecuta checks de salud de la infraestructura
- **Scheduling**: tareas programadas (nuestro DAG corre diariamente)
- **Alertas**: puede notificar si algo falla

**Nuestro DAG:**
- Verifica que Cassandra esté respondiendo correctamente
- Se ejecuta todos los días a las 00:00
- Si falla, puede reintentarlo o alertar al equipo

**En producción:** Airflow también se usa para:
- Entrenar modelos de ML periódicamente
- Generar reportes
- Ejecutar backfills de datos históricos

---

## 🔄 **FLUJO DE DATOS COMPLETO**

Ahora conectemos todas las piezas. Este es el journey de un evento:

```
┌─────────────────┐
│  1. PRODUCTOR   │  Genera evento JSON cada 200ms
│   (Python)      │
└────────┬────────┘
         │
         ↓ (envía a Kafka via network)
┌─────────────────┐
│   2. KAFKA      │  Almacena mensaje en topic "sensors.events"
│   (Topic)       │  El mensaje espera ser consumido
└────────┬────────┘
         │
         ↓ (Spark lee continuamente)
┌─────────────────┐
│   3. SPARK      │  Lee micro-batch desde Kafka
│   (Streaming)   │  ↓
│                 │  Aplica normalize_record():
│                 │    - event_id → strip()
│                 │    - device_id → lowercase
│                 │    - temperature_c → float
│                 │    - humidity_pct → float
│                 │  ↓
│                 │  Aplica is_valid():
│                 │    - ¿campos no vacíos?
│                 │    - ¿valores no None?
│                 │  ↓
│                 │  Convierte tipos Spark:
│                 │    - ts → timestamp
│                 │    - temperature_c → double
│                 │    - humidity_pct → double
└────────┬────────┘
         │
         ↓ (escribe a Cassandra)
┌─────────────────┐
│  4. CASSANDRA   │  INSERT INTO rt.sensor_readings
│   (Database)    │  Datos persistidos y consultables
└─────────────────┘
         │
         ↓ (Airflow monitorea)
┌─────────────────┐
│  5. AIRFLOW     │  Verifica salud de Cassandra
│  (Monitoring)   │  Alerta si hay problemas
└─────────────────┘
```

**Tiempos aproximados:**
- Productor → Kafka: **< 5ms**
- Kafka → Spark (micro-batch): **2-5 segundos**
- Spark → Cassandra: **< 100ms**
- **Latencia end-to-end: ~3-5 segundos**

En sistemas reales optimizados, esto puede bajar a sub-segundo.

---

## 🚀 **PASO A PASO DE LA DEMOSTRACIÓN**

Ahora vamos a verlo en acción. Voy a guiarlos paso a paso:

### **PASO 1: Levantar la Infraestructura**

```bash
docker compose up -d
```

**¿Qué sucede aquí?**
- Docker Compose lee el archivo `docker-compose.yml`
- Crea una red privada para que los contenedores se comuniquen
- Levanta 6 contenedores:
  1. **zookeeper**: coordinador de Kafka
  2. **kafka**: message broker
  3. **cassandra**: base de datos
  4. **spark**: motor de procesamiento
  5. **airflow-webserver**: UI web de Airflow
  6. **airflow-scheduler**: scheduler de Airflow

**Tiempo de inicio:** 1-2 minutos (Cassandra es el más lento en iniciar)

---

### **PASO 2: Inicializar Kafka y Cassandra**

```bash
./scripts/init.sh
```

**¿Qué hace este script?**
1. **Espera** a que Kafka esté listo (hace polling hasta que responda)
2. **Crea el topic** `sensors.events` en Kafka
3. **Espera** a que Cassandra esté lista
4. **Carga el schema** (crea el keyspace `rt` y la tabla `sensor_readings`)

**¿Por qué este paso?**
Los contenedores pueden estar "UP" pero no listos para recibir conexiones. Este script asegura que todo esté realmente funcional antes de empezar.

---

### **PASO 3: Ejecutar el Productor**

```bash
python app/producer/kafka_producer.py
```

**¿Qué verán?**
```
Producing to topic sensors.events at localhost:29092 ... Ctrl+C to stop
```

**¿Qué está pasando internamente?**
1. El productor se conecta a Kafka en el puerto 29092 (puerto externo)
2. Entra en un loop infinito:
   ```python
   while True:
       evt = make_event()          # Genera datos aleatorios
       producer.send(TOPIC, evt)   # Envía a Kafka
       time.sleep(0.2)             # Espera 200ms
   ```
3. Kafka confirma la recepción (acks="all")
4. El mensaje queda guardado en el topic

**Configuraciones importantes del productor:**
- `acks="all"`: espera confirmación de todos los brokers (más seguro)
- `enable_idempotence=True`: evita duplicados
- `retries=3`: reintenta si falla
- `linger_ms=50`: agrupa mensajes para eficiencia

---

### **PASO 4: Observar Spark Procesando**

```bash
docker logs -f realtime_streaming_pipeline_bundle-spark-1
```

**¿Qué verán en los logs?**
```
25/10/16 17:30:34 INFO KafkaSourceProvider: Kafka version: 3.4.1
25/10/16 17:30:35 INFO ConsumerConfig: bootstrap.servers = [kafka:9092]
25/10/16 17:30:38 INFO MicroBatchExecution: Streaming query made progress:
  {
    "batchId" : 0,
    "numInputRows" : 25,
    "processedRowsPerSecond" : 5.2
  }
```

**Explicación:**
- **KafkaSourceProvider**: Spark se conectó a Kafka
- **ConsumerConfig**: configuración del consumer (grupo, offsets, etc.)
- **MicroBatchExecution**: procesa micro-batches continuamente
- **numInputRows**: cuántos eventos procesó en ese batch
- **processedRowsPerSecond**: throughput actual

**Concepto clave: Checkpointing**
Spark guarda su progreso en `/tmp/chk/sensors`. Si Spark se cae y se reinicia, puede continuar desde donde quedó sin reprocesar datos.

---

### **PASO 5: Verificar Datos en Cassandra**

```bash
docker exec -it realtime_streaming_pipeline_bundle-cassandra-1 cqlsh
```

Esto abre una shell interactiva de Cassandra. Luego ejecutamos:

```sql
SELECT * FROM rt.sensor_readings LIMIT 5;
```

**¿Qué verán?**
```
 event_id              | device_id  | humidity_pct | temperature_c | ts
-----------------------+------------+--------------+---------------+---------
 1729107123456-7891    | sensor-23  |        62.34 |         24.57 | 2025-...
 1729107123657-3421    | sensor-08  |        45.12 |         28.91 | 2025-...
 ...
```

**Pregunta para reflexionar:** ¿Notaron que el orden puede parecer aleatorio? Esto es porque Cassandra distribuye datos basándose en el hash de la PRIMARY KEY, no por tiempo de inserción.

**Otras queries interesantes:**
```sql
-- Contar eventos totales
SELECT COUNT(*) FROM rt.sensor_readings;

-- Últimos eventos (limitado, no ordenado)
SELECT * FROM rt.sensor_readings LIMIT 10;

-- Buscar un sensor específico
SELECT * FROM rt.sensor_readings WHERE device_id = 'sensor-23' ALLOW FILTERING;
```

**Nota sobre ALLOW FILTERING:** En producción evitaríamos esto. Es ineficiente porque Cassandra escanea todos los nodos. Lo correcto sería incluir `device_id` en la PRIMARY KEY si lo vamos a consultar frecuentemente.

---

### **PASO 6: Ver Mensajes Raw en Kafka (Opcional)**

```bash
docker exec realtime_streaming_pipeline_bundle-kafka-1 \
  kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensors.events \
  --from-beginning \
  --max-messages 3
```

**¿Qué verán?**
```json
{"event_id":"1729...","device_id":"sensor-23","ts":"2025-...","temperature_c":24.57,"humidity_pct":62.34}
{"event_id":"1729...","device_id":"sensor-08","ts":"2025-...","temperature_c":28.91,"humidity_pct":45.12}
```

**Esto muestra:** Los mensajes tal como están almacenados en Kafka, antes de cualquier procesamiento.

---

### **PASO 7: Explorar Airflow UI**

Abrir navegador: **http://localhost:8080**

**Login:**
- Usuario: `admin`
- Contraseña: `admin`

**¿Qué verán?**
- Dashboard principal con el DAG `sanity_checks`
- Graph view: visualización del DAG
- Grid view: historial de ejecuciones
- Logs de cada task

**Activar el DAG:**
Hagan click en el toggle para activarlo. Verán que se ejecuta diariamente.

**Explorar una ejecución:**
- Click en una ejecución (verde = success, rojo = failed)
- Ver logs de la task `cassandra_check`
- Logs mostrarán "Cassandra OK" si todo funciona

---

## 🧪 **EXPERIMENTOS PARA PROFUNDIZAR**

### **Experimento 1: Resiliencia de Kafka**

**Objetivo:** Demostrar que Kafka actúa como buffer.

**Pasos:**
1. El productor está corriendo y enviando datos
2. Detenemos Spark: `docker stop realtime_streaming_pipeline_bundle-spark-1`
3. Esperamos 30 segundos (el productor sigue enviando a Kafka)
4. Reiniciamos Spark: `docker start realtime_streaming_pipeline_bundle-spark-1`
5. Observamos los logs de Spark

**¿Qué verán?**
Spark procesa un batch grande con todos los mensajes acumulados. **¡No se perdió ningún dato!**

**Lección:** Kafka desacopla productor y consumidor. El sistema es resiliente a fallos temporales.

---

### **Experimento 2: Validación de Datos**

**Objetivo:** Ver cómo Spark rechaza datos inválidos.

**Modificar el productor:**
```python
# En kafka_producer.py, dentro del loop while True:
if random.random() < 0.1:  # 10% de eventos inválidos
    evt = {
        "event_id": "",  # Inválido: vacío
        "device_id": "sensor-99",
        "ts": "2025-01-01T00:00:00",
        "temperature_c": None,  # Inválido: None
        "humidity_pct": 50.0
    }
```

**Ejecutar y observar:**
- Ver logs de Spark: algunos batches procesan menos eventos
- Consultar Cassandra: los eventos inválidos NO aparecen

**Lección:** La validación en Spark protege la calidad de datos en Cassandra.

---

### **Experimento 3: Escalabilidad del Productor**

**Objetivo:** Ver cómo el sistema maneja más carga.

**Modificar la frecuencia:**
```python
# En kafka_producer.py, cambiar:
time.sleep(0.2)  # Original: 5 eventos/seg
time.sleep(0.02)  # Nuevo: 50 eventos/seg
```

**Ejecutar múltiples productores en paralelo:**
```bash
# Terminal 1
python app/producer/kafka_producer.py

# Terminal 2
python app/producer/kafka_producer.py

# Terminal 3
python app/producer/kafka_producer.py
```

**Observar:**
- Logs de Spark: `processedRowsPerSecond` aumenta
- Kafka maneja la carga sin problemas
- Cassandra recibe más escrituras

**Lección:** La arquitectura puede escalar horizontalmente agregando más productores.

---

### **Experimento 4: Monitoreo en Tiempo Real**

**Objetivo:** Ver el crecimiento de datos en vivo.

**Ejecutar en una terminal:**
```bash
watch -n 2 'docker exec realtime_streaming_pipeline_bundle-cassandra-1 \
  cqlsh -e "SELECT COUNT(*) FROM rt.sensor_readings;"'
```

**¿Qué verán?**
Cada 2 segundos, el contador aumenta:
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

**Lección:** Visualización del pipeline funcionando end-to-end en tiempo real.

---

## 💡 **CONCEPTOS CLAVE PARA LLEVARSE**

### **1. Stream Processing vs Batch Processing**

**Batch (tradicional):**
- Procesa datos acumulados periódicamente (cada hora, día)
- Latencia alta (esperas hasta el próximo batch)
- Ejemplo: reporte de ventas diario

**Stream (moderno):**
- Procesa datos continuamente a medida que llegan
- Latencia baja (segundos o menos)
- Ejemplo: detección de fraude en tarjetas de crédito

**¿Cuándo usar cada uno?**
- **Batch**: reportes históricos, análisis no urgentes, modelos ML que entrenan con datos completos
- **Stream**: monitoreo en tiempo real, alertas, dashboards live, recomendaciones instantáneas

---

### **2. Desacoplamiento con Message Queues**

**Sin Kafka:**
```
Productor → (conexión directa) → Spark → Cassandra
```
Problemas:
- Si Spark cae, el productor debe manejar reintentos
- Si Spark está lento, el productor se bloquea
- Difícil agregar nuevos consumidores

**Con Kafka:**
```
Productor → Kafka → Spark → Cassandra
                  ↘ Otro Consumer (ej: Analytics)
```
Ventajas:
- Productor solo se preocupa de enviar a Kafka
- Kafka hace buffering si Spark está lento
- Múltiples consumidores pueden leer el mismo stream
- Componentes evolucionan independientemente

---

### **3. Data Validation & Quality**

**Principio: "Garbage In, Garbage Out"**

Si guardamos datos inválidos en Cassandra:
- Queries fallan o retornan resultados incorrectos
- Dashboards muestran información errónea
- Modelos de ML aprenden de datos malos

**Nuestra estrategia:**
1. **Normalización**: convertir a formatos estándar (lowercase, trim, etc.)
2. **Validación**: rechazar datos con campos faltantes o inválidos
3. **Type casting**: asegurar tipos de datos correctos

**En producción, agregar:**
- Validación de rangos (temperatura entre -50 y 60°C)
- Deduplicación (evitar eventos duplicados)
- Esquemas formales (Avro, Protobuf)

---

### **4. Tolerancia a Fallos**

**¿Qué puede fallar?**
- Kafka: broker puede caer
- Spark: worker puede quedarse sin memoria
- Cassandra: nodo puede perder conexión
- Network: particiones de red

**¿Cómo el sistema se protege?**
- **Kafka**: replica datos en múltiples brokers
- **Spark**: checkpointing + exactly-once semantics
- **Cassandra**: replicación + eventual consistency
- **Contenedores**: Docker restart policies

**En producción:**
- Múltiples brokers de Kafka (3-5)
- Cluster de Spark (1 master, N workers)
- Ring de Cassandra (3+ nodos)
- Monitoreo con Prometheus/Grafana
- Alertas automáticas (PagerDuty, Slack)

---

### **5. Escalabilidad**

**¿Cómo escalar cada componente?**

**Kafka:**
- Agregar más brokers
- Aumentar particiones del topic (paralelismo)
- Cada partición puede ser leída por un consumer diferente

**Spark:**
- Agregar más workers al cluster
- Aumentar `spark.sql.shuffle.partitions`
- Usar más memoria por executor

**Cassandra:**
- Agregar más nodos al ring
- Datos se redistribuyen automáticamente
- Escrituras y lecturas se distribuyen

**Resultado:** Escalabilidad casi lineal. 2x recursos ≈ 2x throughput.

---

## 🎓 **PREGUNTAS PARA REFLEXIONAR**

Les dejo estas preguntas para que piensen:

1. **Arquitectura:**
   - ¿Qué pasaría si eliminamos Kafka y conectamos el productor directamente a Spark?
   - ¿Podríamos reemplazar Cassandra con PostgreSQL? ¿Qué ventajas/desventajas?

2. **Data Quality:**
   - ¿Qué otras validaciones agregarían a los datos de sensores?
   - ¿Deberíamos guardar los eventos inválidos en algún lado? ¿Para qué?

3. **Escalabilidad:**
   - ¿Cómo escalaríamos para 1 millón de sensores enviando datos por segundo?
   - ¿Qué componente sería el cuello de botella primero?

4. **Casos de Uso:**
   - ¿Qué modificaciones harían para procesar tweets en tiempo real?
   - ¿Cómo adaptarían esto para un sistema de monitoreo de servidores?

5. **Evolución:**
   - ¿Dónde agregarían machine learning? (ej: detectar anomalías en temperatura)
   - ¿Cómo implementarían un dashboard en tiempo real con estos datos?

---

## 📚 **RECURSOS PARA SEGUIR APRENDIENDO**

### **Documentación Oficial:**
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Cassandra Documentation](https://cassandra.apache.org/doc/latest/)
- [Airflow Documentation](https://airflow.apache.org/docs/)

### **Tutoriales y Cursos:**
- Kafka: "Kafka: The Definitive Guide" (libro)
- Spark: "Learning Spark" (libro, O'Reilly)
- Cassandra: DataStax Academy (cursos gratuitos)

### **Proyectos para Practicar:**
1. Agregar un dashboard con Streamlit o Grafana
2. Implementar alertas (ej: si temperatura > 30°C)
3. Agregar un modelo ML que prediga fallos de sensores
4. Procesar tweets en tiempo real y hacer análisis de sentimiento
5. Crear un sistema de monitoreo de logs de aplicaciones

---

## 🎯 **CONCLUSIÓN**

Hoy vieron:
✅ Una arquitectura moderna de streaming end-to-end
✅ Cómo 5 tecnologías (Kafka, Spark, Cassandra, Airflow, Docker) trabajan juntas
✅ Los conceptos de desacoplamiento, validación, tolerancia a fallos
✅ Un sistema escalable desde 5 eventos/seg hasta millones

**Lo más importante:** Esta NO es solo una demo académica. Es una arquitectura real utilizada por empresas como:
- **Uber**: tracking de viajes en tiempo real
- **Netflix**: análisis de visualización y recomendaciones
- **LinkedIn**: feed de actividad en tiempo real
- **Spotify**: recomendaciones de música

**Próximos pasos:**
1. Ejecuten la demo ustedes mismos
2. Experimenten con las modificaciones propuestas
3. Piensen en un proyecto personal usando esta arquitectura
4. Profundicen en el componente que más les interesó

**¡Estoy disponible para preguntas!**

---

## 🛠️ **COMANDOS DE REFERENCIA RÁPIDA**

```bash
# Iniciar todo
docker compose up -d
./scripts/init.sh

# Ejecutar productor
python app/producer/kafka_producer.py

# Ver logs de Spark
docker logs -f realtime_streaming_pipeline_bundle-spark-1

# Conectar a Cassandra
docker exec -it realtime_streaming_pipeline_bundle-cassandra-1 cqlsh

# Ver mensajes en Kafka
docker exec realtime_streaming_pipeline_bundle-kafka-1 \
  kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic sensors.events \
  --from-beginning \
  --max-messages 5

# Monitoreo en tiempo real
watch -n 2 'docker exec realtime_streaming_pipeline_bundle-cassandra-1 \
  cqlsh -e "SELECT COUNT(*) FROM rt.sensor_readings;"'

# Detener todo
docker compose down -v
```

---

**¡Gracias y éxitos en sus proyectos!** 🚀

