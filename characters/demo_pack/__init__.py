import os
import json

DEMO_PACK_DIR = os.path.dirname(__file__)

def load_demo_pack():
    characters = {}
    for fname in os.listdir(DEMO_PACK_DIR):
        if fname.endswith('.json'):
            with open(os.path.join(DEMO_PACK_DIR, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
                characters[data['name']] = data
    return characters

# Export for the rest of the system
DEMO_CHARACTERS = load_demo_pack()