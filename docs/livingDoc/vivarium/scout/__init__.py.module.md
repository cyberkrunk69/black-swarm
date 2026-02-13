## Purpose
The vivarium.scout module is a logging and auditing library designed to track and record events within the Vivarium simulation framework. It provides a centralized logging mechanism, ensuring data integrity through line buffering, atomic writes, and fsync cadence. The module is responsible for managing audit data, including log rotation, auto-archiving, and gzip compression of old logs.

## Key Components
- **AuditLog Class**: An append-only JSONL event log that ensures data integrity through line buffering, atomic writes, and fsync cadence.
- **logger**: A constant used for logging purposes, providing a centralized logging mechanism for applications.
- **DEFAULT_AUDIT_PATH**: A constant that specifies the default path for audit data in the Vivarium Scout library.
- **ROTATION_SIZE_BYTES**: A constant that represents the size of a rotation in bytes.
- **FSYNC_EVERY_N_LINES**: A constant that controls the frequency of file syncing.
- **FSYNC_INTERVAL_SEC**: A constant that determines the interval in seconds for fsync operations.
- **EVENT_TYPES**: A collection of event types used in the Vivarium simulation framework.
- **_SESSION_LOCK**: A constant used to synchronize access to session data in Vivarium.
- **_get_session_id**: A function that generates a unique session ID for each process using uuid4.
- **hourly_spend**: A method that calculates the total cost incurred over the last N hours.
- **last_events**: A method that retrieves recent events, optionally filtered by type.
- **accuracy_metrics**: A method that calculates and returns accuracy metrics for navigation events.
- **flush**: A method that forces the persistence of events by calling fsync and ensuring that all events are written to storage before process exit.
- **close**: A method that is responsible for flushing and closing the log file.
- **__enter__**: A special Python method that defines the behavior when an object is used in a with statement.
- **__exit__**: A special Python method that is called when exiting a context manager.

## Interaction Flow
The vivarium.scout module interacts with the vivarium/scout/audit.py module for logging and auditing purposes. It uses the AuditLog class to manage audit data, including log rotation, auto-archiving, and gzip compression of old logs. The module also uses the logger constant for logging purposes and the DEFAULT_AUDIT_PATH constant to specify the default path for audit data. The _get_session_id function generates a unique session ID for each process using uuid4, and the hourly_spend, last_events, accuracy_metrics, flush, close, __enter__, and __exit__ methods are used to manage events and ensure data integrity.