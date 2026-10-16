import os
from urllib.parse import urlparse

import httpx

from specguard.config.models import LlmConfig
from specguard.errors import ProviderError


class LlmClient:
    def __init__(self, config: LlmConfig, transport: httpx.BaseTransport | None = None):
        if not config.base_url:
            raise ProviderError("未配置内部模型地址")
        self.config = config
        self._allowed_host = urlparse(config.base_url).netloc
        self._transport = transport

    def post_review(self, payload: dict) -> dict:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        host = urlparse(url).netloc
        if host != self._allowed_host:
            raise ProviderError("禁止把源码改送到其他服务")
        headers = self._auth_headers()
        attempts = self.config.max_retries + 1
        client = httpx.Client(transport=self._transport, timeout=self.config.timeout_seconds)
        try:
            for attempt in range(attempts):
                try:
                    response = client.post(url, json=payload, headers=headers)
                except httpx.HTTPError as exc:
                    if attempt + 1 >= attempts:
                        raise ProviderError("模型服务不可用") from exc
                    continue
                if response.status_code >= 500 and attempt + 1 < attempts:
                    continue
                if response.status_code >= 400:
                    raise ProviderError(f"模型返回无法使用的状态 {response.status_code}")
                return _usable_payload(response)
        finally:
            client.close()
        raise ProviderError("模型服务不可用")

    def _auth_headers(self) -> dict[str, str]:
        token = os.environ.get(self.config.api_key_env, "")
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}


def _usable_payload(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ProviderError("模型返回的内容无法解析") from exc
    if not isinstance(payload, dict):
        raise ProviderError("模型返回的内容无法作为审核结果使用")
    if "error" in payload and "findings" not in payload:
        raise ProviderError("模型返回的内容无法作为审核结果使用")
    if "findings" in payload and not isinstance(payload["findings"], list):
        raise ProviderError("模型返回的内容无法作为审核结果使用")
    return payload
