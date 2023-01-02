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
    'accept-language': 'ru,en;q=0.9',
    'cache-control': 'max-age=0',
    'cookie': 'maps_los=0; maps_theme=s; yandexuid=711543871665599802; yuidss=711543871665599802; _ym_uid=16655998041011732940; _ym_d=1665599804; is_gdpr=0; is_gdpr_b=CJ2cGhCdjwEoAg==; L=XhdTXVp8Y3Z/U3FXUkF9VX9FdFB/Zl1gQTBeIk04MC0sHSpZRWA=.1665599842.15128.371660.7a8faff1f84c9fdd0a011a7b54e5ae16; yandex_login=telitsinivan05; my=YwA=; gdpr=0; ymex=1980959803.yrts.1665599803#1980959899.yrtsi.1665599899; font_loaded=YSv1; skid=3465527391667506905; i=+d1V+wyom37BgIHC6A9v1Xkw+hFIE0qG2HDO1OYHBAhRP9WRtmaedcVWID2o0De3Jaro/WsXV19SkWw6SE51g+CZpHY=; sae=0:85538D18-B2A8-46EB-8437-08BDC192AACC:p:22.11.3.823:m:d:RU:20221012; instruction=1; Session_id=3:1672575760.5.0.1665599842401:Hjz8bQ:43.1.2:1|1462882106.0.2|3:10263459.907490.fchKL4lvTadQ3x1AeI6rI7oNoA4; sessionid2=3:1672575760.5.0.1665599842401:Hjz8bQ:43.1.2:1|1462882106.0.2|3:10263459.907490.fakesign0000000000000000000; _ym_isad=2; yabs-frequency=/5/LG000DV4icC00000/WQaQFolcFbiqIa2_2TngfI-KL3HAG000/; _yasc=XGwkPk9PfXKYdaSsGnFQwYvJZjN/dThr1WV5oQhVCnpvd5Ihj0pvJ9wGW+fZnEqyMeqJNUxg4xW8cR5dtV2KWv/k+yt/4w==; _ym_visorc=b; spravka=dD0xNjcyNjYyNjMwO2k9MzEuMTQ4LjI0OC4yMzQ7RD00NDcwNkI5QUI0NTNDRTRCOUVDMDk1N0VCNEFCRDgxRUM0NUUyMzNGMUYyNjI3RDcxQjEyMzc3QUZCRjE2RkZDMTMyMjE5NDJFRTgwRDcyQ0JBMDZCMjFBRENCOUREO3U9MTY3MjY2MjYzMDIyODg0MTc4NDtoPThkOTZhNGI4M2ZlZWU3YjAwYzVjMmQ2NGY0MjQ1OTk4; ys=svt.1#def_bro.1#ead.C5C8A923#wprid.1672663844213261-11267109776155207246-sas5-9950-2d8-sas-l7-balancer-8080-BAL-9843#ybzcc.ru#newsca.native_cache; yp=1682664051.szm.2:1470x956:1470x820#1697135849.cld.1955450#1700807746.pgp.5_27821155#1988023845.pcs.1#1673181912.mcv.0#1673181912.mcl.14iu38k#1672670677.gpauto.55_755863:37_617699:100000:3:1672663477#1672671145.nycrsr.1',
    'device-memory': '8',
    'downlink': '10',
    'dpr': '2',
    'ect': '4g',
    'rtt': '50',
    'sec-ch-ua': '"Chromium";v="106", "Yandex";v="22", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
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
