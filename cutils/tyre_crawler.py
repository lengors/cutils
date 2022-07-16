import os
import re
import dateparser
import unicodedata

from urllib.parse import urljoin
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

from .crawler import Crawler


# Define base tyre crawler
class TyreCrawler(Crawler):
    def __init__(self, username: str, password: str, netloc: str, scheme: str = 'https') -> None:

        # Initialize superclass
        super().__init__(username, password, netloc, scheme)

    def parse(self, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f'Value must be a string')
        return unicodedata.normalize('NFD', value).encode('ascii', 'ignore').decode('ascii')

    def parse_brand(self, brand: Optional[str]) -> Optional[str]:
        if brand is None:
            return None
        elif isinstance(brand, str):
            information = re.search(r'\(.*?\)', brand)
            if information is not None:
                start, end = information.start(), information.end()
                brand = ' '.join((brand[:start], brand[end:]))
            brand = self.parse_text(brand)
            return None if brand is None else ' '.join((name.capitalize() for name in brand.split(' ')))
        raise TypeError(f'Unable to parse brand for type: {type(brand)}')

    def parse_consumption_or_grip(self, consumption_or_grip: Optional[str]) -> Optional[str]:
        if consumption_or_grip is None:
            return None
        elif isinstance(consumption_or_grip, str):
            consumption_or_grip = self.parse_text(consumption_or_grip)
            if consumption_or_grip is None:
                return None
            consumption_or_grip = consumption_or_grip.upper()
            consumption_or_grip = re.search('[A-Z]$', consumption_or_grip)
            if consumption_or_grip is not None:
                consumption_or_grip = consumption_or_grip.group(0)
            return consumption_or_grip
        raise TypeError(
            f'Unable to parse grip for type: {type(consumption_or_grip)}')

    def parse_decibels(self, decibels: Optional[Union[str, int]]) -> Optional[int]:
        if decibels is None:
            return None
        elif isinstance(decibels, str):
            decibels = self.parse_text(decibels)
            if decibels is None:
                return None
            decibels = re.search(r'[0-9]{2}', decibels)
            if decibels is not None:
                decibels = decibels.group(0)
                decibels = int(decibels)
                return decibels if decibels > 0 else None
            return None
        elif isinstance(decibels, int):
            return decibels if decibels > 0 else None
        raise TypeError(f'Unable to parse decibels for type: {type(decibels)}')

    def parse_delivery(self, delivery: Optional[Union[datetime, str]]) -> Optional[datetime]:
        if delivery is None:
            return None
        elif isinstance(delivery, datetime):
            return delivery
        elif isinstance(delivery, str):
            delivery = self.parse(delivery)
            delivery = delivery.lower()
            delivery = re.sub(r'inicio\s+de\s+', '1 de ', delivery)
            match = re.search(
                r'(([1-2][0-9])|(([0])?[1-9])|(3[0-1]))\s+de\s+\w+', delivery)
            if match is not None:
                delivery = match.group(0)
            else:
                match = re.search(
                    r'(depois\s+de\s+)?(amanha|hoje)(\s+de\s+(manha|tarde))?', delivery)
                if match is not None:
                    date = dateparser.parse(match.group(2), settings={
                        'SKIP_TOKENS': ['o', 't', 'da', 'de', 'do'],
                        'PREFER_DATES_FROM': 'future',
                        'DATE_ORDER': 'DMY',
                    })
                    if match.group(1) is not None:
                        date += timedelta(days=1)
                    if match.group(4) == 'manha':
                        date = date.replace(hour=10)
                    elif match.group(4) == 'tarde':
                        date = date.replace(hour=16)
                    else:
                        date = date.replace(hour=0)
                    if date is not None:
                        date = date.replace(minute=0, second=0, microsecond=0)
                    return date
            date = dateparser.parse(delivery, settings={
                'SKIP_TOKENS': ['o', 't', 'da', 'de', 'do'],
                'PREFER_DATES_FROM': 'future',
                'DATE_ORDER': 'DMY',
            })
            if date is not None:
                date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            return date
        raise TypeError(f'Unable to parse delivery for type: {type(delivery)}')

    def parse_description(self, description: Optional[str]) -> Optional[str]:
        if description is None:
            return None
        elif isinstance(description, str):
            description = self.parse_text(description)
            return None if description is None else description.upper()
        raise TypeError(
            f'Unable to parse description for type: {type(description)}')

    def parse_image(self, image: Optional[str]) -> Tuple[str, str]:
        if image is None:
            return None, None
        elif not isinstance(image, str):
            raise TypeError(f'Image must be a string')
        if len(image.strip()) == 0:
            return None, None
        return urljoin(self.domain, image), self.parse_path(image)

    def parse_noise(self, noise: Optional[Union[str, int]]) -> Optional[int]:
        if noise is None:
            return None
        elif isinstance(noise, str):
            noise = self.parse_text(noise)
            if noise is None:
                return None
            noise = noise.upper()
            match = re.search(r'[A-C]', noise)
            if match is not None:
                return ord(match.group(0)) - ord('A') + 1
            match = re.search(r'[1-3]', noise)
            if match is not None:
                return int(match.group(0))
            return None
        elif isinstance(noise, int):
            return noise if noise > 0 else None
        raise TypeError(f'Unable to parse noise for type: {type(noise)}')

    def parse_path(self, path: Optional[str]) -> Optional[str]:
        if path is None:
            return None
        elif not isinstance(path, str):
            raise TypeError(f'Path must be a string')
        _, name = os.path.split(path)
        name, _ = os.path.splitext(name)
        return name

    def parse_price(self, price: Optional[Union[str, float, int]], prefer_period: bool = False) -> Optional[float]:
        if not isinstance(prefer_period, bool):
            raise TypeError(f'Prefer period must be a boolean')
        if price is None:
            return None
        elif isinstance(price, int):
            return float(price)
        elif isinstance(price, float):
            return price
        elif isinstance(price, str):

            # Remove all spaces
            price = re.sub(r'\s+', '', price.strip())

            # Define regexes for different price formats
            pattern_prefer_comma = '(?P<comma>\d+(\.\d{3})*(\,\d{2})?)(\€|\£|\$|\§)?'
            pattern_prefer_period = '(?P<period>\d+(\,\d{3})*(\.\d{2})?)(\€|\£|\$|\§)?'
            pattern = f'({pattern_prefer_period}|{pattern_prefer_comma})' if prefer_period else f'({pattern_prefer_comma}|{pattern_prefer_period})'
            pattern = re.compile(pattern)

            # Try to match the price with all formats
            match = pattern.search(price)
            if match is None:
                return None

            # Get the price if it was matched (period)
            match_period = match.group('period')
            if match_period is not None:
                match_period = float(match_period.replace(',', ''))

            # Get the price if it was matched (comma)
            match_comma = match.group('comma')
            if match_comma is not None:
                match_comma = float(match_comma.replace(
                    '.', '').replace(',', '.'))

            # Set test match
            match_test = (match_period, match_comma) if prefer_period else (
                match_comma, match_period)

            # Check first match
            for match in match_test:
                if match is not None and match > 0:
                    return match
            return None
        raise TypeError(f'Unable to parse price for type: {type(price)}')

    def parse_stock(self, stock: Optional[Union[float, int, str]]) -> Tuple[Optional[str], int, Optional[str]]:
        if stock is None:
            return None, 0, None
        elif isinstance(stock, int):
            return None, stock, None
        elif isinstance(stock, str):
            match = re.search(r'(\>|\<|\+|\-)?\s*(\d+)', stock)
            if match is None:
                return None, 0, None
            extraction = ' '.join((stock[:match.start()], stock[match.end():]))
            extraction = self.parse_text(extraction)
            modifier = match.group(1)
            quantity = int(match.group(2))
            if modifier is not None:
                modifier = re.sub(r'\+', '>', modifier)
                modifier = re.sub(r'\-', '<', modifier)
            if int(quantity) < 2 and modifier == '<':
                return None, 0, extraction
            return modifier, quantity, extraction
        elif isinstance(stock, float):
            return None, int(stock), None
        raise TypeError(f'Unable to parse stock for type: {type(stock)}')

    def parse_text(self, text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        elif isinstance(text, str):
            text = re.sub(r'\s+', ' ', text.strip())
            return text if len(text) > 0 else None
        raise TypeError(f'Unable to parse text for type: {type(text)}')
