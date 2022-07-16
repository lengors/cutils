from bs4 import BeautifulSoup
from urllib.parse import ParseResult
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union


# Define response type
Response = Tuple[Optional[Union[str, bytes, BeautifulSoup,
                                Dict[Any, Any]]], int, ParseResult, Mapping[str, Iterable[str]]]
