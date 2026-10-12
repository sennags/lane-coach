"""Bounded Riot requests; credentials stay in the server process."""
import json
import math
import socket
import ssl
from email.utils import parsedate_to_datetime
from http.client import HTTPException
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


def transport_error_code(error):
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, ssl.SSLCertVerificationError):
        return 'tls_certificate_error'
    if isinstance(reason, ssl.SSLError):
        return 'tls_error'
    if isinstance(reason, socket.gaierror):
        return 'dns_error'
    if isinstance(reason, TimeoutError):
        return 'request_timeout'
    if isinstance(reason, OSError):
        return 'connection_error'
    return 'provider_unavailable'


class RiotClient:
    def __init__(self, key, reserve, clock):
        self.key, self.reserve, self.clock = key, reserve, clock
        self.opener = build_opener(NoRedirect())

    def get(self, path, platform=False):
        if not self.key:
            raise RiotError('not_configured')
        if (not isinstance(self.key, str) or not self.key.isascii()
                or any(not 33 <= ord(character) <= 126 for character in self.key)):
            raise RiotError('invalid_key', 3600)
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
            code = f'http_{error.code}' if isinstance(error.code, int) and 300 <= error.code <= 599 else 'provider_unavailable'
            raise RiotError(code) from None
        except (URLError, OSError) as error:
            # Classify types only; exception text can include URLs or credentials.
            raise RiotError(transport_error_code(error)) from None
        except HTTPException:
            raise RiotError('invalid_response') from None
        except (ValueError, UnicodeError):
            raise RiotError('invalid_response') from None
