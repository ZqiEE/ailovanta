from node_client.resource_guard import GpuSample, ResourceGuard, ResourceLimits, ResourceSnapshot, parse_nvidia_smi


def snapshot(**kwargs) -> ResourceSnapshot:
    return ResourceSnapshot(cpu_percent=kwargs.get("cpu", 10), free_memory_gb=kwargs.get("memory", 8), idle_seconds=kwargs.get("idle", 120), on_battery=kwargs.get("battery", False), gpu=kwargs.get("gpu"))


def test_allows_idle_machine() -> None:
    guard = ResourceGuard(ResourceLimits(), snapshot_provider=lambda: snapshot(gpu=GpuSample(20, 1000, 8000, 60)))
    assert guard.can_run_job() == (True, "ok")


def test_pauses_on_user_activity() -> None:
    guard = ResourceGuard(ResourceLimits(min_idle_seconds=300), snapshot_provider=lambda: snapshot(idle=20))
    allowed, reason = guard.can_run_job()
    assert not allowed
    assert "user active" in reason


def test_pauses_on_battery() -> None:
    guard = ResourceGuard(ResourceLimits(pause_on_battery=True), snapshot_provider=lambda: snapshot(battery=True))
    allowed, reason = guard.can_run_job()
    assert not allowed
    assert "battery" in reason


def test_pauses_when_gpu_busy() -> None:
    guard = ResourceGuard(ResourceLimits(max_gpu_percent=50), snapshot_provider=lambda: snapshot(gpu=GpuSample(90, 1000, 8000, 60)))
    allowed, reason = guard.can_run_job()
    assert not allowed
    assert "gpu too busy" in reason


def test_pauses_when_gpu_memory_high() -> None:
    guard = ResourceGuard(ResourceLimits(max_gpu_memory_percent=50), snapshot_provider=lambda: snapshot(gpu=GpuSample(10, 7000, 8000, 60)))
    allowed, reason = guard.can_run_job()
    assert not allowed
    assert "gpu memory too high" in reason


def test_pauses_when_gpu_hot() -> None:
    guard = ResourceGuard(ResourceLimits(max_gpu_temperature_c=70), snapshot_provider=lambda: snapshot(gpu=GpuSample(10, 1000, 8000, 82)))
    allowed, reason = guard.can_run_job()
    assert not allowed
    assert "gpu temperature too high" in reason


def test_parse_nvidia_smi() -> None:
    sample = parse_nvidia_smi("10, 1000, 8000, 55\n80, 2000, 24000, 70\n")
    assert sample is not None
    assert sample.utilization_percent == 80
    assert sample.memory_used_mb == 2000
    assert sample.memory_total_mb == 24000
    assert sample.temperature_c == 70
