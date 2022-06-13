import numpy as np
import selenium
from selenium import webdriver
from selenium.common import exceptions as sce
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.common.keys import Keys
from time import sleep
#import matplotlib.pyplot as plt
import requests
import re
import streamlit as st
import undetected_chromedriver as uc
from datetime import date
from google.oauth2 import service_account
from gsheetsdb import connect


with st.echo(code_location='below'):
    def scrape_prices(city, ingredient, category=""):

        # ЧАСТЬ 1. Проверяем, не собраны ли уже данные
        with st.spinner("Ищу данные в таблице..."):
            db = st.secrets["private_gsheets_url"]
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])

            db_conn = connect(credentials=credentials)
            today = date.today().strftime("%d.%m.%Y")
            get_data = f'SELECT name, price, unit, price_per_kg, price_per_l FROM "{db}" WHERE ingredient = "{ingredient}" AND city = "{city}" AND date = "{today}"'
            existing_data = pd.read_sql(get_data, db_conn)
        if not existing_data.empty:
            return existing_data
        else:


            # ЧАСТЬ 2. Скрэппинг
            try:
                with st.spinner("Запускаю виртуальный браузер..."):

                    options = webdriver.ChromeOptions()
                    options.headless = True

                    # FROM: https://github.com/Franky1/Streamlit-Selenium/blob/main/streamlit_app.py
                    options.add_argument("--headless")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-features=NetworkService")
                    options.add_argument("--window-size=1920x1080")
                    options.add_argument("--disable-features=VizDisplayCompositor")
                    driver = uc.Chrome(options=options)
                    # END FROM
                    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                    driver.set_page_load_timeout(5)

                with st.spinner("Подключаюсь к сайту Metro..."):
                    def sel(selector):
                        return driver.find_elements(By.CSS_SELECTOR, selector)


                    c = 0
                    while not sel("input.search-bar__input") and not sel("input.header__search-i"):
                        try:
                            c += 1
                            if c <= 10:
                                driver.get("http://online.metro-cc.ru")
                                sleep(1)
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

                with st.spinner("Выбираю город..."):

                    sel(s['delivery'])[0].click()


                    sel(".obtainments-list__content")[1].click()
                    sel("div.select-item__input")[0].click()
                    sleep(0.3)
                    sel("input.multiselect__input")[0].send_keys(city)
                    sel("input.multiselect__input")[0].send_keys(Keys.ENTER)
                    sleep(0.3)
                    sel("div.pickup__apply-btn-desk button")[0].click()
                    sleep(0.3)


                with st.spinner("Ищу продукты..."):

                    sel(s['search'])[s['index']].send_keys(ingredient)
                    sel(s['search'])[s['index']].send_keys(Keys.ENTER)

                    sleep(3)

                with st.spinner("Выбираю категорию продуктов ..."):
                    if category:
                        category_links = sel(s['catalog'])[0].find_elements(By.TAG_NAME, "a")
                        for link in category_links:
                            if link.get_attribute("innerHTML").find(category) > -1:
                                link.click()

                with st.spinner("Листаю сайт..."):
                    while sel(s['more_button']):
                        sel(s['more_button'])[0].click()
                        sleep(2)

                with st.spinner("Собираю данные о ценах..."):
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
                                unit = price_and_unit.find_elements(By.TAG_NAME, "span")[0].get_attribute("innerHTML")[1:].strip()
                            rows.append([name, price, unit])
                    driver.quit()
            except Exception as exc:
                print(exc)
                return st.image(driver.get_screenshot_as_png())
        with st.spinner("Обрабатываю данные..."):
            def detect_kg(pr_name):
                multiplied_regex = re.findall("(\d+)[^\d]*[\*xXхХ][^\d]*([\d.,]+) *г", pr_name)
                grams_regex = re.findall("([\d.,]+) *г", pr_name)
                kilograms_regex = re.findall("([\d.,]+) *кг", pr_name)
                try:
                    if multiplied_regex:
                        return (float(multiplied_regex[0][0]) *
                                float(multiplied_regex[0][1].replace(",", "."))) / 1000
                    elif grams_regex:
                        return float(grams_regex[0].replace(",", ".")) / 1000
                    elif kilograms_regex:
                        return float(kilograms_regex[0].replace(",", "."))
                    else:
                        return float("nan")
                except ValueError:
                    return float("nan")

            def detect_l(pr_name):
                ml_regex = re.findall("([\d.,]+) *мл", pr_name)
                l_regex = re.findall("([\d.,]+) *л", pr_name)
                try:
                    if ml_regex:
                        return float(ml_regex[0].replace(",", ".")) / 1000
                    elif l_regex:
                        return float(l_regex[0].replace(",", "."))
                    else:
                        return float("nan")
                except ValueError:
                    return float("nan")



            df = pd.DataFrame(rows, columns=["name", "price", "unit"])

            df["kilograms"] = df["name"].apply(detect_kg)
            df.loc[df["unit"] == "кг", "kilograms"] = 1
            df["price_per_kg"] = np.divide(df["price"], df["kilograms"])

            df["liters"] = df["name"].apply(detect_l)
            df.loc[df["unit"] == "л", "liters"] = 1
            df["price_per_l"] = np.divide(df["price"], df["liters"])

        with st.spinner("Сохраняю данные..."):
            df1 = df
            df1[['ingredient', 'city', 'date']] = [ingredient, city, today]
            df1.to_sql('new_data', db_conn)
            db_conn.execute(f"INSERT INTO {db} SELECT * FROM new_data")
        return df


    city_list = ("Москве, Московской области, Санкт-Петербурге, Архангельске, Астрахани, Барнауле, Белгороде, Брянске, Владикавказе, Владимире, Волгограде, Волжском, Вологде, Воронеже, Екатеринбурге, Иваново, Иркутске, Ижевске, Казани, Калининграде, Калуге, Кемерово, Кирове, Краснодаре, Красноярске, Курске, Липецке, Магнитогорске, Набережных Челнах, Нижнем Новгороде, Новой Адыгее, Новокузнецке, Новосибирске, Новороссийске, Омске, Орле, Оренбурге, Пензе, Перми, Пятигорске, Ростове-на-Дону, Рязани, Самаре, Саратове, Смоленске, Серпухове, Ставрополе, Стерлитамаке, Сургуте, Твери, Тольятти, Томске, Туле, Тюмени, Уфе, Ульяновске, Чебоксарах, Челябинске, Ярославле"
                 .split(", "))

    city_select = st.selectbox("Искать товары в...", options=city_list)
    ingredient_input = st.text_input("Введите ингредиент")
    category_input = st.text_input("Введите категорию")
    start_scrapping = st.button(label="Начать скрэппинг")
    def get_city(city_select):
        if city_select == "Московской области":
            return "Московская область"
        elif city_select == "Новой Адыгее":
            return "Новая Адыгея"
        elif city_select == "Набережных Челнах":
            return "Набережные Челны"
        elif city_select == "Нижнем Новгороде":
            return "Нижний Новгород"
        elif city_select == "Ростове-на-Дону":
            return "Ростов-на-Дону"
        else:
            return city_select[:-1]

    if start_scrapping:
        st.write(scrape_prices(get_city(city_select), ingredient_input, str(category_input)))

    st.markdown("***")
    st.write("Исходный код:")