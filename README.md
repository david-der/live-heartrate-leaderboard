## SOS 

```docker stop $(docker ps -aq)```

```bash -i <(curl -fsSL https://fiveonefour.com/install.sh) moose, aurora```

## Project Architecture

### Core Primitives

#### Data Models
- `RawAntHRPacket`: Initial heart rate data from ANT+ sensors (device_id, packet_count, ant_hr_packet)
- `ProcessedAntHRPacket`: Processed heart rate data with beat timing information (device_id, previous_beat_time, last_beat_time, calculated_heart_rate, heart_beat_count)
- `UnifiedHRPacket`: Standardized heart rate data with user context (user_id, user_name, device_id, hr_timestamp_seconds, hr_value, rr_interval_ms, processed_timestamp)

#### APIs
- `getLatestUserHeartRates` (TypeScript): Retrieves current heart rate data for users
- `getUserHeartRateStats` (TypeScript): Provides statistical analysis of user heart rates
- `get_group_hr_by_second` (Python): Aggregates group heart rate data per second
- `getHR`: REST endpoint for querying heart rate data by timestamp

#### Functions
- `raw_to_processed`: Transforms raw ANT+ packets into processed heart rate data
- `processed_to_unified`: Enriches processed data with user information into unified format
- `aggregated_per_second`: Computes per-second heart rate aggregates

#### Scripts
- Data Generation (`generate_data/`): Tools for generating test heart rate data
- Data Ingestion (`ingest-foo/`): Scripts for ingesting heart rate data into the system

### Data Flow

The system follows a multi-stage streaming pipeline:

1. **Data Ingestion**
   ```
   ANT+ Heart Rate Sensors → RawAntHRPacket Stream
   ```

2. **Processing Pipeline**
   ```
   RawAntHRPacket → raw_to_processed → ProcessedAntHRPacket
   ProcessedAntHRPacket → processed_to_unified → UnifiedHRPacket
   UnifiedHRPacket → aggregated_per_second → per_second_heart_rate_aggregate
   ```

3. **Data Access**
   ```
   UnifiedHRPacket ─┬→ getLatestUserHeartRates
                    ├→ getUserHeartRateStats
                    └→ get_group_hr_by_second
   ```

Each stage enriches the data:
- Raw stage: Captures basic device data
- Processing stage: Calculates heart rate metrics
- Unified stage: Adds user context
- Aggregation stage: Computes group statistics

### Data Storage

All data is persisted in Clickhouse tables that mirror the streaming topics:

#### Raw Tables
- `raw_ant_hr_packet`: Stores raw ANT+ heart rate packets
  - Fields: device_id, packet_count, ant_hr_packet

#### Processing Tables
- `processed_ant_hr_packet`: Contains processed heart rate measurements
  - Fields: device_id, previous_beat_time, last_beat_time, calculated_heart_rate, heart_beat_count

#### Unified and Aggregated Tables
- `unified_hr_packet`: Stores enriched heart rate data with user context
  - Fields: user_id, user_name, device_id, hr_timestamp_seconds, hr_value, rr_interval_ms, processed_timestamp
- `per_second_heart_rate_aggregate`: Contains per-second aggregated heart rate data
  - Fields: user_name, rounded_up_time, processed_timestamp, avg_hr_per_second

Each table is automatically synced with its corresponding Redpanda topic, ensuring real-time data availability for both streaming and analytical queries.

### Schema Evolution

The data undergoes several schema transformations as it flows through the system:

1. **Raw ANT+ Data** → **Processed Data**
   ```
   {                                    {
     "device_id": string,        →        "device_id": string,
     "packet_count": int,                 "previous_beat_time": float,
     "ant_hr_packet": bytes              "last_beat_time": float,
   }                                      "calculated_heart_rate": int,
                                         "heart_beat_count": int
                                       }
   ```
   - Decodes binary ANT+ packet
   - Extracts timing information
   - Calculates heart rate

2. **Processed Data** → **Unified Data**
   ```
   {                                    {
     "device_id": string,        →        "user_id": int,
     "previous_beat_time": float,          "user_name": string,
     "last_beat_time": float,             "device_id": string,
     "calculated_heart_rate": int,         "hr_timestamp_seconds": float,
     "heart_beat_count": int              "hr_value": int,
   }                                      "rr_interval_ms": float,
                                         "processed_timestamp": datetime
                                       }
   ```
   - Enriches with user information
   - Standardizes timestamps
   - Adds RR interval calculation
   - Includes processing metadata

3. **Unified Data** → **Aggregated Data**
   ```
   {                                    {
     "user_id": int,             →        "user_name": string,
     "user_name": string,                 "rounded_up_time": datetime,
     "device_id": string,                 "processed_timestamp": datetime,
     "hr_timestamp_seconds": float,       "avg_hr_per_second": float
     "hr_value": int,
     "rr_interval_ms": float,
     "processed_timestamp": datetime
   }
   ```
   - Groups by user and time window
   - Computes average heart rate
   - Simplifies schema for analytics

Each transformation enriches the data while maintaining necessary information for the next stage in the pipeline.
