import io
import imghdr
import base64
import pickle
import logging
import requests
import json as jslib

from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from calmjs.parse.parsers.es5 import Parser
from urllib.parse import parse_qs, urlparse
from typing import Any, Dict, Iterator, Mapping, Optional, Tuple, TypeVar, Union

from .data import Data
from .response import Response
from .abstract_crawler import AbstractCrawler

# Define generic bound to data
_T = TypeVar('_T', bound=Data)


# Define base crawler
class Crawler(AbstractCrawler, ABC):
    # Define JavaScript parser
    PARSER = Parser()

    def __init__(self, username: str, password: str, netloc: str, scheme: str = 'https') -> None:

        # Validate credentials and options
        if not isinstance(username, str):
            raise TypeError('Username must be a string')
        if not isinstance(password, str):
            raise TypeError('Password must be a string')
        if not isinstance(netloc, str):
            raise TypeError('Netloc must be a string')
        if not isinstance(scheme, str):
            raise TypeError('Scheme must be a string')
        if scheme not in ('http', 'https'):
            raise ValueError('Scheme must be either http or https')

        # Set credentials
        self.username = username
        self.password = password

        # Set options
        self.__netloc = netloc
        self.__scheme = scheme

        # Create session
        self.session = requests.Session()

        # Set default user-agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        })

    @abstractmethod
    def _fetch(self, term: str, quantity: int) -> Iterator[Dict[str, Any]]:
        pass

    def _preprocessing(self, content: bytes) -> Union[bytes, str]:

        # # Retrieve content
        return content

    @property
    def domain(self) -> str:
        return f'{self.__scheme}://{self.__netloc}'

    def dumps(self) -> bytes:

        # Dump cookies
        return pickle.dumps(self.session.cookies)

    def fetch(self, term: str, quantity: Optional[Union[int, str]] = None) -> Iterator[Dict[str, Any]]:
        try:
            term, quantity = self.validate(term, quantity)
            logging.info(f'Fetching term={term}, quantity={quantity}')
            return self._fetch(term, quantity)
        except Exception as e:
            logging.exception(e)
        return iter(())

    def fill(self, content: BeautifulSoup, payload: _T) -> _T:

        # Validate content as html
        if not isinstance(content, BeautifulSoup):
            raise TypeError(f'Content is not html: type={type(content)}')

        # Check payload
        if payload is None:
            return None

        # Validate payload
        elif not isinstance(payload, Mapping):
            raise TypeError(
                f'Payload is not a dictionary: type={type(payload)}')

        # Fill payload
        for key, current_value in payload.items():

            # Get field
            field = content.find(attrs={'name': key})

            # Check if field exists
            if field is not None:

                # Get field value
                value = field.get('value')

                # Check if value exists
                if value is not None:

                    # Set payload value
                    payload[key] = value

            # Check if field is required
            elif current_value is None:
                raise ValueError(f'Field {key} is required')

        # Return payload
        return payload

    def get(self, url: Union[str, bytes], params: Data = None, data: Data = None, headers: Data = None, json: Data = None) -> Response:

        # Make request
        return self.request('GET', url, params=params, data=data, headers=headers, json=json)

    def loads(self, state: bytes) -> None:

        # Loads cookies
        self.session.cookies.update(pickle.loads(state))

    @property
    def netloc(self) -> str:
        return self.__netloc

    def post(self, url: Union[str, bytes], params: Data = None, data: Data = None, headers: Data = None, json: Data = None) -> Response:

        # Make request
        return self.request('POST', url, params=params, data=data, headers=headers, json=json)

    def request(self, method: Union[str, bytes], url: Union[str, bytes], params: Data = None, data: Data = None, headers: Data = None, json: Data = None) -> Response:

        try:
            # Make request
            response = self.session.request(method, url, params=params,
                                            data=data, headers=headers, json=json)
        except requests.TooManyRedirects as e:
            return None, 1000, urlparse(url), dict()
        except requests.ConnectionError as e:
            logging.debug(f'{url}:{method}')
            logging.exception(e)
            return None, 1001, urlparse(url), dict()

        # Check status code
        if response.status_code != 200:

            # No content
            content = response.reason

        # Otherwise
        else:

            # Parse response content
            content = response.content.strip()

            # Check if response doesn't exist
            if len(content) == 0:
                content = None

            # Otherwise
            else:

                # Check if response is image
                stream = io.BytesIO(content)
                imgtype = imghdr.what(stream)
                if imgtype is not None:
                    content = base64.b64encode(content)
                    content = content.decode()
                    content = f'data:image/{imgtype};base64,{content}'

                # Otherwise
                else:

                    # Try to parse response as json
                    try:
                        content = jslib.loads(content)
                    except (jslib.JSONDecodeError, UnicodeDecodeError):

                        # Try to parse response as JavaScript
                        try:
                            content = self.PARSER.parse(content.decode())
                        except (SyntaxError, UnicodeDecodeError):

                            # Parse response as html
                            content = BeautifulSoup(
                                self._preprocessing(content), 'html5lib')

        # Parse url
        url = urlparse(response.url)

        # Return response
        return content, response.status_code, url, parse_qs(url.query)

    @property
    def scheme(self) -> str:
        return self.__scheme

    def validate(self, term: str, quantity: Optional[Union[int, str]] = None) -> Tuple[str, int]:
        # Parse term
        if not isinstance(term, str):
            raise TypeError('Term must be a string')

        # Parse quantity
        if quantity is None:
            quantity = 4
        elif isinstance(quantity, str):
            if not quantity.isdigit():
                raise ValueError('Quantity must be an integer')
            quantity = int(quantity)
        elif not isinstance(quantity, int):
            raise TypeError(
                'Quantity must be an integer or an integer string or None')

        # Return term and quantity
        return term, quantity
