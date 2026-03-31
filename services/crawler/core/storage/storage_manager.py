from typing import Any, Dict, Optional

from services.crawler.core.storage.database_handler import DatabaseHandler
from services.crawler.core.storage.typesense_handler import TypesenseHandler


class StorageManager:
    _instance: Optional["StorageManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> "StorageManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        db_url: Optional[str] = None,
        database_handler: Optional[DatabaseHandler] = None,
        typesense_handler: Optional[TypesenseHandler] = None,
        typesense_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.__class__._initialized:
            return
        self._db_handler = database_handler or DatabaseHandler(db_url=db_url)
        if typesense_handler is not None:
            self._typesense_handler = typesense_handler
        else:
            self._typesense_handler = TypesenseHandler(**(typesense_config or {}))
        self.__class__._initialized = True

    def get_db_handler(self) -> DatabaseHandler:
        return self._db_handler

    def get_typesense_handler(self) -> TypesenseHandler:
        return self._typesense_handler

    def close(self) -> None:
        self._db_handler.close_connection()
