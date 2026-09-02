# ORD / ex2 — Single-site volume data for a case study

**Persona:** researcher studying a specific convective storm.

Lists and concurrently downloads the raw ODIM HDF5 polar-volume scans from
one radar site during a known event window, ready to open offline with
tools like wradlib or Py-ART.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
