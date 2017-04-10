from selenium import webdriver
from scrapy import Selector
import sys,os,time,random

browsernames = ['chrome','firefox','safari','ie']
platforms = ['linux-unknown-64bit','linux-unknown-32bit','windows-xp-32bit','windows-7-64bit','windows-10-64bit','windows-10-32bit']
class WebContainer(object):
    def __init__(self,link,logfile=sys.stdout,timeout=20,tries=10):
        self.isempty = False
        self.dc = {'webStorageEnabled': False, 'databaseEnabled': False, 'browserName': 'phantomjs', 'platform': 'linux-unknown-64bit', 'version': '2.1.1', 'applicationCacheEnabled': False, 'locationContextEnabled': False, 'nativeEvents': True, 'takesScreenshot': True, 'browserConnectionEnabled': False, 'proxy': {'proxyType': 'direct'}, 'driverVersion': '1.2.0', 'driverName': 'ghostdriver', 'rotatable': False, 'acceptSslCerts': False, 'cssSelectorsEnabled': True, 'handlesAlerts': False, 'javascriptEnabled': True}

        
        self.dc['browsername'] = browsernames[random.randint(0,len(browsernames)-1)]
        self.dc['platform'] = platforms[random.randint(0,len(platforms)-1)]
        self.dc['version'] = '.'.join(list(str(random.randint(100,800))))
        print('b:%s p:%s v:%s'%(self.dc['browsername'],self.dc['platform'],self.dc['version']))
        self.dr = webdriver.PhantomJS(desired_capabilities=self.dc)
        self.dr.set_page_load_timeout(timeout)
        print('Now scraping %s'%link)
        curtry = 1
        while True:
            try:
                time.sleep(random.random()+0.3)
                self.dr.implicitly_wait(10)
                self.dr.get(link)
                self.contents = Selector(text=self.dr.page_source)
                self.dr.quit()
                if not self.contents.xpath('//div').extract():
                    time.sleep(500)
                    raise Warning('Page is Empty!')
                print(self.contents.xpath('//div/text()').extract_first())
                break
            except Exception as e:
                print('Exception raised:',end='')
                print('%s'%e)
                if curtry == tries:
                    self.isempty = True
                    print('Failed to scrap %s'%link)
                    print(e)
                    print('Failed to scrap %s'%link,file=logfile)
                    self.contents = None
                    break
                curtry += 1
                print('Trying to rescrape...%%%d time'%curtry)
                self.dr = webdriver.PhantomJS(desired_capabilities=self.dc)

    ## maybe add css version of find() later
    def find(self,expression,kind='xpath'):
        return self.contents.xpath(expression)

    def xpath(self,expression):
        return self.find(expression,kind='xpath')

    def randdcap(self):
        dcap['phantomjs.page.settings.userAgent'] = UAlist[random.randint(0,len(UAlist))]+str(random.randint(1,100))
        print(dcap)
        return dcap
