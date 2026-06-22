# Job Descriptor and Worker Reports

v1.8 adds optional job descriptors and worker execution reports.

## Files

```text
node_client/job_descriptor.py
node_client/execution_report.py
scripts/worker_report_demo.py
```

## Worker report demo

```bash
python scripts/worker_report_demo.py
```

## Tests

```bash
python -m pytest tests/test_job_descriptor.py tests/test_execution_report.py -q
```

## Purpose

The worker now has a place to record why a job was accepted or rejected, and to emit a structured report for later auditing.
