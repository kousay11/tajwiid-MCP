# Validation records

Empty on purpose. A `ValidationRecord` (see `knowledge/models.py`) needs a named reviewer, a
qualification record, the decision, a rationale, cited evidence and the SHA-256 of the exact
subject. Only such a record can ever make `scholarly_verified` legal; the services never
emit it. Records are append-only: later decisions supersede, never rewrite.
