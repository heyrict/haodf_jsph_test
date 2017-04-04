# coding: utf-8
## import necessary packages
### web-climbing libraries
from selenium import webdriver
from scrapy import Selector
### modules for storing data
import pickle, os, sys
import pandas as pd, numpy as np
from pandas import DataFrame, Series
### time processing
from datetime import datetime
from dateutil import parser

# initial browser

dr = webdriver.PhantomJS()
dr.set_page_load_timeout(15)

# get web-climbing libraries wrapped

class WebContainer(object):
    def __init__(self,link,PhantomJSDriver=None,logfile=sys.stdout):
        if PhantomJSDriver: self.dr = PhantomJSDriver
        else: self.dr = webdriver.PhantomJS()
        try:
            print('Now scraping %s'%link)
            while(1):
                try: self.dr.get(link);break
                except Exception as e:
                    print('Exception raised:',end='')
                    print(e)
                    print('Trying to rescrape...')
            self.contents = Selector(text=self.dr.page_source)
            print('Succeeded in scraping %s'%link,file=logfile)
        except Exception as e:
            print('Failed to scrap %s'%link)
            print(e)
            print('Failed to scrap %s'%link,file=logfile)

    ## maybe add css version of find() later
    def find(self,expression,kind='xpath'):
        return self.contents.xpath(expression)

    def xpath(self,expression):
        return self.find(expression,kind='xpath')

# global variables for labeling data

##疗效及态度满意度
sat_att = sat_eff = {'很不满意':2,'不满意':3,'一般':4,'满意':5,'很满意':6,'其他':0,'还不知道':1}
##看病目的
aim = {'治疗':3,'未填':0,'诊断':2,'其他':1,'咨询问题':4}
##选择该医生的理由
reason = {'网上评价':3,'医生推荐':2,'其他':1,'未填':0,'熟人推荐':4,}
##本次挂号途径
reservation = {'网络预约':3,'排队挂号':2,'其他':1,'未填':0}
##目前病情状态
status = {'有好转':3,'其他':1,'未见好转':2,'痊愈':4,'未填':0}
##名称匹配
namspc = {'看病目的':'aim','疗效':'sat_eff','态度':'sat_att','选择该医生就诊的理由':'reason','本次挂号途径':'reservation','目前病情状态':'status','本次看病费用总计':'cost'}

def current_page_to_df(this_page,logfile,lblix,docix):
    #从医生主页抓取所有患者信息
    if type(this_page)==type(None): return
    global sat_att, sat_eff, aim, reason, reservation, status, namspc, temp
    curpatdf = DataFrame(columns=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost'])
    
    for pat in this_page.xpath('//table[@class="doctorjy"]'):
        curpat = pd.Series({'lblix':lblix,'docix':docix},index=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost'])
        #Time Processing
        t = pat.xpath('.//td[contains(@style,"text-align:right;")]/text()').extract_first()
        try: t = parser.parse(t[3:]).strftime(r'%Y-%m-%d')
        except: t = np.nan
        curpat['time'] = t

        #dlemd Processing
        patbriefinfo = pat.xpath('.//td[@class="dlemd"]')
        ##aim
        for i in patbriefinfo.xpath('.//td[@colspan="3"]/span/text()').extract():
            t = i.split('：')
            if t[0] in namspc.keys(): 
                curaim = [eval(namspc[t[0]])[i] if i in eval(namspc[t[0]]) else 1 for i in t[1].split('、')] 
                curpat[namspc[t[0]]] = str(curaim)

        ##satisfaction
        t = patbriefinfo.xpath('./table/tbody/tr')[-1].xpath('./td')
        for i in t[:2]:
            try:
                text = i.xpath('text()').extract_first()
                if text: 
                    temp = namspc[text[:-1]]
                    try:
                        degr = eval(temp)[i.xpath('span/text()').extract_first()]
                    except:
                        degr = 0
                    curpat[temp] = degr
            except Exception as e:
                print('Exception raised: %s'%e)
                continue
        
        #tbody processing
        patadditinfo = pat.xpath('.//tbody//td[@valign="top"][@height="40px"]')
        for i in patadditinfo.xpath('div'):
            try:
                if not i.xpath('span/text()').extract_first(): continue
                temp = namspc[i.xpath('span/text()').extract_first()[:-1]]
                try:
                    tval = float(i.xpath('text()').extract_first()[:-1]) if temp=='cost' else eval(temp)[i.xpath('text()').extract_first()]
                except:
                    tval = 0
                curpat[temp] = tval
            except Exception as e:
                print('Exception raised: %s'%e)
                continue
        curpatdf = curpatdf.append(curpat,ignore_index=True)
    return curpatdf

def scrape_hospital_page(link,prov_name,hosp_name,logfile):
    #爬取某医院下所有医生主页并返回
    # initial directory for storing data
    curdir = './%s/%s'%(prov_name,hosp_name)
    if prov_name not in os.listdir(): os.mkdir('%s'%prov_name)
    if hosp_name not in os.listdir('./%s/'%prov_name): os.mkdir('%s'%(prov_name+'/'+hosp_name))
    if 'doctors.data' in os.listdir(curdir) and 'doctors_labels.data' in os.listdir(curdir):
        # load stored data
        print('Stored index data found in %s'%curdir,file=logfile)
        with open(curdir+'/doctors.data','rb') as f:
            doctors = pickle.load(f)
        with open(curdir+'/doctors_labels.data','rb') as f:
            doctors_labels = pickle.load(f)
    else:
        # if stored data not found
        wc = WebContainer(link,dr,logfile)
        ## get all sections
        sections = []
        for i in wc.xpath('//table[@id="hosbra"]//a[@class="blue"]'):
            sections.append((i.xpath('./text()').extract()[0],i.xpath('./@href').extract()[0]))

        ## get doctors in every section
        doctors = []
        doctors_labels = []
        for i in sections:
            wc = WebContainer(i[1],dr,logfile)
            doctors_on_this_section = [(t.xpath('./text()').extract()[0],t.xpath('./@href').extract()[0]) for t in wc.xpath('//a[@class="name"][@target="_blank"]')]
            try:
                all_pages = range(1,int(wc.xpath('//a[@class="p_text"][@rel="true"]/text()').extract_first().strip()[1:-1])+1)
            except AttributeError as e:
                ### if no more than one page exists
                all_pages = [1]
                doctors_labels.append(i[0])
                doctors.append(doctors_on_this_section)
                continue

            templatel = wc.xpath('//div[@class="p_bar"]/a[@class="p_num"]/@href').extract_first().split('2.htm')
            try: 
                templatel[1] = '.htm'+templatel[1]
                if len(templatel) != 2: raise ValueError('Template Link list with more or less than 2 elements.')
            except Exception as e:
                print('Error raised when finding all page numbers on page %s:\n\t%s'%(a,e))
                continue

            ### fine all pages
            for j in all_pages:
                j = str(j).join(templatel)
                wc = WebContainer(j,dr,logfile)
                doctors_on_this_section += [(t.xpath('./text()').extract()[0],t.xpath('./@href').extract()[0]) for t in wc.xpath('//a[@class="name"][@target="_blank"]')]
            doctors_labels.append(i[0])
            doctors.append(doctors_on_this_section)
        
        #stores all indexes
        with open(curdir+'/doctors.data','wb') as f:
            pickle.dump(doctors, f)
        with open(curdir+'/doctors_labels.data','wb') as f:
            pickle.dump(doctors_labels,f)
        print('Index data stored in %s'%curdir,file=logfile)
    return doctors,doctors_labels

def scrape_doct_page(doctors,doctors_labels,logfile):
    #从每一个医生主页抓取患者信息并返回
    patdf = DataFrame(columns=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost'])
    for lblix in range(len(doctors)):
        for docix in range(len(doctors[lblix])):
            while 1:
                try:
                    this_page = WebContainer(doctors[lblix][docix][1],dr,logfile)
                except Exception as e:
                    print(e);continue
                break 
            a = this_page.xpath('//td[@class="center orange"]/a/@href').extract_first()
            if a:
                #handling all patient data
                wc = WebContainer(a,dr,logfile)
                a = wc.xpath('//div[@class="p_bar"]/a[@class="p_num"]/@href').extract_first()
                templatel = a.split('2.htm'); templatel[1]+='.htm'
                if len(templatel)!=2: print('Error in handling adress: %s'%a);continue
                curpagnum = 1
                try:
                    totpagnum = int(wc.xpath('//a[@class="p_text"][@rel="true"]/text()').extract_first()[1:-1])
                except Exception as e:
                    print('Error raised when finding all page numbers on page %s:\n\t%s'%(a,e))
                    continue
                while curpagnum<=totpagnum:
                    if curpagnum != 1: 
                        wc = WebContainer(str(curpagnum).join(templatel),dr,logfile)
                    else: wc = this_page
                    resdf = current_page_to_df(wc,logfile,lblix,docix)
                    if type(resdf) != type(None): patdf = patdf.append(resdf,ignore_index=True)
                    curpagnum += 1
                    
            else:
                resdf = current_page_to_df(this_page,logfile,lblix,docix)
                if type(resdf) != type(None): patdf = patdf.append(resdf,ignore_index=True)
    return patdf


def get_all_hosp(link,prov_name,logfile):
    #抓取所有本页面上医院清单并以n×2列表返回
    if prov_name not in os.listdir(): os.mkdir('%s'%prov_name)
    curdir = './'+prov_name
    if 'hosp_list.data' in os.listdir(curdir):
        with open(curdir+'/hosp_list.data','rb') as f:
            l = pickle.load(f)
    else:
        wc = WebContainer(link,dr,logfile)
        l = []
        for i in wc.xpath('//li/a[@target="_blank"]'):
            cn = i.xpath('./text()').extract_first()
            cl = i.xpath('./@href').extract_first()
            if cl[:4] != 'http': cl = 'http://www.haodf.com'+cl
            if cn and cl: l.append((cn,cl))
        with open(curdir+'/hosp_list.data','wb') as f:
            pickle.dump(l,f)
    return l


def get_all_prov(logfile):
    if 'all_prov.data' in os.listdir():
        with open('all_prov.data','rb') as f:
            l = pickle.load(f)
    else:
        wc = WebContainer('http://www.haodf.com/yiyuan/hebei/list.htm',dr,logfile)
        l = []
        for i in wc.xpath('//div[@class="kstl"]/a'):
            cn = i.xpath('./text()').extract_first()
            cl = i.xpath('./@href').extract_first()
            if cn and cl: l.append((cn,cl))
        with open('all_prov.data','wb') as f:
            pickle.dump(l,f)
    return l

