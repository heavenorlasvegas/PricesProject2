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

with st.echo(code_location='below'):


    st.markdown("***")
    st.write("Исходный код:")
