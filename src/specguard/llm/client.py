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
        client = httpx.Client(transport=self._transport, timeout=self.config.timeout_seconds)
        try:
            response = client.post(url, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(f"模型服务不可用: {exc}") from exc
        finally:
            client.close()
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError("模型返回的内容无法解析") from exc
