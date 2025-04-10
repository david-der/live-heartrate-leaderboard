# This file was auto-generated by the framework. You can add data models or change the existing ones
from app.ingest import models, transforms

from moose_lib import IngestPipeline, IngestPipelineConfig
from moose_lib import StreamingFunction
from moose_lib import ConsumptionApi
from app.apis.get_group_hr_by_second import get_hr_api, QueryParams, QueryResult
from app.functions.raw_to_processed import RawAntHRPacket__ProcessedAntHRPacket
from app.functions.processed_to_unified import processedAntHRPacket__UNIFIED_HR_PACKET
from app.datamodels.UnifiedHRPacket import UnifiedHRPacket
from app.datamodels.ProcessedAntHRPacket import ProcessedAntHRPacket
from app.datamodels.RawAntHRPacket import RawAntHRPacket
from app.functions.aggregated_per_second import aggregateHeartRateSummaryPerSecondMV
# Initalize Ingest Pipeline Infrastructure
rawAntHRPipeline = IngestPipeline[RawAntHRPacket]("raw_ant_hr_packet", IngestPipelineConfig(
    ingest=True,
    stream=True,
    table=True
))

unifiedHRPipeline = IngestPipeline[UnifiedHRPacket]("unified_hr_packet", IngestPipelineConfig(
    ingest=True,
    stream=True,
    table=True
))

processedAntHRPipeline = IngestPipeline[ProcessedAntHRPacket]("processed_ant_hr_packet", IngestPipelineConfig(
    ingest=True,
    stream=True,
    table=True
))

# Transform RawAntHRPacket to ProcessedAntHRPacket in stream
rawAntHRPipeline.get_stream().add_transform(
    destination=processedAntHRPipeline.get_stream(),
    transformation=RawAntHRPacket__ProcessedAntHRPacket
)

processedAntHRPipeline.get_stream().add_transform(
    destination=unifiedHRPipeline.get_stream(),
    transformation=processedAntHRPacket__UNIFIED_HR_PACKET
)

getHR_api = ConsumptionApi[QueryParams, QueryResult](name="getHR", query_function=get_hr_api)