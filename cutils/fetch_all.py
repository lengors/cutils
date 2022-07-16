import logging

from threading import Condition, Thread, current_thread
from typing import Any, Dict, Generic, Iterator, List, Optional, Tuple, TypeVar, Union

from .abstract_crawler import AbstractCrawler

T = TypeVar('T')


class Queue(Generic[T]):
    def __init__(self) -> None:
        self.__queue = list[T]()
        self.__condition = Condition()

    def push(self, item: T) -> None:
        with self.__condition:
            self.__queue.append(item)
            self.__condition.notify()

    def pop(self, block: bool = True) -> T:
        with self.__condition:
            while block and len(self.__queue) == 0:
                self.__condition.wait()
            return self.__queue.pop()

    def pop_all(self, block: bool = True) -> Iterator[T]:
        with self.__condition:
            while block and len(self.__queue) == 0:
                self.__condition.wait()
            while len(self.__queue) > 0:
                yield self.__queue.pop(0)


def fetch_each(queue: Queue[Union[Dict[str, Any], int]], crawler: AbstractCrawler, queries: List[Tuple[str, Optional[Union[int, str]]]]) -> None:
    for query in queries:
        try:
            for product in crawler.fetch(*query):
                queue.push(product)
        except Exception as e:
            logging.exception(e)
    queue.push(current_thread().ident)


def fetch_next(queue: Queue[Union[Dict[str, Any], int]], threads: Dict[int, Thread]) -> Iterator[Dict[str, Any]]:

    # Get products from queue
    products = queue.pop_all()

    # Process products
    for product in products:

        # Check if product is an identity
        if isinstance(product, int):

            # Remove thread from threads
            thread = threads.pop(product, None)

            # Check if thread exists
            if thread is not None:

                # Join thread
                thread.join()

        # Othewise check if product is not None
        elif product is not None:
            yield product


def fetch_all(crawlers: List[AbstractCrawler], *queries: Tuple[str, Optional[Union[int, str]]]) -> Iterator[Iterator[Dict[str, Any]]]:

    # Initialize queue
    queue = Queue[Union[Dict[str, Any], int]]()

    # Initialize threads
    threads = dict[int, Thread]()

    # Open threads
    for crawler in crawlers:

        # Create thread
        thread = Thread(target=fetch_each, args=(queue, crawler, queries))

        # Start thread
        thread.start()

        # Add thread to threads
        threads[thread.ident] = thread

    # While threads are running
    while len(threads) > 0:

        # Retrieve products
        yield fetch_next(queue, threads)

    # Yield any products left in queue
    yield queue.pop_all(block=False)
