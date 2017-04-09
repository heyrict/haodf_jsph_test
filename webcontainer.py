from selenium import webdriver
from scrapy import Selector
import sys,os
class WebContainer(object):
    def __init__(self,link,PhantomJSDriver=None,logfile=sys.stdout,timeout=15):
        if PhantomJSDriver: self.dr = PhantomJSDriver
        else: self.dr = webdriver.PhantomJS();self.dr.set_page_load_timeout(timeout)
        try:
            print('Now scraping %s'%link)
            while(1):
                try: self.dr.get(link);break
                except Exception as e:
                    print('Exception raised:',end='')
                    print(e)
                    print('Trying to rescrape...')
            self.contents = Selector(text=self.dr.page_source)
        except Exception as e:
            print('Failed to scrap %s'%link)
            print(e)
            print('Failed to scrap %s'%link,file=logfile)

    ## maybe add css version of find() later
    def find(self,expression,kind='xpath'):
        return self.contents.xpath(expression)

    def xpath(self,expression):
        return self.find(expression,kind='xpath')


