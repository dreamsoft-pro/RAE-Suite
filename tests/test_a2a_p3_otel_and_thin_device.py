import pytest
from core.otel_telemetry import OTelMeshTelemetry
from core.thin_device import ThinDeviceRuntime


def test_otel_telemetry_span_and_metrics_export():
    telemetry = OTelMeshTelemetry(service_name="rae-memory-test")
    span_id = telemetry.start_span("trace_1001", "save_memory")
    assert "span_" in span_id

    telemetry.record_tool_execution("trace_1001", "save_memory", 0.045, True)
    telemetry.record_tool_execution("trace_1001", "save_memory", 0.030, True)

    metrics = telemetry.export_prometheus_metrics()
    assert metrics["mcp_tools_called_total"]["save_memory"] == 2
    assert metrics["total_spans_recorded"] == 2
    assert metrics["service"] == "rae-memory-test"


def test_thin_device_runtime_detects_limits():
    runtime = ThinDeviceRuntime()
    assert runtime.profile.max_ram_mb > 0
    assert runtime.profile.max_worker_threads >= 1
