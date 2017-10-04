# coding: utf-8
# python: 2.7.8 [PyPy 2.4.0 with GCC 4.9.2]
# module: btcelib.py <http://pastebin.com/kABSEyYB>
# import: simplejson <https://pypi.python.org/pypi/simplejson>

"""BTC-E Public API v3 and Trade API v1

The MIT License (MIT) <http://opensource.org/licenses/MIT>.
Copyright (c) 2014, 2015, 2016, John Saturday <stozher@gmail.com>.

THE BTC-E IS NOT AFFILIATED WITH THIS PROJECT. THIS IS A COMPLETELY
INDEPENDENT IMPLEMENTATION BASED ON THE ONLINE BTC-E API DESCRIPTION:

BTC-E Public API v3 <https://btc-e.com/api/3/docs>
BTC-E Trade API v1 <https://btc-e.com/tapi/docs>

EXAMPLE:
    >>> import btcelib
    >>> from pprint import pprint
    >>> papi = btcelib.PublicAPIv3('btc_usd-ltc_xxx')
    >>> data = papi.call('ticker', ignore_invalid=1)
    >>> pprint(data)
    >>> # The next instance use the same connection...
    >>> apikey = {    # Replace with your API key/secret!
    ...     'Key': 'YOUR-KEY',
    ...     'Secret': 'YOUR-SECRET',
    ...     }
    >>> tapi = btcelib.TradeAPIv1(apikey, compr=True)
    >>> data = tapi.call('TradeHistory', pair='btc_usd', count=2)
    >>> pprint(data)

CLASSES:
    __builtin__.object
        BTCEConnection
            PublicAPIv3
            TradeAPIv1
    exceptions.Exception(exceptions.BaseException)
        APIError

class btcelib.BTCEConnection([compr=None[, timeout=30]]):
    BTC-E Public/Trade API persistent HTTPS connection.

    BTCEConnection.jsonrequest(url[, apikey=None[, **params]]):
        Create query to the BTC-E API (JSON response).

    BTCEConnection.apirequest(url[, apikey=None[, **params]]):
        Create query to the BTC-E API (decoded response).

    BTCEConnection.conn - shared httplib.HTTPSConnection

class btcelib.PublicAPIv3([*pairs[, **connkw]]):
    BTC-E Public API v3 (see: online documentation).

    PublicAPIv3.call(method[, **params]):
        Create query to the BTC-E Public API v3.
        method: info | ticker | depth | trades
        params: limit=150 (max: 2000), ignore_invalid=0

class btcelib.TradeAPIv1(apikey[, **connkw]):
    BTC-E Trade API v1 (see: online documentation).

    TradeAPIv1.call(method[, **params]):
        Create query to the BTC-E Trade API v1.
        method: getInfo | Trade | ActiveOrders | OrderInfo |
            CancelOrder | TradeHistory (max: 2000) |
            TransHistory (max: 2000)
        method*: WithdrawCoin | CreateCoupon | RedeemCoupon
        params: param1=value1, param2=value2, ..., paramN=valueN

EXCEPTIONS:
    btcelib.APIError, httplib.HTTPException, socket.error

exception btcelib.APIError(exceptions.Exception):
    Raise exception when the BTC-E API returned an error."""

__date__ = "2016-10-25T16:35:22+0300"
__author__ = """John Saturday <stozher@gmail.com>
BTC: 13buUVsVXG5YwhmP6g6Bgd35WZ7bKjJzwM
LTC: Le3yV8mA3a7TrpQVHzpSSkBmKcd2Vw3NiR"""
__credits__ = "Alan McIntyre <https://github.com/alanmcintyre>"

from http.cookies import CookieError
from http.cookies import SimpleCookie
import errno
from http import client as httplib
import socket
import codecs
from decimal import Decimal
from hashlib import sha512 as _sha512
from hmac import new as newhash
from re import search
from urllib.parse import urlencode
from zlib import MAX_WBITS as _MAX_WBITS, decompress as _zdecompress


try:
    from simplejson import loads as jsonloads
except ImportError:
    from json import loads as jsonloads

API_REFRESH = 2            # data refresh time
BTCE_HOST = 'wex.nz'       # BTC-E host (HTTP/SSL)
CF_COOKIE = '__cfduid'     # CloudFlare security cookie
HTTP_TIMEOUT = 60          # connection timeout (max 60 sec)


class APIError(Exception):
    "Raise exception when the BTC-E API returned an error."
    pass

class BTCEConnection(object):
    """BTC-E Public/Trade API persistent HTTPS connection.
    @cvar conn: shared httplib.HTTPSConnection between instances"""
    _headers = {    # common HTTPS headers
        'Accept': 'application/json',
        'Accept-Charset': 'utf-8',
        'Accept-Encoding': 'identity',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        }
    _post_headers = {    # common and POST headers
        'Content-Type': 'application/x-www-form-urlencoded',
        }
    _resp = None    # type 'httplib.HTTPResponse'
    conn = None     # type 'httplib.HTTPSConnection'

    @classmethod
    def __init__(cls, compr=None, timeout=HTTP_TIMEOUT):
        """Initialization of shared HTTPS connection.
        @param compr: HTTPS compression (default: identity)
        @param timeout: connection timeout (max: 60 sec)"""
        if compr is False:
            compr = 'identity'
        elif compr is True:
            compr = 'gzip, deflate'

        if not cls.conn:
            # Create new connection.
            cls.conn = httplib.HTTPSConnection(
                BTCE_HOST,
                timeout=timeout
            )
            cls._post_headers.update(cls._headers)
        elif timeout != cls.conn.timeout:
            # update: connection timeout
            cls.conn.timeout = timeout
            cls.conn.close()

        if compr and compr != cls._headers['Accept-Encoding']:
            # update: connection compression
            cls._headers['Accept-Encoding'] = compr
            cls._post_headers.update(cls._headers)
            cls.conn.close()

    @classmethod
    def _signature(cls, apikey, msg):
        """Calculation of the SHA-512 authentication signature.
        @param apikey: Trade API-Key {'Key': 'KEY', 'Secret': 'SECRET'}
        @param msg: Trade API method and parameters"""
        sign = newhash(str.encode(apikey['Secret']), msg=str.encode(msg), digestmod=_sha512)
        cls._post_headers['Key'] = apikey['Key']
        cls._post_headers['Sign'] = sign.hexdigest()

    @classmethod
    def _setcookie(cls):
        "Get the CloudFlare cookie and update security."
        cookie_header = cls._resp.getheader('Set-Cookie')
        try:
            cf_cookie = SimpleCookie(cookie_header)[CF_COOKIE]
        except (CookieError, KeyError):
            pass    # XXX: with/out previous cookie
        else:
            cls._headers['Cookie'] = cf_cookie.OutputString('value')
            cls._post_headers['Cookie'] = cls._headers['Cookie']

    @classmethod
    def _decompress(cls, data):
        """Decompress connection response.
        @return: decompressed data <type 'str'>"""
        encoding = cls._resp.getheader('Content-Encoding')
        if encoding == 'gzip':
            data = _zdecompress(data, _MAX_WBITS+16)
        elif encoding == 'deflate':
            data = _zdecompress(data, -_MAX_WBITS)
        # XXX: failback to 'identity' encoding
        return data

    @classmethod
    def jsonrequest(cls, url, apikey=None, **params):
        """Create query to the BTC-E API (JSON response).
        @raise httplib.HTTPException, socket.error: connection errors
        @param url: Public/Trade API plain URL without parameters
        @param apikey: Trade API Key {'Key': 'KEY', 'Secret': 'SECRET'}
        @param **params: Public/Trade API method and/or parameters
        @return: BTC-E API response (JSON data) <type 'str'>"""
        if apikey:
            # args: Trade API
            method = 'POST'
            body = urlencode(params)
            cls._signature(apikey, body)
            headers = cls._post_headers
        else:
            # args: Public API
            method = 'GET'
            if params:
                url = '{}?{}'.format(url, urlencode(params))
            body = None
            headers = cls._headers
        while True:
            # Make HTTPS request.
            try:
                cls.conn.request(method, url, body=body, headers=headers)
                cls._resp = cls.conn.getresponse()
            except httplib.BadStatusLine:
                cls.conn.close()
                continue
            except socket.error as error:
                cls.conn.close()
                if error.errno != errno.ECONNRESET:
                    raise
                continue
            except httplib.HTTPException:
                cls.conn.close()
                raise
            cls._setcookie()
            break    # Connection succeeded.
        reader = codecs.getreader("utf-8")
        return cls._decompress(reader(cls._resp).read())

    @classmethod
    def apirequest(cls, url, apikey=None, **params):
        """Create query to the BTC-E API (decoded response).
        @raise APIError, httplib.HTTPException: BTC-E and CloudFlare errors
        @param url: Public/Trade API plain URL without parameters
        @param apikey: Trade API Key {'Key': 'KEY', 'Secret': 'SECRET'}
        @param **params: Public/Trade API method and/or parameters
        @return: BTC-E API response (decoded data) <type 'dict'>"""
        data = cls.jsonrequest(url, apikey, **params)
        try:
            data = jsonloads(data, parse_float=Decimal, parse_int=Decimal)
        except ValueError:
            if cls._resp.status != httplib.OK:
                # CloudFlare HTTP errors
                raise httplib.HTTPException("{} {}".format(
                    cls._resp.status, cls._resp.reason))
            else:
                # BTC-E API unknown errors
                raise APIError(str(data) or "Unknown Error")
        else:
            if 'error' in data:
                # BTC-E API standard errors
                raise APIError(str(data['error']))
        return data

class PublicAPIv3(BTCEConnection):
    "BTC-E Public API v3 <https://btc-e.com/api/3/docs>."
    def __init__(self, *pairs, **connkw):
        """Initialization of the BTC-E Public API v3.
        @param *pairs: [btc_usd[-btc_rur[-...]]] or arguments
        @param **connkw: ... (see: 'BTCEConnection' class)"""
        super(PublicAPIv3, self).__init__(**connkw)
        self.pairs = pairs    # type 'str' (delimiter: '-')

        # Get and/or join BTC-E pairs.
        if not self.pairs:
            self.pairs = self.call('info')['pairs'].items()
        if not isinstance(self.pairs, str):
            self.pairs = '-'.join(self.pairs)

    async def call(self, method, **params):
        """Create query to the BTC-E Public API v3.
        @param method: info | ticker | depth | trades
        @param **params: limit=150 (max: 2000), ignore_invalid=0
        @return: ... <type 'dict'> (see: online documentation)"""
        if method == 'info':
            url = '/api/3/{}'.format(method)
        else:    # method: ticker, depth, trades
            url = '/api/3/{}/{}'.format(method, self.pairs)
        return self.apirequest(url, **params)

class TradeAPIv1(BTCEConnection):
    "BTC-E Trade API v1 <https://btc-e.com/tapi/docs>."
    def __init__(self, apikey, **connkw):
        """Initialization of the BTC-E Trade API v1.
        @raise APIError: where no 'invalid nonce' in error
        @param apikey: Trade API Key {'Key': 'KEY', 'Secret': 'SECRET'}
        @param **connkw: ... (see: 'BTCEConnection' class)"""
        super(TradeAPIv1, self).__init__(**connkw)
        self._apikey = apikey            # type 'dict' (keys: 'Key', 'Secret')
        self.nonce = self._getnonce()    # type 'long' (min/max: 1-4294967294)

    def _getnonce(self):
        """Get nonce value from BTC-E API error.
        @return: nonce parameter <type 'long'>"""
        try:
            self.apirequest('/tapi', self._apikey, nonce=None)
        except APIError as error:
            message = str(error)
            if 'invalid nonce' not in message:
                raise
            return int(search(r'\d+', message).group())
        else:
            raise APIError("Unknown 'nonce' parameter")

    def _nextnonce(self):
        """Get next nonce POST parameter.
        @return: nonce parameter <type 'long'>"""
        self.nonce += 1
        return self.nonce

    async def call(self, method, **params):
        """Create query to the BTC-E Trade API v1.
        @param method: getInfo | Trade | ActiveOrders | OrderInfo |
            CancelOrder | TradeHistory (max: 2000) | TransHistory (max: 2000)
        @param method*: WithdrawCoin | CreateCoupon | RedeemCoupon
        @param **params: param1=value1, param2=value2, ..., paramN=valueN
        @return: ... <type 'dict'> (see: online documentation)"""
        params['method'] = method
        params['nonce'] = self._nextnonce()
        return self.apirequest('/tapi', self._apikey, **params)['return']
