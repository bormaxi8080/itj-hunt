import requests
from bs4 import BeautifulSoup
from django.conf import settings
import logging
from selenium import webdriver


def create_beautiful_soup_object(url):
    header = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'TE': 'Trailers',
    }
    response = requests.get(url, headers=header)
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, features="html.parser")


def create_beautiful_soup_object_using_selenium(url):
    browser = webdriver.PhantomJS(executable_path=settings.SELENIUM_DRIVER_PATH)
    browser.get(url)
    html = browser.page_source
    browser.quit()
    return BeautifulSoup(html, features="html.parser")


def cleanup_beautifulsoup_object(bs_obj, unwrap_a=False):
    '''for tag in bs_obj.findAll('strong'):
        tag.unwrap()
    for tag in bs_obj.findAll('b'):
        tag.unwrap()
    for tag in bs_obj.findAll('i'):
        tag.unwrap()
    for tag in bs_obj.findAll('em'):
        tag.unwrap()'''
    for tag in bs_obj.findAll('u'):
        tag.unwrap()
    for tag in bs_obj.findAll('img'):
        tag.decompose()
    for tag in bs_obj.findAll('hr'):
        tag.unwrap()
    for tag in bs_obj.findAll('span'):
        tag.unwrap()
    if unwrap_a:
        for tag in bs_obj.findAll('a'):
            tag.unwrap()
    for h in bs_obj.findAll('h1'):
        new_tag = bs_obj.new_tag('strong')
        new_tag.string = h.text
        h.replace_with(new_tag)
    for h in bs_obj.findAll('h2'):
        new_tag = bs_obj.new_tag('strong')
        new_tag.string = h.text
        h.replace_with(new_tag)
    for h in bs_obj.findAll('h3'):
        new_tag = bs_obj.new_tag('strong')
        new_tag.string = h.text
        h.replace_with(new_tag)
    return bs_obj


LOG_FATAL = 50
LOG_ERROR = 40
LOG_WARNING = 30
LOG_INFO = 20
LOG_DEBUG = 10
LOG_NOTSET = 0


def add_log(msg, loglevel=LOG_DEBUG):
    if settings.DEBUG:
        logger = logging.getLogger()
        hdlr = logging.FileHandler(settings.LOG_FILE)
        formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"', '%Y-%m-%d %a %H:%M:%S')

        hdlr.setFormatter(formatter)

        logger.addHandler(hdlr)
        if settings.DEBUG:
            logger.setLevel(logging.NOTSET)
        else:
            logger.setLevel(logging.INFO)
        logger.log(loglevel, msg)
        hdlr.close()
