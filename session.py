import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_
from config import user_agent
import pickle


def load_cookies():
    try:
        with open('src/cookies', 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        response = session.get('https://yandex.ru/maps', headers=headers)
        with open('src/cookies', 'wb') as file:
            pickle.dump(response.cookies, file)
        with open('src/cookies', 'rb') as file:
            return pickle.load(file)


CIPHERS = """ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA"""


class TlsAdapter(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(ciphers=CIPHERS, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru,en;q=0.9',
    'cache-control': 'max-age=0',
    'cookie': 'maps_los=0; yandexuid=9487894991674465594; yuidss=9487894991674465594; is_gdpr=0; is_gdpr_b=CPGsJRC8ogEoAg==; _yasc=CdHqv7s+d924PQ4uJgU+kKPo9tbFBhbdIWss9P7Hr0zjWT79strupdWsrGAT; i=WxpwSit/qRBaQiNz7/p3Jv4b+EQ7bPjkwqJLKoeK5y57cvPp7p7LJ9w6W7e63Je33Enc26Z8al0Yg8EPEGd94MFFb3c=; yashr=8447866831674465594; ymex=1989825604.yrts.1674465604; gdpr=0; _ym_uid=1674465605327520544; _ym_d=1674465605',
    'referer': 'https://yandex.ru/',
    'sec-ch-ua': '"Chromium";v="106", "Yandex";v="22", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'user-agent': user_agent
}
session = requests.session()
adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
session.mount("https://", adapter)
session.headers = headers
session.cookies = load_cookies()