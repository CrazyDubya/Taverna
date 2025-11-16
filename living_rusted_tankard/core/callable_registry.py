# living_rusted_tankard/core/callable_registry.py

CALLBACK_REGISTRY = {}
INTERACTION_REGISTRY = {}  # For NPC interactions specifically


def register_callback(name: str):
    """
    Decorator to register a general callback function for serialization.
    """

    def decorator(func):
        if name in CALLBACK_REGISTRY:
            # This could indicate a naming collision, which might be an issue.
            # For now, let's print a warning. In a real scenario, you might raise an error
            # or have a more sophisticated way to handle this (e.g., namespacing).
            print(
                f"Warning: Callback '{name}' is being overwritten in CALLBACK_REGISTRY."
            )
        CALLBACK_REGISTRY[name] = func
        return func

    return decorator


def register_interaction(name: str):
    """
    Decorator to register an NPC interaction function for serialization.
    """

    def decorator(func):
        if name in INTERACTION_REGISTRY:
            print(
                f"Warning: Interaction '{name}' is being overwritten in INTERACTION_REGISTRY."
            )
        INTERACTION_REGISTRY[name] = func
        return func

    return decorator


def get_callback(name: str):
    """
    Retrieves a callback function from the registry.
    """
    callback = CALLBACK_REGISTRY.get(name)
    if not callback:
        raise ValueError(f"No callback registered with name: {name}")
    return callback


def get_interaction(name: str):
    """
    Retrieves an NPC interaction function from the registry.
    """
    interaction = INTERACTION_REGISTRY.get(name)
    if not interaction:
        raise ValueError(f"No interaction registered with name: {name}")
    return interaction
