import json
import logging

class FailureCategorizer:
    """
    Categorizes grind session failures, records the category in the grind log,
    updates learned_lessons.json with failure patterns, and provides counts
    of errors per category for reporting.
    """

    def __init__(self):
        # Defined error categories per the Reflexion paper
        self.error_categories = [
            'TIMEOUT',
            'ENCODING',
            'IMPORT',
            'SYNTAX',
            'RUNTIME',
            'UNKNOWN'
        ]
        # Files used for persistence (relative to the experiment directory)
        self.learned_lessons_file = 'learned_lessons.json'
        self.grind_log_file = 'grind_log.json'

    # --------------------------------------------------------------------- #
    # 1. Error categorization
    # --------------------------------------------------------------------- #
    def categorize_error(self, error_message: str) -> str:
        """
        Return the appropriate error category for a given error message.
        Matching is case‑insensitive and based on keyword heuristics.
        """
        msg = error_message.lower()
        if 'timeout' in msg:
            return 'TIMEOUT'
        elif 'unicode' in msg or 'charset' in msg:
            return 'ENCODING'
        elif 'import' in msg and 'error' in msg:
            return 'IMPORT'
        elif 'syntax' in msg:
            return 'SYNTAX'
        elif 'execution' in msg or 'runtime' in msg:
            return 'RUNTIME'
        else:
            return 'UNKNOWN'

    # --------------------------------------------------------------------- #
    # 2. Store category in grind log
    # --------------------------------------------------------------------- #
    def store_category_in_grind_log(self, error_category: str) -> None:
        """
        Insert or update the 'error_category' field in the grind log JSON.
        If the log does not exist, create a minimal one.
        """
        try:
            with open(self.grind_log_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data['error_category'] = error_category
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            # Create a new log containing only the error category
            with open(self.grind_log_file, 'w', encoding='utf-8') as f:
                json.dump({'error_category': error_category}, f, indent=4)

    # --------------------------------------------------------------------- #
    # 3. Update learned_lessons.json with failure patterns
    # --------------------------------------------------------------------- #
    def update_learned_lessons(self, error_category: str, error_message: str) -> None:
        """
        Append the raw error message to the list for its category.
        If the file or the category entry does not exist, they are created.
        """
        try:
            with open(self.learned_lessons_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.setdefault(error_category, []).append(error_message)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            # Fresh file – start with the first entry
            with open(self.learned_lessons_file, 'w', encoding='utf-8') as f:
                json.dump({error_category: [error_message]}, f, indent=4)

    # --------------------------------------------------------------------- #
    # 4. Count errors by category for reporting
    # --------------------------------------------------------------------- #
    def count_errors_by_category(self) -> dict:
        """
        Return a dictionary mapping each error category to the number of
        recorded failures.
        """
        try:
            with open(self.learned_lessons_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {cat: len(messages) for cat, messages in data.items()}
        except FileNotFoundError:
            return {}

# ------------------------------------------------------------------------- #
# Example usage (can be removed or adapted by the orchestrator)
# ------------------------------------------------------------------------- #
if __name__ == '__main__':
    categorizer = FailureCategorizer()

    # Simulated error message – replace with real output from a grind session
    error_message = 'example error message'

    # 1. Determine category
    error_category = categorizer.categorize_error(error_message)

    # 2. Record category in grind log
    categorizer.store_category_in_grind_log(error_category)

    # 3. Append pattern to learned lessons
    categorizer.update_learned_lessons(error_category, error_message)

    # 4. Print a quick report
    print('Current error counts:', categorizer.count_errors_by_category())