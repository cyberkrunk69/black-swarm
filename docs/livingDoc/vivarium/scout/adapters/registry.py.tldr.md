# _ensure_registry

Simple _ensure_registry utility.
---

# get_adapter_for_path

This function retrieves an adapter for a given path, using the path's language to determine the adapter type. It appears to be part of a system that maps file paths to language-specific adapters. The function likely uses a registry or mapping to resolve the adapter type based on the path's language.
---

# get_supported_extensions

The function `get_supported_extensions` retrieves a list of supported file extensions from the `_ADAPTERS` registry, which is a dictionary of adapters. It ensures the registry is initialized and returns the extensions in sorted order.