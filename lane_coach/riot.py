"""Bounded Riot requests; credentials stay in the server process."""
import json
import math
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class RiotError(Exception):
    def __init__(self, code, retry_after=60):
        super().__init__(code)
        self.code = code
        self.retry_after = retry_after


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, *args, **kwargs):
        # Never forward X-Riot-Token to a redirect destination.
        return None


class RiotClient:
    def __init__(self, key, reserve, clock):
        self.key, self.reserve, self.clock = key, reserve, clock
        self.opener = build_opener(NoRedirect())

    def get(self, path, platform=False):
        if not self.key:
            raise RiotError('not_configured')
        self.reserve()
        host = 'br1' if platform else 'americas'
        request = Request(f'https://{host}.api.riotgames.com{path}',
                          headers={'X-Riot-Token': self.key, 'Accept': 'application/json'})
        try:
            with self.opener.open(request, timeout=6) as response:
                raw = response.read(8_000_001)
            if len(raw) > 8_000_000:
                raise RiotError('invalid_response')
            return json.loads(raw)
        except HTTPError as error:
            retry = 120
            if error.code == 429:
                value = error.headers.get('Retry-After', '120') if error.headers else '120'
                try:
                    retry = float(value)
                except (TypeError, ValueError):
                    try:
                        retry = parsedate_to_datetime(value).timestamp() - self.clock()
                    except (TypeError, ValueError, OverflowError):
                        retry = 120
                if not math.isfinite(retry):
                    retry = 120
                raise RiotError('rate_limited', max(1, retry)) from None
            if error.code in (401, 403):
                raise RiotError('unauthorized', 3600) from None
            if error.code == 404:
                raise RiotError('not_found') from None
            raise RiotError('provider_unavailable') from None
        except (URLError, TimeoutError, OSError):
            raise RiotError('provider_unavailable') from None
        except (ValueError, UnicodeError):
            raise RiotError('invalid_response') from None
