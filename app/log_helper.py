import os

def get_recent_logs():
    """Utility used by deferred tasks to obtain log data."""
    log_path = os.getenv('GRINDER_LOG_PATH', 'logs/grinder.log')
    if not os.path.isfile(log_path):
        return ""
    with open(log_path, 'r', encoding='utf-8') as f:
        # Return the last 10 KB of the log (enough for pattern detection)
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(size - 10 * 1024, 0), os.SEEK_SET)
        return f.read()