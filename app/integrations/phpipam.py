# app/integrations/phpipam.py
import time
import logging
from typing import Optional, Any, Dict
import httpx
from pydantic import SecretStr

logger = logging.getLogger(__name__)


class PhpIpamAPIError(Exception):
    """Ошибки работы с PhpIPAM API."""


class PhpIpamAsyncClient:
    def __init__(
        self,
        base_url: str,
        app_id: str,
        username: str,
        password: str | SecretStr,
        verify_ssl: bool = True,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.app_id = app_id
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        self.token: Optional[str] = None
        self.token_expiry: float = 0
        self._client: Optional[httpx.AsyncClient] = None

    # ---------------- Lifecycle ----------------
    async def startup(self):
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            await self.authenticate()
            logger.info("[PhpIpamAsyncClient] ✅ подключен (%s)", self.base_url)
        except Exception as e:
            logger.error("❌ PhpIPAM startup failed: %s", e)
            await self._mark_dead()

    async def shutdown(self):
        try:
            if self._client:
                await self._client.aclose()
                logger.info("[PhpIpamAsyncClient] 🔴 закрыт")
        except Exception as e:
            logger.warning("⚠️ PhpIPAM shutdown failed: %s", e)
        finally:
            await self._mark_dead()

    async def _mark_dead(self):
        """Сбросить состояние клиента (недоступен)."""
        self._client = None
        self.token = None
        self.token_expiry = 0

    # ---------------- Internal helpers ----------------
    def _resolve_password(self) -> str:
        if isinstance(self.password, SecretStr):
            return self.password.get_secret_value()
        return self.password

    async def _build_url(self, controller: str, path: Optional[str] = None) -> str:
        url = f"{self.app_id}/{controller}/"
        if path:
            url += f"{path}/"
        return url

    async def _headers(self) -> Dict[str, str]:
        hdr = {"Content-Type": "application/json"}
        if self.token:
            hdr["token"] = self.token
        return hdr

    def is_alive(self) -> bool:
        return (
            self._client is not None
            and self.token is not None
            and time.time() < self.token_expiry
        )

    # ---------------- Auth ----------------
    async def authenticate(self) -> None:
        if not self._client:
            raise RuntimeError("httpx.AsyncClient не инициализирован")

        url = await self._build_url("user")
        resp = await self._client.post(
            url,
            auth=(self.username, self._resolve_password()),
        )
        data = resp.json()
        if not data.get("success"):
            raise PhpIpamAPIError(f"Auth failed: {data.get('message')}")

        self.token = data["data"]["token"]
        self.token_expiry = time.time() + 6 * 3600
        logger.debug("[PhpIpamAsyncClient] 🔑 новый токен до %s", self.token_expiry)

    async def ensure_token(self):
        if not self.token or time.time() > self.token_expiry:
            logger.info("[PhpIpamAsyncClient] 🔄 обновляем токен...")
            await self.authenticate()

    # ---------------- CRUD wrappers ----------------
    async def get(self, controller: str, path: Optional[str] = None, params: dict = None) -> Any:
        await self.ensure_token()
        url = await self._build_url(controller, path)
        resp = await self._client.get(url, headers=await self._headers(), params=params)
        return self._handle_response(resp)

    async def post(self, controller: str, data: dict, path: Optional[str] = None) -> Any:
        await self.ensure_token()
        url = await self._build_url(controller, path)
        resp = await self._client.post(url, json=data, headers=await self._headers())
        return self._handle_response(resp)

    async def patch(self, controller: str, data: dict, path: Optional[str] = None) -> Any:
        await self.ensure_token()
        url = await self._build_url(controller, path)
        resp = await self._client.patch(url, json=data, headers=await self._headers())
        return self._handle_response(resp)

    async def delete(self, controller: str, path: str, params: dict = None) -> Any:
        await self.ensure_token()
        url = await self._build_url(controller, path)
        resp = await self._client.delete(url, headers=await self._headers(), params=params)
        return self._handle_response(resp)

    # ---------------- Safe CRUD wrappers ----------------
    async def _safe_call(self, func, *args, **kwargs) -> Optional[Any]:
        if not self.is_alive():
            logger.warning("⚠️ PhpIPAM недоступен, вызов %s пропущен", func.__name__)
            return None
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error("❌ PhpIPAM %s error: %s", func.__name__, e)
            await self._mark_dead()
            return None

    async def get_safe(self, *args, **kwargs) -> Optional[Any]:
        return await self._safe_call(self.get, *args, **kwargs)

    async def post_safe(self, *args, **kwargs) -> Optional[Any]:
        return await self._safe_call(self.post, *args, **kwargs)

    async def patch_safe(self, *args, **kwargs) -> Optional[Any]:
        return await self._safe_call(self.patch, *args, **kwargs)

    async def delete_safe(self, *args, **kwargs) -> Optional[Any]:
        return await self._safe_call(self.delete, *args, **kwargs)

    # ---------------- Response handler ----------------
    def _handle_response(self, resp: httpx.Response) -> Any:
        try:
            jsondata = resp.json()
        except ValueError:
            raise PhpIpamAPIError("Response not JSON: " + resp.text)

        if not jsondata.get("success"):
            msg = jsondata.get("message", f"HTTP {resp.status_code}")
            raise PhpIpamAPIError(f"API error: {msg}")

        return jsondata.get("data")
