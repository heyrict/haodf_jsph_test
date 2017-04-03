# coding: utf-8
from selenium import webdriver
from scrapy import Selector
import pickle, os
from datetime import datetime
import pandas as pd, numpy as np
from pandas import DataFrame, Series
from dateutil import parser

log = open('log.txt','a')
print('----------\nlog start: %s\n----------'%datetime.today().strftime(r'%Y-%m-%d %H:%M'),file=log)
class WebContainer(object):
    def __init__(self,link,PhantomJSDriver=None):
        if PhantomJSDriver: self.dr = PhantomJSDriver
        else: self.dr = webdriver.PhantomJS()
        try:
            print('Now scraping %s'%link)
            self.dr.get(link)
            self.contents = Selector(text=self.dr.page_source)
            print('Succeeded in scraping %s'%link,file=log)
        except Exception as e:
            print('Failed to scrap %s'%link)
            print(e)
            print('Failed to scrap %s'%link,file=log)

    def find(self,expression,kind='xpath'):
        return self.contents.xpath(expression)

    def xpath(self,expression):
        return self.find(expression,kind='xpath')

if 'doctors.data' in os.listdir() and 'doctors_labels.data' in os.listdir():
    with open('doctors.data','rb') as f:
        doctors = pickle.load(f)
    with open('doctors_labels.data','rb') as f:
        doctors_labels = pickle.load(f)
else:
    dr = webdriver.PhantomJS()
    #省人医页面
    wc = WebContainer('http://www.haodf.com/hospital/DE4roiYGYZwX-bc2dcByMhc7g.htm',dr)
    sections = []
    for i in wc.xpath('//table[@id="hosbra"]//a[@class="blue"]'):
        sections.append((i.xpath('./text()').extract()[0],i.xpath('./@href').extract()[0]))

    doctors = []
    doctors_labels = []
    for i in sections:
        try:
            wc = WebContainer(i[1],dr)
        except:
            continue
        all_pages = set(wc.xpath('//a[@class="p_num"][contains(@href,"_")]/@href').extract())
        doctors_on_this_section = [(t.xpath('./text()').extract()[0],t.xpath('./@href').extract()[0]) for t in wc.xpath('//a[@class="name"][@target="_blank"]')]
        for j in all_pages:
            doctors_on_this_section += [(t.xpath('./text()').extract()[0],t.xpath('./@href').extract()[0]) for t in wc.xpath('//a[@class="name"][@target="_blank"]')]
        doctors_labels.append(i[0])
        doctors.append(doctors_on_this_section)

##疗效及态度满意度
sat_att = sat_eff = {'很不满意':1,'不满意':2,'一般':3,'满意':4,'很满意':5,'其他':0}
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


#从每一个医生界面抓取信息
patdf = DataFrame(columns=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost'])
for lblix in range(len(doctors)):
    for docix in range(len(doctors[lblix])):
        while 1:
            try:
                this_page = WebContainer(doctors[lblix][docix][1],dr)
            except Exception as e:
                print(e);continue
            break 
        a = this_page.xpath('//td[@class="center orange"]/a/@href').extract_first()
        if a:
            pass
        else:
            for pat in this_page.xpath('//table[@class="doctorjy"]'):
                curpat = pd.Series(index=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost'])
                #Time Processing
                t = pat.xpath('//td[contains(@style,"tex-align:right;")]').extract_first()
                try: t = parser.parse(t[3:])
                except: t = np.nan
                curpat['time'] = t

                #dlemd Processing
                patbriefinfo = pat.xpath('//td[@class="dlemd"]')
                ##aim
                for i in patbriefinfo.xpath('//td[@colspan="3"]/span/text()').extract():
                    t = i.split('：')
                    if t[0] in namspc: 
                        aim = [eval(namspc[t[0]])[i] for i in t[1].split('、') if i in eval(namspc[t[0]] else 1]
                        curpat[namspc[t[0]]] = aim

                ##satisfaction
                t = patbriefinfo.xpath('./table/tbody/tr')[-1].xpath('./td')
                for i in t[:2]:
                    try:
                        temp = namspc[i.xpath('text()').extract_first().split('：')[0]]
                        try:
                            degr = eval(temp)[i.xpath('span/text()').extract_first()]
                        except:
                            degr = 0
                        curpat[temp] = degr
                    except Exception as e:
                        print('Exception raised: %s'%e)
                
                #tbody processing
                pass
log.close()
