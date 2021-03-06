import os
from dotenv import load_dotenv
import logging
from enum import IntEnum
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


class Operation(IntEnum):
    BUY = 0
    SELL = 1
    SEND_CLOUT = 2
    FOLLOW = 3
    DM = 4
    DM_TO_INVESTORS = 5
    FOLLOW_AND_DM = 7
    DO_NOTHING = 99


GAS = 0.0000002


class Worker:
    def __init__(
        self,
        name: str,
        private_key: str,
        use_proxy: bool = False,
        node: str = "https://bitclout.com",
    ) -> None:
        self.is_busy = False
        self.name = name
        self.username = ""
        self.headless = os.getenv("HEADLESS")
        self.private_key = private_key
        self.public_key = ""
        self.wallet: dict = {}
        self.balance_bitclout = 0
        self.node = node
        self.usd_per_coin = 0
        capa = DesiredCapabilities.CHROME
        chrome_options = Options()
        if use_proxy:
            proxy_server = os.getenv("PROXY_URL")
            if proxy_server != "" and proxy_server != None:
                chrome_options.add_argument(f"--proxy-server={proxy_server}")
        if not self.headless:
            chrome_options.add_argument("--headless=false")
            chrome_options.add_argument("--disable-gpu=false")
        else:
            chrome_options.add_argument("--headless ")
            chrome_options.add_argument("--disable-gpu ")
        chrome_options.add_argument("--window-size=1280, 800")
        capa["pageLoadStrategy"] = "eager"
        self.driver = webdriver.Chrome(
            desired_capabilities=capa, chrome_options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 60)

    def launch(self):
        logger.info(f"launching {self.private_key}")
        self.is_busy = True
        try:
            self.driver.get(self.node)
            login_in = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//a[@class='landing__log-in d-none d-sm-block']",
                    )
                )
            )
            login_in.click()
            self.switch_to_tab(1)
            login_in_with_seed = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//button[@class='btn btn-default log-in-seed']",
                    )
                )
            )
            login_in_with_seed.click()
            input_box = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//textarea[@placeholder='Enter your seed phrase']",
                    )
                )
            )
            input_box.click()
            for ch in self.private_key:
                input_box.send_keys(ch)
            self.driver.find_element_by_xpath(
                "//button[contains(text(),'Load Account')]"
            ).click()

            select_account = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(text(),'BC1YL')]")
                )
            )
            select_account.click()
            self.switch_to_tab(0)
            # read wallet
            wallet_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Wallet')]"))
            )
            # read clout price self.usd_per_coin
            usd_per_coin_str = self.driver.find_element_by_xpath(
                "//div[@class='d-flex justify-content-between']/div[2]/span[1]"
            ).text
            price_per_coin = float(usd_per_coin_str[2:])
            logger.info(f"current $CLOUT price is {price_per_coin}")
            self.usd_per_coin = price_per_coin

            wallet_button.click()
            public_key = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//div[@class = 'col-9 d-flex align-items-center holdings__pub-key mb-0']",
                    )
                )
            )
            self.public_key = public_key.text
            # self.username = self.driver.find_element_by_xpath(
            #     "//div[@class='change-account-selector__ellipsis-restriction cursor-pointer ng-star-inserted']").text
            self.balance_bitclout = float(
                self.driver.find_element_by_xpath(
                    "//div[@class='col-9']/div[1]"
                ).text.split(" ")[0]
            )
            logger.info(f"balance_bitclout: {self.balance_bitclout}")
            coin_name_elements = self.driver.find_elements_by_xpath(
                "//div[@class='text-truncate holdings__name']/span[not(contains(@class,'ml-1'))]"
            )
            coin_count_elements = self.driver.find_elements_by_xpath(
                "//div[@class='text-grey8A fs-12px text-right']"
            )
            self.wallet = dict(
                zip(
                    [
                        coin_name_element.text
                        for coin_name_element in coin_name_elements
                    ],
                    [
                        float(coin_count_element.text)
                        for coin_count_element in coin_count_elements
                    ],
                )
            )
            logger.info(f"get wallet success: {self.wallet}")
            logger.info(f"login {self.public_key} complete, wait signal")
        except Exception as e:
            logger.error(f"login in error: {e}")
            self.driver.save_screenshot("error_launch.png")
            self.driver.close()
        finally:
            self.is_busy = False

    def dispatcher(self, signal_index, args):
        """
        BUY = 0
        SELL = 1
        SEND_CLOUT = 2
        FOLLOW = 3
        DM = 4
        DM_TO_INVESTORS = 5
        FOLLOW_AND_DM = 7
        """
        signal = int(signal_index)
        if signal == Operation.BUY:
            self.buy(*args)
        elif signal == Operation.SELL:
            self.sell(*args)
        elif signal == Operation.SEND_CLOUT:
            self.send_clout(*args)
        elif signal == Operation.FOLLOW:
            self.follow(*args)
        elif signal == Operation.DM:
            usernames, message = args[0], args[1:]
            for username in usernames.split("/"):
                self.dm(username, " ".join(message))
                wait_s = 10
                time.sleep(wait_s)
                logger.info(f"wait {wait_s} seconds forbid CF ban")
        elif signal == Operation.DM_TO_INVESTORS:
            creator, message = args[0], args[1:]
            invests_info = self.get_investors(creator)
            try:
                del invests_info[self.username]
            except:
                logger.info("creator is not buy his own coin")
            for investor in invests_info.keys():
                self.dm(investor, " ".join(message))
        elif signal == Operation.FOLLOW_AND_DM:
            usernames, message = args[0], args[1:]
            for username in usernames.split("/"):
                self.follow(username)
                self.dm(username, " ".join(message))
                wait_s = 10
                time.sleep(wait_s)
                logger.info(f"wait {wait_s} seconds forbid CF ban")
        else:
            logger.warning(f"??????????????????:{signal}")

    def buy(self, username: str, clout_str: str):
        clout = float(clout_str)
        if clout > self.balance_bitclout + GAS:
            logger.error(f"buy {username} in {clout} exceed max balance")
            return
        logger.info(f"want to buy {username} in {clout} $CLOUT")
        try:
            self.is_busy = True
            self.enter_user_page(username)
            buy_button = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//a[@class='btn btn-primary font-weight-bold ml-15px fs-14px']",
                    )
                )
            )
            buy_button.click()

            unit_input = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='0']"))
            )
            unit_input.click()

            usd_amount = round(clout * self.usd_per_coin, 2)
            unit_input.send_keys(str(usd_amount))

            review_button = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[@class='pb-3 pt-3']/a[not(contains(@class,'disable'))]",
                    )
                )  # Review
            )
            review_button.click()
            confirm_buy_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Confirm Buy')]")
                )
            )
            recieve_number_str = self.driver.find_element_by_xpath(
                "//trade-creator-table/div[2]/div"
            ).text
            recieve_number = float(recieve_number_str.split(" ")[0])
            bitclout_str = self.driver.find_element_by_xpath(
                "//trade-creator-table/div[3]/div"
            ).text
            price_per_coin = float(bitclout_str.split(" ")[0][1:])
            logger.info(
                f"recieve_number: {recieve_number}; price_per_coin: {price_per_coin}"
            )
            confirm_buy_button.click()
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[@class='ml-10px text-primary']")
                )
            )  # ????????????????????????
            logger.info(f"????????????, ?????????{clout:.9f} bitclout")
            self.balance_bitclout -= clout
        except Exception as e:
            logger.error(f"buying error: {e}")
        finally:
            self.driver.get(self.node + "/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")

    def sell(self, username: str, coin: str):
        logger.info(f"want to sell {coin} {username} coin")

    def send_clout(self, to: str, amount_str: str = "MAX"):
        if amount_str != "MAX":
            amount = float(amount_str)
            logger.info(f"{self.public_key} want to send {amount} $CLOUT to {to}")
            if amount <= 0 or amount > (self.balance_bitclout - GAS):
                logger.warn(
                    "transfer amount is must greater than 0 or balance not enough"
                )
                return
        try:
            # click Send BitClout
            send_clout_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Send $CLOUT')]")
                )
            )
            send_clout_button.click()

            search_input = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(text(),'Public key or username to pay: ')]//input[@placeholder='Search']",
                    )
                )
            )
            search_input.click()
            search_input.send_keys(to)
            user_button = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        f"//div[contains(@class, 'search-bar__results-dropdown')]/div[1]/div/div[2]/span[1][contains(text(),'{to}')]",
                    )
                )
            )

            user_button.click()

            if amount_str != "MAX":
                amount_input = self.driver.find_element_by_xpath(
                    "//input[@placeholder='0']"
                )
                amount_input.click()
                for a in str(amount):
                    amount_input.send_keys(a)
            else:
                max_button = self.driver.find_element_by_xpath(
                    "//button[contains(text(),'Max')]"
                )
                max_button.click()
                time.sleep(1)

            send_button = self.driver.find_element_by_xpath(
                "//button[contains(text(),'Send Bitclout')]"
            )
            send_button.click()

            ok_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'OK')]")
                )
            )
            ok_button.click()
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//h2[contains(text(),'Success!')]")
                )
            )
            if amount_str != "MAX":
                self.balance_bitclout -= amount + GAS
                logger.info(f"{self.public_key} send {amount} $CLOUT to {to} success")
            else:
                self.balance_bitclout = 0
                logger.info(f"{self.public_key} send ALL $CLOUT to {to} success")
        except Exception as e:
            logger.error(f"send_clout error: {e}")
        finally:
            self.driver.get(self.node + "/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")

    def get_investors(self, username: str) -> dict[str, float]:
        logger.info(f"want to get investors info of {username}")
        investors_info = {}
        try:
            self.is_busy = True
            self.enter_user_page(username)
            create_coin_button = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(text(),'Creator Coin')]")
                )
            )
            create_coin_button.click()
            self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//creator-profile-hodlers[1]/div[1]/div[2]/div[1]/div[1]/div[1]/a[1]",
                    )
                )
            )
            coin_name_elements = self.driver.find_elements_by_xpath(
                "//a[@class='d-flex align-items-center link--unstyled']"
            )
            coin_count_and_value_elements = self.driver.find_elements_by_xpath(
                "//div[@class='col-3 d-flex align-items-center mb-0']"
            )
            coin_count_elements = coin_count_and_value_elements[::2]
            investors_info = dict(
                zip(
                    [
                        coin_name_element.text[:15]
                        for coin_name_element in coin_name_elements
                    ],
                    [
                        float(coin_count_element.text)
                        for coin_count_element in coin_count_elements
                    ],
                )
            )
            logger.info(investors_info)
        except Exception as e:
            logger.error(f"get {username}'s investors error: {e}")
        finally:
            self.driver.get(self.node + "/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")
            return investors_info

    def dm(self, username: str, dm_content: str = ""):
        logger.info(f"want to dm {dm_content} to {username}")
        try:
            if dm_content == "":
                logger.warning("No content to send")
                raise DMEmptyException
            self.is_busy = True
            self.driver.get(self.node + "/inbox")
            search_input = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//input[@placeholder='Search']")
                )
            )
            search_input.click()
            search_input.send_keys(username)
            user_button = self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        f"//div[contains(@class, 'search-bar__results-dropdown')]/div/div/div[2]/span[1][contains(text(),'{username}')]",
                    )
                )
            )
            user_button.click()
            input_form = self.driver.find_element_by_xpath(
                "//textarea[contains(@class,'ng-valid')]"
            )
            input_form.click()
            # input text
            JS_ADD_TEXT_TO_INPUT = """
                var elm = arguments[0], txt = arguments[1];
                elm.value += txt;
                elm.dispatchEvent(new Event('change'));
            """  # only js can use emoji
            self.driver.execute_script(JS_ADD_TEXT_TO_INPUT, input_form, dm_content)
            input_form.send_keys(" ")  # input a space can send message
            send_button = self.driver.find_element_by_xpath(
                "//messages-thread-view[@class='messages-thread__desktop-column']//button[contains(text(),'Send')]"
            )
            send_button.click()  # comment for test
            time.sleep(3)  # wait loading done
            logger.info(f"dm {dm_content} to {username} sent")
        except Exception as e:
            self.driver.save_screenshot("error_dm.png")
            logger.error(f"error when dm: {e}")
        finally:
            self.driver.get(self.node + "/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")

    def follow(self, username: str):
        logger.info(f"want to follow {username}")
        try:
            self.is_busy = True
            self.enter_user_page(username)
            self.wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//a[@class = 'btn btn-primary font-weight-bold ml-15px fs-14px']",
                    )
                )
            )
            logger.info("checking UnFollow")
            try:
                self.driver.find_element_by_xpath("//a[contains(text(),'Unfollow')]")
                logger.info(f"{username} is already followed")
            except NoSuchElementException:
                follow_button = self.wait.until(
                    EC.visibility_of_element_located(
                        (By.XPATH, "//a[contains(text(),'Follow')]")
                    )
                )
                follow_button.click()
                time.sleep(2)
                logger.info(f"follow to {username} success")
        except Exception as e:
            self.driver.save_screenshot("error_follow.png")
            logger.error(f"error when follow: {e}")
        finally:
            self.driver.get(self.node + "/browse")
            self.is_busy = False
            logger.info("go back to homepage, wait for new signal")
            return

    def enter_user_page(self, username: str):
        if (
            not self.node + "/browse" in self.driver.current_url
            and not self.node + "/wallet" in self.driver.current_url
        ):
            logger.warning("current page is not home/wallet page")
            return
        search_input = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@placeholder='Search']")
            )
        )
        search_input.click()
        search_input.send_keys(username)
        user_page_enter_button = self.wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    f"//div[contains(@class, 'search-bar__results-dropdown')]//span[1][contains(text(),'{username}')]",
                )
            )
        )
        user_page_enter_button.click()
        time.sleep(1)

    def open_new_tab(self):
        self.driver.execute_script("window.open('');")
        tab = self.driver.window_handles[-1]
        self.driver.switch_to.window(tab)

    def switch_to_tab(self, index: int):
        tab = self.driver.window_handles[index]
        self.driver.switch_to.window(tab)
