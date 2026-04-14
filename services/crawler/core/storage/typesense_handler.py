from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None
    
DEFAULT_COLLECTION_SCHEMA = {
    "name": "products",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "normalized_name", "type": "string", "infix": True},
        {"name": "product_name", "type": "string", "infix": True},
    ],
}

class TypesenseHandler:
    """Minimal Typesense HTTP client for product search collection."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[str] = None,
        protocol: Optional[str] = None,
        timeout: int = 15,
        session: Optional[Any] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("TYPESENSE_API_KEY", "")
        self.host = host or os.getenv("TYPESENSE_HOST", "localhost")
        self.port = port or os.getenv("TYPESENSE_PORT", "8108")
        self.protocol = protocol or os.getenv("TYPESENSE_PROTOCOL", "http")
        self.timeout = timeout
        self.session = session or (requests.Session() if requests else None)

    def ensure_collection(self, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = self._get_session()
        schema = schema or DEFAULT_COLLECTION_SCHEMA
        name = schema.get("name", "products")
        url = f"{self._base_url()}/collections/{name}"
        response = session.get(url, headers=self._headers(), timeout=self.timeout)
        if response.status_code == 200:
            return response.json()

        create_url = f"{self._base_url()}/collections"
        response = session.post(create_url, json=schema, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def delete_collection(self, name: str) -> Dict[str, Any]:
        session = self._get_session()
        url = f"{self._base_url()}/collections/{name}"
        response = session.delete(url, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def upsert_document(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        session = self._get_session()
        url = f"{self._base_url()}/collections/{collection}/documents"
        params = {"action": "upsert"}
        response = session.post(url, params=params, json=document, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def import_documents(self, collection: str, documents: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        session = self._get_session()
        url = f"{self._base_url()}/collections/{collection}/documents/import"
        payload = "\n".join(json.dumps(doc, ensure_ascii=False) for doc in documents)
        response = session.post(url, data=payload, headers=self._headers(content_type="text/plain"), timeout=self.timeout)
        response.raise_for_status()
        return self._parse_import_response(response.text)

    def search(
        self,
        collection: str,
        query: str,
        query_by: str = "normalized_name,product_name",
        query_by_weights: str = "4,4",
        num_typos: int = 2,
        min_len_1typo: int = 4,
        min_len_2typo: int = 7,
        typo_tokens_threshold: int = 1,
        infix: str = "always",
        drop_tokens_threshold: int = 2,
        prefix: str = "true",
        per_page: int = 10,
    ) -> Dict[str, Any]:
        session = self._get_session()
        url = f"{self._base_url()}/collections/{collection}/documents/search"
        params = {
            "q": query,
            "query_by": query_by,
            "query_by_weights": query_by_weights,
            "num_typos": num_typos,
            "min_len_1typo": min_len_1typo,
            "min_len_2typo": min_len_2typo,
            "typo_tokens_threshold": typo_tokens_threshold,
            "infix": infix,
            "drop_tokens_threshold": drop_tokens_threshold,
            "prefix": prefix,
            "per_page": per_page,
        }
        response = session.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _headers(self, content_type: str = "application/json") -> Dict[str, str]:
        headers = {"Content-Type": content_type}
        if self.api_key:
            headers["X-TYPESENSE-API-KEY"] = self.api_key
        return headers

    def _base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def _get_session(self) -> Any:
        if self.session is None:
            raise RuntimeError("requests is required for Typesense operations")
        return self.session

    def _parse_import_response(self, text: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            results.append(json.loads(line))
        return results
