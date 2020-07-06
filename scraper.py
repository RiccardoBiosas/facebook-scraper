from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
from PIL import Image
from pytesseract import image_to_string
import re
import json
import argparse
import datetime
import shutil
import os



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', help='set the path of your facebook URLs dump')
    parser.add_argument('--hless', '-hl', action="store_true", help='set headless mode')
    parser.add_argument("--cleanUp", '-cl', action="store_true", help="remove all screenshots after running the scraper")
    args = parser.parse_args()
    args_dict = vars(args)
    scraper = Scraper(**args_dict)
    scraper.run_scraper()


class Scraper(object):
    def __init__(self, path, hless, cleanUp):
        self.path = path
        self.hless = hless
        self.cleanUp = cleanUp
        options = Options()
        if self.hless:
            options.add_argument('--headless')
        self.driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', options=options)
        self.urls = self.load_facebook_urls(self.path)
        self.scraped_data = {"timestamp": datetime.datetime.today().strftime('%Y-%m-%d-%m-%s'),
                             "batch": {}}

    def load_facebook_urls(self, json_file):
        facebook_urls = []
        f = open(json_file)
        data = json.load(f)
        for k in data:
            facebook_urls.append(k["url"])
        f.close()
        return facebook_urls


    def screenshot_facebook_page(self, platform_name, index):
        target_url = platform_name
        self.driver.get(target_url)
        self.driver.maximize_window()
        time.sleep(2)
        self.driver.execute_script('window.scrollTo(600, 600)')
        if not os.path.exists('./screenshots'):
            os.mkdir('./screenshots')
        screenshot_path = './screenshots/' + str(index) + '.png'
        self.driver.get_screenshot_as_file(screenshot_path)
        text = image_to_string(Image.open(screenshot_path), lang='eng')
        result = self.scrape_text_regex(text)
        return result

    @staticmethod
    def scrape_text_regex(txt):
        regex_big_number = re.compile('([0-9]+,[0-9]*) people')
        regex_small_number = re.compile('([0-9]+) people')
        result_big_number = regex_big_number.findall(txt)
        if len(result_big_number) != 0:
            return result_big_number
        else:
            return regex_small_number.findall(txt)

    @staticmethod
    def removeScreenshots():
        shutil.rmtree("./screenshots")


    def run_scraper(self):
        if self.path is not None:
            for index, url in enumerate(self.urls):
                result = self.screenshot_facebook_page(url, index)
                self.scraped_data["batch"].update({json.dumps(index): {
                    'url': url,
                    'likes': result[0] if len(result) > 0 else '',
                    'followers': result[1] if len(result) > 1 else ''
                }})
            if self.cleanUp:
                self.removeScreenshots()
            with open("scrape_output.json", "w") as write_file:
                json.dump(self.scraped_data, write_file)
            self.driver.quit()
        else:
            print('set a path!')


if __name__ == '__main__':
    main()
