from typing import Optional


class PluginMeta:
    def __init__(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        author: Optional[str] = None,
        priority: int = 10,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.priority = priority

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "priority": self.priority,
        }


class PluginMetaDescriptor:
    def __init__(self, *, name: str, version: str, **kwargs):
        self._meta = PluginMeta(name=name, version=version, **kwargs)

    def __get__(self, instance, owner) -> PluginMeta:
        return self._meta

    def __set__(self, instance, value):
        raise AttributeError("meta is read-only")

    def __delete__(self, instance):
        raise AttributeError("meta cannot be deleted")

    def __repr__(self):
        return f"<PluginMetaDescriptor(name={self._meta.name}, version={self._meta.version})>"
