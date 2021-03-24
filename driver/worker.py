import undetected_chromedriver as uc
uc.install()

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
import re
from enum import Enum
import logging
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

class Signal(Enum):
    BUY = 0,
    SELL = 1

class Worker:
    def __init__(self, name:str, private_key:str) -> None:
        self.is_busy = False
        self.name = name
        self.headless = False
        self.private_key = private_key
        self.wallet:dict = { } 
        self.balance = 0
        capa = DesiredCapabilities.CHROME
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument(
                '--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50"')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument("--window-size=1280, 800")  
        capa["pageLoadStrategy"] = "eager"
        self.driver = webdriver.Chrome(
            desired_capabilities=capa, chrome_options=chrome_options)
        self.wait = WebDriverWait(self.driver, 300)

    def launch(self):
        logger.info(f"headless mode: {self.headless}")
        self.is_busy = True
        try:
            self.driver.get("https://bitclout.com/?password=825bbae8589b65720731d867f436471e18683c6a3192a20140105ee1733bb7cc")

            login_in = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[@class='slide-up-2']//a[@class='landing__log-in d-none d-md-block'][contains(text(),'Log in')]"))
            )
            login_in.click()

            input_box = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//textarea[@placeholder='Enter your secret phrase here.']"))
            )
            input_box.click()
            for ch in self.private_key:
                input_box.send_keys(ch)
            self.driver.find_element_by_xpath(
                "//button[contains(text(),'Load Account')]").click()
            
            # read wallet
            wallet_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Wallet')]"))
            )
            wallet_button.click()
            time.sleep(2)
            self.balance = float(self.driver.find_element_by_xpath("//div[@class='col-9']/div[1]").text)
            logger.info(f"get balance success: {self.balance}")
            coin_name_elements = self.driver.find_elements_by_xpath("//div[@class='text-truncate holdings__name']/span")
            coin_count_elements = self.driver.find_elements_by_xpath("//div[@class='text-grey8A fs-12px text-right']")
            self.wallet = dict(zip([coin_name_element.text for coin_name_element in coin_name_elements], [float(coin_count_element.text) for coin_count_element in coin_count_elements]))
            logger.info(f"get wallet success: {self.wallet}")
            logger.info("login complete")
        except Exception as e:
            logger.error(f"login in error: {e}")
            self.driver.save_screenshot('error_screenshot.png')
            self.driver.close()
        finally:
            self.is_busy = False       

    def dispatcher(self, signal_index, args):
        '''
            BUY = 0,
            SELL = 1
        '''
        signal = int(signal_index)
        if signal == 0:
            self.buy(*args)
        elif signal == 1:
            self.sell(*args)
        else:
            logger.warning(f'无法解析信号:{signal}')

    def buy(self, username:str, bitclout:str):
        logging.info(f"want to buy {username} in {bitclout} bitclout")

    def sell(self, username:str, coin:str):
        logging.info(f"want to sell {coin} {username} coin")