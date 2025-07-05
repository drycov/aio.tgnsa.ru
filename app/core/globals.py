# app/core/globals.py

import inspect

class GlobalFlags:
    def __init__(self):
        self._debug_mode = False

    @property
    def debug_mode(self) -> bool:
        stack = inspect.stack()
        caller = stack[1]
        print(f"[debug_mode] accessed from {caller.filename}:{caller.lineno} in {caller.function}()")
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, value: bool):
        caller = inspect.stack()[1]
        print(f"[debug_mode] set to {value} from {caller.filename}:{caller.lineno} in {caller.function}()")
        self._debug_mode = value


# создаём глобальный экземпляр
flags = GlobalFlags()
