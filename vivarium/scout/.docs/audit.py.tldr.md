# logger

The `logger` constant is used for logging purposes, but its exact behavior and responsibilities are unclear due to the lack of a docstring. It appears to be related to the `vivarium/scout/audit.py` module, suggesting it may be used for logging audit-related events or information.
---

# DEFAULT_AUDIT_PATH

The `DEFAULT_AUDIT_PATH` constant is used to specify the default path for audit data in the Vivarium Scout library. It is responsible for defining the default location where audit data is stored. This constant is likely used in conjunction with the `vivarium/scout/audit.py` module to manage audit data.
---

# ROTATION_SIZE_BYTES

**ROTATION_SIZE_BYTES**
=====================

ROTATION_SIZE_BYTES is a Python constant that represents the size of a rotation in bytes. Its primary purpose is to define a fixed size for rotation operations. It depends on the vivarium/scout/audit.py module, which likely uses this constant for data processing or storage.
---

# FSYNC_EVERY_N_LINES

**FSYNC_EVERY_N_LINES**

FSYNC_EVERY_N_LINES is a constant that controls the frequency of file syncing. It determines how often file syncing should occur, specifically every N lines. Its primary purpose is to regulate the syncing process, likely for logging or auditing purposes. It interacts with the vivarium/scout/audit.py module, suggesting its role in data collection or logging.
---

# FSYNC_INTERVAL_SEC

**FSYNC_INTERVAL_SEC**
=====================

FSYNC_INTERVAL_SEC is a Python constant that determines the interval in seconds for fsync operations. Its primary purpose is to control the frequency of file synchronization. It depends on the vivarium/scout/audit.py module, which likely utilizes this constant for file system operations.
---

# EVENT_TYPES

The `EVENT_TYPES` constant is not explicitly documented, but based on its interactions with `vivarium/scout/audit.py`, it appears to be a collection of event types used in the Vivarium simulation framework. Its primary purpose is to define and categorize events that occur within the simulation, and it is likely used to facilitate event handling and auditing.
---

# _SESSION_LOCK

The `_SESSION_LOCK` constant is used to synchronize access to session data in Vivarium. It is primarily responsible for ensuring thread safety during session operations. Its relationship with `vivarium/scout/audit.py` suggests it may be used in conjunction with auditing or logging functionality within Vivarium.
---

# _get_session_id

**Function Summary: `_get_session_id`**

The `_get_session_id` function generates a unique session ID for each process using `uuid4`. It returns a string representing the session ID. The function interacts with `vivarium/scout/audit.py` and is responsible for exception handling and conditional logic to ensure a valid session ID is returned.
---

# AuditLog

**AuditLog Class Summary**
==========================

The `AuditLog` class is an append-only JSONL event log that ensures data integrity through line buffering, atomic writes, and fsync cadence. It provides crash recovery and log rotation features, including auto-archiving and gzip compression of old logs. It depends on the `vivarium/scout/audit.py` module for interactions.
---

# __init__

The `__init__` method initializes an object, setting its attributes based on the provided `path` parameter. It is responsible for setting up the object's state. The `path` parameter is optional and defaults to `None`. It interacts with the `vivarium/scout/audit.py` module, likely utilizing its functionality.
---

# _ensure_open

The `_ensure_open` method opens a file with line buffering if it's not already open, ensuring it's accessible for further operations. Its primary responsibility is to conditionally open a file and make it available for use. It depends on the `vivarium/scout/audit.py` module for its functionality.
---

# _maybe_rotate

**_maybe_rotate Method Summary**
================================

The `_maybe_rotate` method rotates the log if it has grown to >= 10MB by gzipping the current log and starting a fresh one. It handles exceptions and conditions to ensure a smooth log rotation process. This method depends on the `vivarium/scout/audit.py` module for its functionality.
---

# _close_file

The `_close_file` method is a private method responsible for closing a file, handling potential exceptions, and ensuring the file is properly closed. It appears to be part of a class that interacts with the `vivarium/scout/audit.py` module, possibly for file operations related to auditing or scouting.
---

# _fsync_if_needed

**_fsync_if_needed Method Summary**
=====================================

The `_fsync_if_needed` method synchronizes file data to disk every 10 lines or every 1 second. It is responsible for ensuring data integrity by periodically calling the `fsync` function. This method depends on the `vivarium/scout/audit.py` module and is likely used in a context where data persistence is critical.
---

# log

**Python Method 'log' Summary**

The `log` method logs an event with atomic line write and fsync cadence, recording various details such as event type, cost, model, input/output token counts, affected files, reason, confidence, duration, and additional fields.

Its primary purpose is to track and record events, and its key responsibilities include writing log entries and handling optional parameters. The `log` method depends on the `vivarium/scout/audit.py` module, which suggests it is part of a larger logging or auditing system.
---

# _iter_lines

**Summary**

The `_iter_lines` method streams lines from the current log file, skipping malformed lines and logging warnings. It iterates over the log file, handling exceptions and returning a generator of valid lines. This method depends on the `vivarium/scout/audit.py` module for its functionality.
---

# _parse_line

**Summary**

The `_parse_line` method parses a single JSON line, returning a dictionary representation if successful, and logging a warning if the line is corrupted. It handles exceptions and returns `None` in case of errors. This method is likely used in conjunction with the `vivarium/scout/audit.py` module.
---

# query

**Summary**

The `query` method is a streaming JSONL parser designed for memory-efficient processing of large logs. It returns a list of events matching a specified `since` timestamp (inclusive) and `event_type` filter, skipping malformed lines with a logged warning. It depends on the `vivarium/scout/audit.py` module.
---

# hourly_spend

**hourly_spend Method Summary**
================================

The `hourly_spend` method calculates the total cost incurred over the last N hours. It takes an optional `hours` parameter (defaulting to 1) and returns the total cost as a float. This method likely interacts with the `vivarium/scout/audit.py` module to retrieve relevant cost data.
---

# last_events

**last_events Method Summary**
================================

The `last_events` method retrieves recent events, optionally filtered by type, and returns the last N matches. It iterates over events, applies filtering (if specified), and returns a list of dictionaries containing event information. This method depends on the `vivarium/scout/audit.py` module for event data.
---

# accuracy_metrics

**accuracy_metrics Method Summary**

The `accuracy_metrics` method calculates and returns accuracy metrics for navigation events. It takes a `since` datetime parameter and returns a dictionary with total navigation events, validation failure count, and accuracy percentage. This method depends on the `vivarium/scout/audit.py` module and is likely used to evaluate the performance of navigation-related functionality.
---

# flush

**flush Method Summary**

The `flush` method forces the persistence of events by calling `fsync` and ensuring that all events are written to storage before process exit. It handles exceptions and conditions to guarantee data integrity. This method is related to the `vivarium/scout/audit.py` dependencies, which it interacts with to enforce data persistence.
---

# close

**close method summary**

The `close` method is responsible for flushing and closing the log file. It handles exceptions during this process and calls necessary operations. This method is likely used in conjunction with the `vivarium/scout/audit.py` module, possibly to manage logging functionality within the context of these dependencies.
---

# __enter__

**__enter__ Method Summary**

The `__enter__` method is a special Python method that defines the behavior when an object is used in a `with` statement. Its primary purpose is to return the object itself, allowing it to be used within the `with` block. It is likely used in conjunction with the `AuditLog` class in the `vivarium/scout/audit.py` module.
---

# __exit__

The `__exit__` method is a special Python method that is called when exiting a context manager. Its primary purpose is to perform any necessary cleanup or final actions. It is typically used in conjunction with the `with` statement and is related to the `vivarium/scout/audit.py` dependencies, where it may be used to manage resources or perform auditing tasks.