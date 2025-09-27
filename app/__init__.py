from app.core.utils.version import __version__

import bcrypt

# Monkey-patch для совместимости Passlib с bcrypt >=4.0
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = _About()