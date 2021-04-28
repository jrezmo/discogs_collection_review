from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
import re


options = Options()
options.headless = True


def run_driver(url):
    print('>>> ', end='')
    driver = webdriver.Firefox(options=options, executable_path='lib/geckodriver')
    driver.get(url)
    delay = 3  # seconds
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, Selector().sale)))
    except TimeoutException:
        print('<')
        sleep(5)
        pass
    return driver


class Selector:
    def __init__(self):
        self.price = '.marketplace_aside > div:nth-child(1) > div:nth-child(1) > ' \
                     'div:nth-child(1) > p:nth-child(1) > span:nth-child(1)'
        self.start = '.price_2Wkos'
        self.want = '.items_3gMeU > ul:nth-child(1) > li:nth-child(2) > a:nth-child(2)'
        self.have = '.items_3gMeU > ul:nth-child(1) > li:nth-child(1) > a:nth-child(2)'
        self.low = '.items_3gMeU > ul:nth-child(2) > li:nth-child(2) > span:nth-child(2)'
        self.med = '.items_3gMeU > ul:nth-child(2) > li:nth-child(3) > span:nth-child(2)'
        self.high = '.items_3gMeU > ul:nth-child(2) > li:nth-child(4) > span:nth-child(2)'
        self.last = '.items_3gMeU > ul:nth-child(2) > li:nth-child(1) > a:nth-child(2) > time:nth-child(1)'
        self.sale = '.forsale_QoVFl > a:nth-child(1)'
        self.avg_rate = '.items_3gMeU > ul:nth-child(1) > li:nth-child(3) > span:nth-child(2)'
        self.rate_count = '.items_3gMeU > ul:nth-child(1) > li:nth-child(4) > a:nth-child(2)'
        self.ships = '.marketplace_aside > div:nth-child(3) > div:nth-child(2) > p:nth-child(5)'
        self.ship_cost = '.marketplace_aside > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > ' \
                         'p:nth-child(1) > span:nth-child(2)'
        self.styles = 'div.lineitem_2U49R:nth-child(6) > div:nth-child(2)'


class Pattern:
    def __init__(self):
        self.price = r'(?:[$£¥€])(\d*.\d\d)'
        self.sale = r'(\d*)'
        self.avg = r'(?:<!-- -->)(\d*.\d*)'
        self.ships = r'(?<=>Item Ships From:</strong>\s)(\w+\s*\w+\s*)'
        self.ship_cost = r'(?:[$£¥€])(\d+.\d+)\s(?:shipping)'


class ReleaseObject:
    def __init__(self, release_id, title):
        self.id = release_id
        self.url = 'https://www.discogs.com/release/' + str(self.id)
        self.select, self.pattern = Selector(), Pattern()
        self.driver = run_driver(self.url)
        self.title = title
        self.want = self.get_data(self.select.want)
        self.have = self.get_data(self.select.have)

        self.start = self.get_price(self.select.start)
        self.low = self.get_price(self.select.low)
        self.med = self.get_price(self.select.med)
        self.high = self.get_price(self.select.high)

        self.for_sale = self.get_data(self.select.sale, self.pattern.sale)
        self.avg_rating = self.get_data(self.select.avg_rate, self.pattern.avg)
        self.rating_count = self.get_data(self.select.rate_count)
        self.last_sold = self.get_data(self.select.last)
        self.driver.quit()

    def get_data(self, select, pattern=None):
        try:
            data = self.driver.find_element_by_css_selector(select).get_attribute('innerHTML')
            if pattern:
                data = self.get_data(select)
                return re.findall(pattern, str(data), re.DOTALL)[0]
            else:
                return data
        except (IndexError, NoSuchElementException):
            print(self.driver.current_url, 'err', select, pattern)
            print(self.driver.title)
            return 0

    def get_price(self, select):
        data = self.get_data(select)
        price, currency = self.currency_check(data)
        price = re.findall(self.pattern.price, price, re.DOTALL)
        price = self.convert_float(price, currency)
        return price

    @staticmethod
    def convert_float(price, currency):
        try:
            price = float(price[0])
            return round(price * currency, 2)
        except ValueError:
            price = float(re.sub(",", "", str(price[0])))
            price *= 10
            return round(price * currency, 2)
        except IndexError:
            return 0

    @staticmethod
    def currency_check(price):
        funt_eur = 1.17
        dollar_eur = 0.84
        yen_eur = 0.0077
        try:
            if '£' in price: return price, funt_eur
            elif '¥' in price: return price, yen_eur
            elif '$' in price: return price, dollar_eur
            else:
                return price, 1
        except TypeError:
            return '€0.00', 1

    def csv_object(self):
        url = self.url
        title = self.title.encode('utf-8')
        columns = (self.id, title, self.start, self.avg_rating, self.rating_count,
                   self.low, self.med, self.high, self.want, self.have,
                   self.last_sold, self.for_sale, url)
        return columns