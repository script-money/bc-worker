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
        self.balance_bitclout = 0
        self.balance_usd = 0
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
            self.balance_bitclout = float(self.driver.find_element_by_xpath("//div[@class='col-9']/div[1]").text)
            balance_usd = self.driver.find_element_by_xpath("//div[@class='col-9']/div[2]").text
            self.balance_usd = float(balance_usd[3:-4])
            logger.info(f"balance_bitclout: {self.balance_bitclout}, balance_usd: {self.balance_usd}")
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

    def buy(self, username:str, usd_str:str):
        usd = float(usd_str)
        if usd > self.balance_usd:
            logging.error("超出最大可购买本金")
        logging.info(f"want to buy {username} in {usd} usd")
        buy_page_url = f"https://bitclout.com/u/{username}/buy"
        try:
            self.is_busy = True
            self.driver.execute_script("window.open('');")
            tab = self.driver.window_handles[-1]
            self.driver.switch_to.window(tab)
            self.driver.get(buy_page_url)      
            unit_input = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@name='amount']"))
            )
            unit_input.click()
            unit_input.send_keys(usd_str)
            review_button = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='pb-3 pt-3']/a[not(contains(@class,'disable'))]")) # Review
            )
            review_button.click()
            confirm_buy_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Confirm Buy')]"))
            )
            recieve_number_str = self.driver.find_element_by_xpath("//trade-creator-table/div[2]/div").text
            recieve_number = float(recieve_number_str.split(' ')[0])
            bitclout_str = self.driver.find_element_by_xpath("//trade-creator-table/div[3]/div").text
            price_per_coin = float(bitclout_str.split(' ')[0][1:])
            logger.info(f"recieve_number: {recieve_number}; price_per_coin: {price_per_coin}")

            confirm_buy_button.click()                 
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[@class='ml-10px text-primary']"))
            )# 购买成功的蓝色字
            spend_bitclout = recieve_number * price_per_coin
            logger.info(f"购买成功, 花费了{spend_bitclout:.9f} bitclout, 等同于 ${usd:.7f} ")
            self.balance_bitclout -= spend_bitclout
            self.balance_usd -= usd
        except Exception as e:
            logger.error(f"buying error: {e}")
        finally:
            self.driver.close()
            self.switch_to_tab(0)
            self.is_busy = False
            return

    def sell(self, username:str, coin:str):
        logging.info(f"want to sell {coin} {username} coin")

    def open_new_tab(self):
        self.driver.execute_script("window.open('');")
        tab = self.driver.window_handles[-1]
        self.driver.switch_to.window(tab)

    def switch_to_tab(self, index):
        tab = self.driver.window_handles[index]
        self.driver.switch_to.window(tab)