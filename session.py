import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_

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
    'accept-language': 'ru, en; q=0.9',
    'cache-control': 'max-age=0',
    'cookie': 'maps_los=0; yandexuid=3963249841672331441; yuidss=3963249841672331441; is_gdpr=0; is_gdpr_b=CJaLGxDrnQEoAg==; i=o+xcR39P19Ptumjr8fIXRe+annkYR1+j7fOYjBhQaXjQgDI4beUWB6PfY4z2CCblS632JnceJx5TleFgHYPgzHlP5Vo=; _yasc=smprKqgRniPXjVmhi9xjcZsZQx1r4i0lUGKYbE/4d2zxVUUJDZtT/26H8cHEJK8=; ymex=1987691443.yrts.1672331443; gdpr=0; _ym_uid=1672331420578896976; _ym_d=1672331421; _ym_isad=2',
    'sec-ch-ua': 'Chromium;v=106, Yandex;v=22, Not;A=Brand;v=99',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': 'Windows',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.3.823 Yowser/2.5 Safari/537.36',
    'viewport-width': '1470'
}
session = requests.session()
adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
session.mount("https://", adapter)
