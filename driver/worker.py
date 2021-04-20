import os
from dotenv import load_dotenv
import logging
from enum import Enum
import re
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from exceptions import DMEmptyException
import time
import undetected_chromedriver as uc
uc.install()


logger = logging.getLogger(__name__)


class Signal(Enum):
    BUY = 0,
    SELL = 1


class Worker:
    def __init__(self, name: str, private_key: str) -> None:
        self.is_busy = False
        self.name = name
        self.headless = False
        self.private_key = private_key
        self.wallet: dict = {}
        self.balance_bitclout = 0
        self.balance_usd = 0
        capa = DesiredCapabilities.CHROME
        chrome_options = Options()
        proxy_server = os.getenv('PROXY_URL')
        if proxy_server != "" and proxy_server != None:
            chrome_options.add_argument(f'--proxy-server={proxy_server}')
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument("--window-size=1280, 800")
        capa["pageLoadStrategy"] = "eager"
        self.driver = webdriver.Chrome(
            desired_capabilities=capa, chrome_options=chrome_options)
        self.wait = WebDriverWait(self.driver, 60)

    def launch(self):
        logger.info(f"headless mode: {self.headless}")
        self.is_busy = True
        try:
            self.driver.get(
                "https://bitclout.com/?password=825bbae8589b65720731d867f436471e18683c6a3192a20140105ee1733bb7cc")
            login_in = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[@class='slide-up-2']//a[@class='landing__log-in d-none d-md-block'][contains(text(),'Log in')]"))
            )
            login_in.click()
            time.sleep(2)
            self.switch_to_tab(1)
            input_box = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//textarea[@placeholder='Enter your secret phrase here.']"))
            )
            input_box.click()
            for ch in self.private_key:
                input_box.send_keys(ch)
            self.driver.find_element_by_xpath(
                "//button[contains(text(),'Load Account')]").click()

            self.switch_to_tab(0)
            # read wallet
            wallet_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Wallet')]"))
            )
            wallet_button.click()
            time.sleep(2)
            self.balance_bitclout = float(self.driver.find_element_by_xpath(
                "//div[@class='col-9']/div[1]").text)
            balance_usd = self.driver.find_element_by_xpath(
                "//div[@class='col-9']/div[2]").text
            self.balance_usd = float(balance_usd[3:-4])
            logger.info(
                f"balance_bitclout: {self.balance_bitclout}, balance_usd: {self.balance_usd}")
            coin_name_elements = self.driver.find_elements_by_xpath(
                "//div[@class='text-truncate holdings__name']/span")
            coin_count_elements = self.driver.find_elements_by_xpath(
                "//div[@class='text-grey8A fs-12px text-right']")
            self.wallet = dict(zip([coin_name_element.text for coin_name_element in coin_name_elements], [
                               float(coin_count_element.text) for coin_count_element in coin_count_elements]))
            logger.info(f"get wallet success: {self.wallet}")
            logger.info("login complete, wait signal")
        except Exception as e:
            logger.error(f"login in error: {e}")
            self.driver.save_screenshot('error_launch.png')
            self.driver.close()
        finally:
            self.is_busy = False

    def dispatcher(self, signal_index, args):
        '''
            BUY = 0
            SELL = 1
            FOLLOW = 3
            DM = 4
            FOLLOW+DM = 7
        '''
        signal = int(signal_index)
        if signal == 0:
            self.buy(*args)
        elif signal == 1:
            self.sell(*args)
        elif signal == 3:
            self.follow(*args)
        elif signal == 4:
            usernames, message = args[0], args[1:]
            for username in usernames.split('/'):
                self.dm(username, ' '.join(message))
        elif signal == 7:
            usernames, message = args[0], args[1:]
            for username in usernames.split('/'):
                self.follow(username)
                self.dm(username, ' '.join(message))
        else:
            logger.warning(f'无法解析信号:{signal}')

    def buy(self, username: str, usd_str: str):
        usd = float(usd_str)
        if usd > self.balance_usd:
            logging.error("超出最大可购买本金")
        logging.info(f"want to buy {username} in {usd} usd")
        buy_page_url = f"https://bitclout.com/u/{username}/buy"
        try:
            self.is_busy = True
            self.driver.get(buy_page_url)
            unit_input = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@name='amount']"))
            )
            unit_input.click()
            unit_input.send_keys(usd_str)
            review_button = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='pb-3 pt-3']/a[not(contains(@class,'disable'))]"))  # Review
            )
            review_button.click()
            confirm_buy_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Confirm Buy')]"))
            )
            recieve_number_str = self.driver.find_element_by_xpath(
                "//trade-creator-table/div[2]/div").text
            recieve_number = float(recieve_number_str.split(' ')[0])
            bitclout_str = self.driver.find_element_by_xpath(
                "//trade-creator-table/div[3]/div").text
            price_per_coin = float(bitclout_str.split(' ')[0][1:])
            logger.info(
                f"recieve_number: {recieve_number}; price_per_coin: {price_per_coin}")

            confirm_buy_button.click()
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[@class='ml-10px text-primary']"))
            )  # 购买成功的蓝色字
            spend_bitclout = recieve_number * price_per_coin
            logger.info(
                f"购买成功, 花费了{spend_bitclout:.9f} bitclout, 等同于 ${usd:.7f} ")
            self.balance_bitclout -= spend_bitclout
            self.balance_usd -= usd
        except Exception as e:
            logger.error(f"buying error: {e}")
        finally:
            self.driver.get("https://bitclout.com/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")

    def sell(self, username: str, coin: str):
        logging.info(f"want to sell {coin} {username} coin")

    def dm(self, username: str, dm_content:str=''):
        logging.info(f"want to dm {dm_content} to {username}")
        try:
            if dm_content == "":
                logger.warning("No content to send")
                raise DMEmptyException
            self.is_busy = True
            self.driver.get("https://bitclout.com/inbox")
            search_input = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//input[@placeholder='Search']"))
            )
            search_input.click()
            search_input.send_keys(username)
            user_button = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//div[contains(@class, 'search-bar__results-dropdown')]/div/div/div[2]/span[1][text()='{username}']"))
            )
            user_button.click()
            input_form = self.driver.find_element_by_xpath(
                "//textarea[contains(@class,'ng-valid')]")
            input_form.click()
            # input text
            JS_ADD_TEXT_TO_INPUT = """
                var elm = arguments[0], txt = arguments[1];
                elm.value += txt;
                elm.dispatchEvent(new Event('change'));
            """  # only js can use emoji
            self.driver.execute_script(
                JS_ADD_TEXT_TO_INPUT, input_form, dm_content)
            input_form.send_keys(" ")  # input a space can send message
            send_button = self.driver.find_element_by_xpath(
                "//messages-thread-view[@class='messages-thread__desktop-column']//button[contains(text(),'Send')]")
            send_button.click()
            time.sleep(3) # wait loading done
            logger.info(f"dm {dm_content} to {username} sent")
        except Exception as e:
            self.driver.save_screenshot('error_dm.png')
            logger.error(f'error when dm: {e}')
        finally:
            self.driver.get("https://bitclout.com/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")

    def follow(self, username: str):
        logging.info(f"want to follow {username}")
        try:
            self.is_busy = True
            self.driver.get(f"https://bitclout.com/u/{username}")
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//a[@class = 'btn btn-primary font-weight-bold ml-15px fs-14px']"))
            )
            logger.info("checking UnFollow")
            try:
                self.driver.find_element_by_xpath(
                    "//a[contains(text(),'Unfollow')]")
                logger.info(f'{username} is already followed')
            except NoSuchElementException:
                follow_button = self.wait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "//a[contains(text(),'Follow')]"))
                )
                follow_button.click()
                time.sleep(2)
                logger.info(f"follow to {username} success")
        except Exception as e:
            self.driver.save_screenshot('error_follow.png')
            logger.error(f'error when follow: {e}')
        finally:
            self.driver.get("https://bitclout.com/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")
            return

    def open_new_tab(self):
        self.driver.execute_script("window.open('');")
        tab = self.driver.window_handles[-1]
        self.driver.switch_to.window(tab)

    def switch_to_tab(self, index:int):
        tab = self.driver.window_handles[index]
        self.driver.switch_to.window(tab)
