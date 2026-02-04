class NarrativeIdentityTracker:
    """
    Simple narrative identity tracker that updates core traits based on
    textual events. It uses a keyword-to-trait mapping and increments
    trait scores when keywords are found in the event description.
    """

    def __init__(self, core_traits):
        """
        Initialize with a reference to the persona's core_traits dict.
        """
        self.core_traits = core_traits
        # Mapping of keywords to trait names
        self.trait_keywords = {
            "brave": "courage",
            "coward": "courage",
            "wise": "wisdom",
            "fool": "wisdom",
            "kind": "kindness",
            "cruel": "kindness",
            "leader": "leadership",
            "follower": "leadership",
        }

    def process_event(self, event: str):
        """
        Process a narrative event string and return a dict of trait updates.
        Positive keywords increase the trait, negative keywords decrease it.
        """
        updates = {}
        lowered = event.lower()
        for keyword, trait in self.trait_keywords.items():
            if keyword in lowered:
                delta = 1 if keyword not in {"coward", "fool", "cruel", "follower"} else -1
                updates[trait] = updates.get(trait, 0) + delta
        # Apply updates directly to the referenced core_traits dict
        for trait, delta in updates.items():
            self.core_traits[trait] = self.core_traits.get(trait, 0) + delta
        return updates