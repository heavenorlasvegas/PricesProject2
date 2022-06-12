
import selenium
from selenium import webdriver
from selenium.common import exceptions as sce
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.common.keys import Keys
from time import sleep
#import matplotlib.pyplot as plt
import requests
import re
import streamlit as st


def get_address(city):
    entrypoint = "https://nominatim.openstreetmap.org/search"
    params = {'q': city,
              'format': 'geojson'}
    r = requests.get(entrypoint, params=params).json()["features"]
    city_data = list(filter(lambda x: x["properties"]["type"] in ["city", "town", "village"], r))
    city_coord = city_data[0]["geometry"]["coordinates"]

    entrypoint = "https://nominatim.openstreetmap.org/reverse.php"
    offset = [0, 0]
    house_number = ""
    road = ""
    while not house_number or not road:
        if offset[0] > 0.01:
            return city + " улица 76"  # что-то пошло не так, ищем дом 76 на рандомной улице
        params = {'lon': city_coord[0] + offset[0], 'lat': city_coord[1] + offset[1],
                  'format': 'json', 'zoom': 18}
        r = requests.get(entrypoint, params=params).json()["address"]
        if "house_number" in r:
            house_number = r["house_number"]
        if "road" in r:
            road = r["road"]
        offset[0] += 0.001
        offset[1] += 0.001
    return ", ".join([city, road, house_number])


def scrape_prices(city, ingredient, category=""):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    driver.set_page_load_timeout(10)

    def sel(selector):
        return driver.find_elements(By.CSS_SELECTOR, selector)



    while not sel("input.search-bar__input") and not sel("input.header__search-i"):
        try:
            driver.get("https://online.metro-cc.ru")
        except sce.TimeoutException:
            pass

    new_version = bool(sel("input.search-bar__input"))
    if new_version:
        s = {'search': "input.search-bar__input",
             'catalog': "div.catalog-filters-categories",
             'index': 0,
             'delivery': "button.header-address__receive-button",
             'product': "div.base-product-item__content-details",
             'product_name': "a.base-product-name",
             'more_button': "button.subcategory-or-type__load-more"}
    else:
        s = {'search': "input.header__search-i",
             'catalog': "div.catalog-filters_links",
             'index': 1,
             'delivery': "div.header-delivery-info",
             'product': "div.catalog-item__top",
             'product_name': "a.catalog-item_name",
             'more_button': "a.catalog-load-more__button"}

    sel(s['delivery'])[0].click()
    driver.find_element(By.ID, "search-input").send_keys(get_address(city))

    sel("button.obtainment-delivery__apply-btn-desktop")[0].click()
    sleep(1)
    sel("button.obtainment-delivery__apply-btn-desktop")[0].click()

    sel(s['search'])[s['index']].send_keys(ingredient)
    sel(s['search'])[s['index']].send_keys(Keys.ENTER)

    sleep(3)

    if category:
        category_links = sel(s['catalog'])[0].find_elements(By.TAG_NAME, "a")
        for link in category_links:
            if link.get_attribute("innerHTML").find(category) > -1:
                link.click()

    while sel(s['more_button']):
        try:
            sel(s['more_button'])[0].click()
        except selenium.common.exceptions.ElementNotInteractableException:
            print('проблема с кнопкой')
        sleep(3)

    products = driver.find_elements(By.CSS_SELECTOR, s['product'])
    rows = []
    for product in products:
        name = product.find_element(By.CSS_SELECTOR, s['product_name']).text
        if not name:
            continue
        else:
            if new_version:
                price = float(product.find_elements(By.CSS_SELECTOR, "span.base-product-prices__actual-sum")[0]
                              .get_attribute("innerHTML").replace("&nbsp;", ""))
                unit = sel("span.base-product-prices__actual-unit")[0].get_attribute("innerHTML")[1:]
            else:

                def detect_price(pr):
                    pr = pr.get_attribute('innerHTML').replace(" ", "")
                    if re.findall("([\d.]+)", pr):
                        return float(re.findall("([\d.]+)", pr)[0])
                    else:
                        return float("nan")

                price_and_unit = product.find_elements(
                    By.CSS_SELECTOR, "div.catalog-item_price-lvl_current, div.catalog-item_price-current")[0]
                if price_and_unit.get_attribute("innerHTML").find("Нет") > -1:
                    continue
                price = detect_price(price_and_unit)
                unit = price_and_unit.find_elements(By.TAG_NAME, "span")[0].get_attribute("innerHTML")[1:]
            rows.append([name, price, unit])
    df = pd.DataFrame(rows, columns=["name", "price", "unit"])
    driver.quit()
    return df
def scrape():
    st.write(scrape_prices('Воронеж', 'торт', 'Торты, пироги, пирожные'))
st.button(label="Начать скрэппинг", on_click=scrape)
