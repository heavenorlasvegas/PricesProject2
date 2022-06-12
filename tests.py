from selenium import webdriver
from selenium.common import exceptions as sce
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.common.keys import Keys
from time import sleep
import matplotlib.pyplot as plt
import requests

cookies = {
    'spid': '1654899488636_315486f0f2f92590d883dc40a820bff7_m5mmnce3fau396ox',
    'exp': 'A2U_1leESkmNvJBPQ26mWQ.1',
    '_gcl_au': '1.1.111177779.1654899489',
    '_ga': 'GA1.2.72157160.1654899489',
    '_gid': 'GA1.2.1891593980.1654899489',
    'tmr_lvid': '115713441247917da0567bf2715a96cb',
    'tmr_lvidTS': '1654899489104',
    '_gaexp': 'GAX1.2.nMqftFPdSCWumFEQmfEIaQ.19232.0',
    '_ym_uid': '1654899489770796989',
    '_ym_d': '1654899489',
    '__ttl__widget__ui': '1654899489279-ef7e8abbb8b1',
    'popmechanic_sbjs_migrations': 'popmechanic_1418474375998%3D1%7C%7C%7C1471519752600%3D1%7C%7C%7C1471519752605%3D1',
    '_ym_isad': '1',
    '_tt_enable_cookie': '1',
    '_ttp': '8b8f6624-8a25-4fe3-b1d5-db241caad50a',
    'flocktory-uuid': '0b9ae515-3c48-48a8-96c6-b27016de01e3-2',
    'metrostore': '10',
    'UserSettings': 'SelectedStore={ffb8b2da-ac28-46a1-b737-3e53d2cd1667}',
    'fam_user': '6 5',
    'spsc': '1654956823747_d872a2f931e293c6e3dfb9da100926f6_d55bcf073b75337b3f2fc604837b4cde',
    'metroStoreId': '10',
    '_gat_family': '1',
    '_gat_gtag_UA_4033113_1': '1',
    '_gat_UA-4033113-1': '1',
    'tmr_detect': '1%7C1654956825390',
    '_ym_visorc': 'b',
    'mindboxDeviceUUID': 'b92de4a8-c4db-40de-a870-3c42109da4b4',
    'directCrm-session': '%7B%22deviceGuid%22%3A%22b92de4a8-c4db-40de-a870-3c42109da4b4%22%7D',
    'tmr_reqNum': '105',
}

headers = {
    'authority': 'online.metro-cc.ru',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,nb;q=0.6',
    'cache-control': 'max-age=0',
    # Requests sorts cookies= alphabetically
    # 'cookie': 'spid=1654899488636_315486f0f2f92590d883dc40a820bff7_m5mmnce3fau396ox; exp=A2U_1leESkmNvJBPQ26mWQ.1; _gcl_au=1.1.111177779.1654899489; _ga=GA1.2.72157160.1654899489; _gid=GA1.2.1891593980.1654899489; tmr_lvid=115713441247917da0567bf2715a96cb; tmr_lvidTS=1654899489104; _gaexp=GAX1.2.nMqftFPdSCWumFEQmfEIaQ.19232.0; _ym_uid=1654899489770796989; _ym_d=1654899489; __ttl__widget__ui=1654899489279-ef7e8abbb8b1; popmechanic_sbjs_migrations=popmechanic_1418474375998%3D1%7C%7C%7C1471519752600%3D1%7C%7C%7C1471519752605%3D1; _ym_isad=1; _tt_enable_cookie=1; _ttp=8b8f6624-8a25-4fe3-b1d5-db241caad50a; flocktory-uuid=0b9ae515-3c48-48a8-96c6-b27016de01e3-2; metrostore=10; UserSettings=SelectedStore={ffb8b2da-ac28-46a1-b737-3e53d2cd1667}; fam_user=6 5; spsc=1654956823747_d872a2f931e293c6e3dfb9da100926f6_d55bcf073b75337b3f2fc604837b4cde; metroStoreId=10; _gat_family=1; _gat_gtag_UA_4033113_1=1; _gat_UA-4033113-1=1; tmr_detect=1%7C1654956825390; _ym_visorc=b; mindboxDeviceUUID=b92de4a8-c4db-40de-a870-3c42109da4b4; directCrm-session=%7B%22deviceGuid%22%3A%22b92de4a8-c4db-40de-a870-3c42109da4b4%22%7D; tmr_reqNum=105',
    'dnt': '1',
    'if-none-match': 'W/"1499d3-K0fNzBBpLLwTMLKlrHebFcQufQo"',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
}

response = requests.get('https://api.metro-cc.ru/api/v1/C98BB1B547ECCC17D8AEBEC7116D6/20/suggestions', cookies=cookies, headers=headers)
print(response.text)



