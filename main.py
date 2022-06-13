import numpy as np
import selenium
import shillelagh.exceptions
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
from shillelagh.backends.apsw.db import connect
import pymorphy2
morph = pymorphy2.MorphAnalyzer()



db = st.secrets["private_gsheets_url"]
db_conn = connect(":memory:", adapter_kwargs={"gsheetsapi": {
                "service_account_info": st.secrets["gcp_service_account"]
            }})
db_index = st.secrets["private_gsheets_url1"]
today = date.today().strftime("%d.%m.%Y")
with st.echo(code_location='below'):
    def scrape_prices(city, ingredient, category="", rescrape=False, return_df=True):

        # ЧАСТЬ 1. Проверяем, не собраны ли уже данные
        if not rescrape:
            with st.spinner(ingredient + ". Ищу данные в таблице..."):

                get_data = f'SELECT name, price, price_per_kg, price_per_l FROM "{db}" WHERE ingredient = "{ingredient}" AND city = "{city}"'
                existing_data = pd.read_sql(get_data, db_conn)
                if not existing_data.empty:
                    if return_df:
                        return existing_data
                    else:
                        return ''


            # ЧАСТЬ 2. Если нет, то собираем их с сайта Metro

            with st.spinner(ingredient + ". Запускаю виртуальный браузер..."):

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
                driver.set_page_load_timeout(3)
            try:
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

                with st.spinner(ingredient + ". Выбираю город..."):
                    sel(s['delivery'])[0].click()


                    sel(".obtainments-list__content")[1].click()
                    sel("div.select-item__input")[0].click()
                    sleep(0.1)
                    sel("input.multiselect__input")[0].send_keys(city)
                    sel("input.multiselect__input")[0].send_keys(Keys.ENTER)
                    sleep(0.1)
                    sel("div.pickup__apply-btn-desk button")[0].click()
                    sleep(0.1)

                with st.spinner(ingredient + ". Ищу продукты..."):

                    sel(s['search'])[s['index']].send_keys(ingredient)
                    sleep(0.1)
                    sel(s['search'])[s['index']].send_keys(Keys.ENTER)

                    sleep(3)

                with st.spinner(ingredient + ". Выбираю категорию продуктов ..."):
                    if category:
                        category_links = sel(s['catalog'])[0].find_elements(By.TAG_NAME, "a")
                        for link in category_links:
                            if link.find_elements(By.TAG_NAME, "span")[0].get_attribute("innerHTML") == category:
                                link.click()
                    sleep(2)

                #with st.spinner("Листаю сайт..."):
                #    if len(sel(s['more_button'])):
                #        sel(s['more_button'])[0].click()
                #        sleep(2)

                with st.spinner(ingredient + ". Собираю данные о ценах..."):
                    products = driver.find_elements(By.CSS_SELECTOR, s['product'])[:26]
                    rows = []
                    for product in products:
                        name = product.find_elements(By.CSS_SELECTOR, s['product_name'])
                        if not len(name):
                            continue
                        else:
                            name = name[0].text
                            if name:
                                if new_version:
                                    price = float(product.find_elements(By.CSS_SELECTOR,
                                                                        "span.base-product-prices__actual-sum")[0]
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
                                        By.CSS_SELECTOR,
                                        "div.catalog-item_price-lvl_current, div.catalog-item_price-current")[0]
                                    if price_and_unit.get_attribute("innerHTML").find("Нет") > -1:
                                        continue
                                    price = detect_price(price_and_unit)
                                    unit = (price_and_unit.find_elements(By.TAG_NAME, "span")[0]
                                                          .get_attribute("innerHTML")[1:].strip())
                                rows.append([name, price, unit])
                    driver.quit()

            except Exception as exc:
                print(str(exc))
                return st.image(driver.get_screenshot_as_png())

        with st.spinner(ingredient + ". Обрабатываю данные..."):
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

        # ЧАСТЬ 3. Сохраняем данные в таблицу для дальнейшего использования

        with st.spinner(ingredient + ". Сохраняю данные для других пользователей..."):
            df1 = df
            df1[['ingredient', 'city', 'date']] = [ingredient, city, today]
            try:
                df1.to_sql("new_data", db_conn, method='multi', index=False, if_exists="replace")
                db_conn.execute(f'INSERT INTO "{db}" SELECT * FROM new_data')
            except shillelagh.exceptions.ProgrammingError:
                pass

        if return_df:
            return df[['name', 'price', 'price_per_kg', 'price_per_l']]
        else:
            return ''


    recipe_list = """Картофель — 350 г
    Говядина лопатка — 500 г
    Капуста — 200 г
    Свекла — 130 г
    Лук — 80 г
    Морковь — 80 г
    Чеснок — 6 г
    Хлеб — 200 г
    Сметана — 100 г """.split("\n")
    recipe = pd.DataFrame(columns=["Масса, г."])
    for ingr in recipe_list:
        ingr = ingr.strip().split(" — ")
        ingr_index = ingr[0]
        ingr_grams = int(ingr[1][:-2])
        recipe.loc[ingr_index] = ingr_grams
    recipe = recipe.transpose()
    city_list = ("Москве, Московская область, Санкт-Петербурге, Архангельске, Астрахани, Барнауле, Белгороде, "
                 "Брянске, Владикавказе, Владимире, Волгограде, Волжском, Вологде, Воронеже, Екатеринбурге, Иваново, "
                 "Иркутске, Ижевске, Казани, Калининграде, Калуге, Кемерово, Кирове, Краснодаре, Красноярске, Курске, "
                 "Липецке, Магнитогорске, Набережные Челны, Нижний Новгород, Новая Адыгея, Новокузнецке, "
                 "Новосибирске, Новороссийске, Омске, Орле, Оренбурге, Пензе, Перми, Пятигорске, Ростове-на-Дону, "
                 "Рязани, Самаре, Саратове, Смоленске, Серпухове, Ставрополе, Стерлитамаке, Сургуте, Твери, Тольятти, "
                 "Томске, Туле, Тюмени, Уфе, Ульяновске, Чебоксарах, Челябинске, Ярославле "
                 .split(", "))

    def normal_form(word):
        if word.find(" ") == -1:
            return morph.parse(word)[0].normal_form.capitalize()
        else:
            return word

    city_list = list(map(normal_form, city_list))
    cat_for_ingr = {"молоко": "Молоко", "хлеб": "Хлеб, лаваш", "картофель": "Овощи", "капуста": "Овощи", "лук":
        "Овощи", "морковь": "Овощи", "свекла": "Овощи", "чеснок": "Овощи", "говядина лопатка": "",
                    "сметана": "Сметана"}

    def calculate_index(city, quantile=0.2):
        prices = pd.DataFrame()
        progress = 0.0
        my_bar = st.progress(progress)
        for product in recipe:
            prices[product] = scrape_prices(city, product, cat_for_ingr[product.lower()])["price_per_kg"]
            progress += 1/9
            progress = min(1, progress)
            my_bar.progress(progress)
        prices_quant = np.nanquantile(prices, quantile, axis=0)
        grams = recipe.transpose()["Масса, г."] / 1000
        costs = prices_quant * grams
        return pd.DataFrame({"quant": quantile,
                             "prices": prices_quant,
                             "grams": grams,
                             "costs": costs,
                             "index": sum(costs)})




    # Фронтенд

    st.title("Индекс борща")

    st.markdown("""**Индекс борща** — это интуитивно понятная метрика потребительских цен и реальных доходов населения,
    предложенная [Владимирстатом](https://vladimirstat.gks.ru/) и популяризированная изданием 
    [Ведомости](https://vedomosti.ru). Индекс рассчитывается как количество блюд на четверых,
    которые можно приготовить, потратив при этом весь средний располагаемый доход.""")
    
    st.subheader("Рецепт борща")

    st.dataframe(recipe)


    st.subheader("Посчитать индекс борща")

    with st.container():

        city_select1 = st.selectbox("Город", options=city_list, key="city1")
        calculate_button = st.button(label="Посчитать индекс!")
        c = st.empty()
        if calculate_button:
            borsch_index = calculate_index(city_select1)
            ind_val = borsch_index["index"][0]
            command = f'INSERT INTO "{db_index}" VALUES ("{city_select1}", "{today}", {ind_val})'
            db_conn.execute(command)
            c.write(ind_val)



    st.subheader("Поискать цены на отдельные товары")

    city_select2 = st.selectbox("Город", options=city_list, key="city2")
    ingredient_input = st.text_input("Введите товар")
    if ingredient_input in cat_for_ingr:
        st.write("Категория: " + cat_for_ingr[ingredient_input])
        category_input = cat_for_ingr[ingredient_input]
    else:
        category_input = st.text_input("Определите категорию (как на сайте Metro)")
    start_scraping = st.button(label="Вывести список цен")

    if start_scraping:
        st.write(scrape_prices(city_select2, ingredient_input, str(category_input)))



    st.markdown("***")
    st.write("Исходный код:")