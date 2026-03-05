# Index schemas (v1)

We keep simple **append-only JSONL** indexes for later search/vectorization.

## adr_index.jsonl
One line per ADR.

```json
{
  "adr_id": "ADR-20260304-001",
  "title": "Adopt ADR decision records",
  "status": "Accepted",
  "date": "2026-03-04",
  "owners": ["Ten"],
  "tags": ["memory", "process"],
  "path": "knowledge/decisions/ADR-20260304-001-adopt-adr.md",
  "evidence": ["telegram:msg:49850"],
  "artifact_links": [],
  "hash": "<sha256 of file>",
  "created_at": "2026-03-04T07:44:00Z"
}
```
