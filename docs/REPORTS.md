# Reports

v1.9 adds local report storage.

```bash
make worker-report
python scripts/list_worker_reports.py
python scripts/export_worker_reports.py
python -m pytest tests/test_report_store.py -q
```
