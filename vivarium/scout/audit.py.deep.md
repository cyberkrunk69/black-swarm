# audit.py

## Function: `_get_session_id`

Detailed documentation (deep stub).

```python
def _get_session_id() -> str:
    """Return uuid4 session ID, one per process."""
    global _SESSION_ID
    with _SESSION_LOCK:
        if _SESSION_ID is None:
            _SESSION_ID = str(uuid.uuid4())
        return _SESSION_ID
```

## Class: `AuditLog`

Detailed documentation (deep stub).

```python
class AuditLog:
    """
    Append-only JSONL event log with line buffering, fsync cadence, and crash recovery.

    - Line buffering (buffering=1): flush on newline
    - Atomic writes: single write() per event, no partial JSON
    - Fsync: every 10 lines OR every 1 second
    - Log rotation: auto-archive at 10MB, gzip old logs
    - Corruption recovery: skip malformed lines on read, log warning
    """

    def __init__(self, path: Path = None):
        self._path = Path(path).expanduser().res
```

## Function: `__init__`

Detailed documentation (deep stub).

```python
    def __init__(self, path: Path = None):
        self._path = Path(path).expanduser().resolve() if path else DEFAULT_AUDIT_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._file: Optional[Any] = None
        self._lines_since_fsync = 0
        self._last_fsync = 0.0
        self._ensure_open()
```

## Function: `_ensure_open`

Detailed documentation (deep stub).

```python
    def _ensure_open(self) -> None:
        """Open file with line buffering if not already open."""
        if self._file is not None and not self._file.closed:
            return
        self._file = open(
            self._path,
            "a",
            encoding="utf-8",
            buffering=1,  # Line buffering — flush on newline
        )
        self._lines_since_fsync = 0
        self._last_fsync = time.monotonic()
```

## Function: `_maybe_rotate`

Detailed documentation (deep stub).

```python
    def _maybe_rotate(self) -> None:
        """Rotate log if >= 10MB: gzip current, start fresh."""
        try:
            stat = self._path.stat()
        except OSError:
            return
        if stat.st_size < ROTATION_SIZE_BYTES:
            return

        self._close_file()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archived = self._path.parent / f"{self._path.stem}_{ts}.jsonl.gz"

        with open(self._path, "rb") as f:
            data = f.read()
 
```

## Function: `_close_file`

Detailed documentation (deep stub).

```python
    def _close_file(self) -> None:
        if self._file is not None and not self._file.closed:
            try:
                self._file.flush()
                os.fsync(self._file.fileno())
            except OSError:
                pass
            self._file.close()
            self._file = None
```

## Function: `_fsync_if_needed`

Detailed documentation (deep stub).

```python
    def _fsync_if_needed(self) -> None:
        """Fsync every 10 lines or every 1 second."""
        self._lines_since_fsync += 1
        now = time.monotonic()
        if (
            self._lines_since_fsync >= FSYNC_EVERY_N_LINES
            or (now - self._last_fsync) >= FSYNC_INTERVAL_SEC
        ):
            try:
                if self._file is not None and not self._file.closed:
                    self._file.flush()
                    os.fsync(self._file.fileno())
            except
```

## Function: `log`

Detailed documentation (deep stub).

```python
    def log(
        self,
        event_type: str,
        *,
        cost: float = None,
        model: str = None,
        input_t: int = None,
        output_t: int = None,
        files: List[str] = None,
        reason: str = None,
        confidence: int = None,
        duration_ms: int = None,
        config: Dict[str, Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log an event. Atomic line write, fsync cadence.

        Args:
            event_type: One of nav|br
```

## Function: `_iter_lines`

Detailed documentation (deep stub).

```python
    def _iter_lines(self) -> Iterator[str]:
        """Stream lines from current log file. Skips malformed lines, logs warnings."""
        if not self._path.exists():
            return
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if not line:
                    continue
                yield line
```

## Function: `_parse_line`

Detailed documentation (deep stub).

```python
    def _parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse one JSON line. Return None and log warning if corrupted."""
        try:
            return json.loads(line)
        except json.JSONDecodeError as e:
            logger.warning("AuditLog: skipping malformed line (corruption recovery): %s", e)
            return None
```

## Function: `query`

Detailed documentation (deep stub).

```python
    def query(
        self,
        since: Optional[datetime] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Streaming JSONL parser — memory-efficient for large logs.

        Returns events matching since (inclusive) and event_type filter.
        Skips malformed lines with a logged warning.
        """
        since_ts = since.isoformat() if since else None
        results: List[Dict[str, Any]] = []

        for line in self._iter_lines():
```

## Function: `hourly_spend`

Detailed documentation (deep stub).

```python
    def hourly_spend(self, hours: int = 1) -> float:
        """Sum costs in last N hours."""
        if hours <= 0:
            return 0.0
        cutoff = datetime.now(timezone.utc).replace(
            microsecond=0, second=0, minute=0
        )
        cutoff = cutoff - timedelta(hours=hours)
        events = self.query(since=cutoff)
        return sum(e.get("cost", 0) or 0 for e in events)
```

## Function: `last_events`

Detailed documentation (deep stub).

```python
    def last_events(
        self,
        n: int = 20,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recent events, optionally filtered. Streams and keeps last N matches."""
        window: deque = deque(maxlen=n)
        for line in self._iter_lines():
            obj = self._parse_line(line)
            if obj is None:
                continue
            if event_type is not None and obj.get("event") != event_type:
                continue
            wi
```

## Function: `accuracy_metrics`

Detailed documentation (deep stub).

```python
    def accuracy_metrics(self, since: datetime) -> Dict[str, Any]:
        """
        % validation_fail vs total nav events.

        Returns dict with total_nav, validation_fail_count, accuracy_pct.
        """
        events = self.query(since=since)
        nav_events = [e for e in events if e.get("event") == "nav"]
        validation_fails = [e for e in events if e.get("event") == "validation_fail"]
        total_nav = len(nav_events)
        fail_count = len(validation_fails)
        if to
```

## Function: `close`

Detailed documentation (deep stub).

```python
    def close(self) -> None:
        """Flush and close the log file."""
        with self._lock:
            self._close_file()
```

## Function: `__enter__`

Detailed documentation (deep stub).

```python
    def __enter__(self) -> "AuditLog":
        return self
```

## Function: `__exit__`

Detailed documentation (deep stub).

```python
    def __exit__(self, *args: Any) -> None:
        self.close()
```
