# app/core/plugin_registry.py
_registry = {}


def plugin(name: str):
    def wrapper(cls_or_func):
        _registry[name] = cls_or_func
        return cls_or_func

    return wrapper


def get_plugins():
    return _registry
