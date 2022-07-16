from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional, Union


class AbstractCrawler(ABC):
    @abstractmethod
    def dumps(self) -> bytes:
        pass

    @abstractmethod
    def fetch(self, term: str, quantity: Optional[Union[int, str]] = None) -> Iterator[Dict[str, Any]]:
        pass

    @abstractmethod
    def loads(self, state: bytes) -> None:
        pass

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __str__(self) -> str:
        return self.__class__.__name__