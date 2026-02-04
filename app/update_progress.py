import json
import glob
import os
from datetime import datetime

PROGRESS_MD = "PROGRESS.md"
LESSONS_JSON = "learned_lessons.json"
GRIND_LOGS_DIR = "grind_logs"

def load_grind_logs():
    logs = []
    pattern = os.path.join(GRIND_LOGS_DIR, "*.json")
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "r") as f:
                logs.append(json.load(f))
        except Exception:
            continue
    return logs

def compute_metrics(logs):
    total = len(logs)
    if total == 0:
        return {
            "total": 0,
            "successes": 0,
            "failures_by_category": {},
            "avg_duration": 0,
            "success_rate": 0,
            "common_failures": []
        }
    successes = sum(1 for log in logs if log.get("returncode") == 0)
    failures = [log for log in logs if log.get("returncode") != 0]
    failures_by_category = {}
    for log in failures:
        cat = log.get("error_category", "unknown")
        failures_by_category[cat] = failures_by_category.get(cat, 0) + 1
    durations = [log.get("duration", 0) for log in logs if isinstance(log.get("duration"), (int, float))]
    avg_duration = sum(durations) / len(durations) if durations else 0
    success_rate = (successes / total) * 100 if total else 0
    # top 3 common failures
    common = sorted(failures_by_category.items(), key=lambda x: x[1], reverse=True)[:3]
    common_formatted = [f"{cat} ({cnt})" for cat, cnt in common]
    return {
        "total": total,
        "successes": successes,
        "failures_by_category": failures_by_category,
        "avg_duration": avg_duration,
        "success_rate": success_rate,
        "common_failures": common_formatted
    }

def update_progress_md(metrics):
    # Read existing content
    if os.path.exists(PROGRESS_MD):
        with open(PROGRESS_MD, "r") as f:
            content = f.read()
    else:
        content = ""
    # Prepare health metrics section
    health_section = (
        "\n## Health Metrics\n"
        f"- Success rate: {metrics['success_rate']:.2f}%\n"
        f"- Avg duration: {metrics['avg_duration']:.2f}s\n"
        f"- Common failures: {', '.join(metrics['common_failures']) if metrics['common_failures'] else 'None'}\n"
    )
    # Remove existing Health Metrics section if present
    import re
    content = re.sub(r"\n## Health Metrics[\s\S]*?(?=\n## |\Z)", "", content, flags=re.MULTILINE)
    # Append new section
    new_content = content.rstrip() + health_section + "\n"
    with open(PROGRESS_MD, "w") as f:
        f.write(new_content)

def append_lesson():
    lesson = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "lesson": "Added failure tracking to PROGRESS.md for better swarm health visibility."
    }
    lessons = []
    if os.path.exists(LESSONS_JSON):
        try:
            with open(LESSONS_JSON, "r") as f:
                lessons = json.load(f)
        except Exception:
            lessons = []
    lessons.append(lesson)
    with open(LESSONS_JSON, "w") as f:
        json.dump(lessons, f, indent=2)

def main():
    logs = load_grind_logs()
    metrics = compute_metrics(logs)
    update_progress_md(metrics)
    append_lesson()

if __name__ == "__main__":
    main()