import logging
import itertools

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional, Tuple, TypeVar, Union

from .abstract_crawler import AbstractCrawler

T = TypeVar('T')


def fetch_each(arguments: Tuple[AbstractCrawler, Tuple[str, Optional[Union[int, str]]]]) -> List[Dict[str, Any]]:
    crawler, query = arguments
    try:
        return list(crawler.fetch(*query))
    except Exception as e:
        logging.exception(e)
        return []


def fetch_all(crawlers: Iterator[AbstractCrawler], *queries: Tuple[str, Optional[Union[int, str]]]) -> Iterator[Tuple[AbstractCrawler, Tuple[str, Optional[Union[int, str]]], List[Dict[str, Any]]]]:
    with ThreadPoolExecutor() as executor:
        requests = list(itertools.product(crawlers, queries))
        for (crawler, query), products in zip(requests, executor.map(fetch_each, requests)):
            yield crawler, query, products
