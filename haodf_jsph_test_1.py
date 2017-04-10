# coding: utf-8
## import necessary packages
### modules for storing data
import pickle, os, sys, re
import pandas as pd, numpy as np
from pandas import DataFrame, Series
### time processing
from datetime import datetime
from dateutil import parser

# initial browser
from selenium import webdriver
from webcontainer import WebContainer
from data_processing import *
dr = webdriver.PhantomJS()
dr.set_page_load_timeout(15)


# global variables for labeling data

def true_link(lnk):
    if type(lnk) == str:
        f = lnk[0]
        if lnk[:4] == 'http': return lnk
        elif f == '/': return 'http://www.haodf.com' + lnk
    
    else:
        return [true_link(i) for i in lnk]

def get_illness(logfile=sys.stdout):
    # returns dict of (illness_ix, illness_link)
    ## illness_ix = '%02d%03d%03d' % (section,subsection,illness_name)
    ## check if local data exists
    if 'index_data' not in os.listdir(): os.mkdir('index_data')
    if 'illness_dict_flipped.csv' in os.listdir('index_data'):
        illness_dict_flipped = pd.read_csv('index_data/illness_dict_flipped.csv')
        print('illness_dict.csv found. Skipping...',file=logfile)
    else:
        illness_dict = pd.DataFrame(columns=['illness_ix','illness_name','illness_link'])
        subsection_dict = pd.DataFrame(columns=['section_ix','subsection_ix','subsection_name'])
        ## get all sections
        sections = WebContainer('http://www.haodf.com/jibing/erkezonghe/list.htm',logfile).xpath('//div[@class="kstl"]//a')
        section_df = pd.DataFrame(np.array([sections.xpath('./@href').extract(),sections.xpath('./text()').extract()]).T,columns=['section_link','section_name'])
        section_df['section_ix'] = np.arange(len(section_df))
        for i in range(len(section_df)):
            subsections = WebContainer(true_link(section_df.ix[i,'section_link']),logfile).xpath('//div[@class="ksbd"]//a')
            subsection_df = pd.DataFrame(np.array([subsections.xpath('./@href').extract(),subsections.xpath('./text()').extract()]).T,columns=['subsection_link','subsection_name'])
            subsection_df['subsection_ix'] = np.arange(len(subsection_df))
            subsection_df['section_ix'] = section_df.ix[i,'section_ix']
            subsection_dict = subsection_dict.append(subsection_df[['section_ix','subsection_ix','subsection_name']],ignore_index=True)
            for j in range(len(subsection_df)):
                illness = WebContainer(true_link(subsection_df.ix[j,'subsection_link']),logfile).xpath('//div[@class="m_ctt_green"]//a')
                illness_df = pd.DataFrame(np.array([illness.xpath('./@href').extract(),illness.xpath('./text()').extract()]).T,columns=['illness_link','illness_name'])
                illness_df['illness_ix'] = np.arange(len(illness_df))
                illness_df['illness_ix'] = illness_df['illness_ix'].map(lambda x: "%02d%03d%03d"%(section_df.ix[i,'section_ix'],subsection_df.ix[j,'subsection_ix'],x))
                illness_dict = illness_dict.append(illness_df,ignore_index=True)

        section_df[['section_ix','section_name']].to_csv('index_data/section_dict.csv',index=False)
        illness_dict.to_csv('index_data/illness_dict.csv',index=False)
        print('illness_dict stored in ./index_data/',file=logfile)

        illness_dict_flipped = pd.DataFrame(pd.Series(flip_dict_full(dict(illness_dict[['illness_ix','illness_link']].values)),name='illness_ixs')).reset_index()
        illness_dict_flipped.rename_axis({'index':'illness_link'},axis=1,inplace=True)
        illness_dict_flipped['illness_ix_flipped'] = np.arange(len(illness_dict_flipped))
        illness_dict_flipped[['illness_ix_flipped','illness_link','illness_ixs']].to_csv('index_data/illness_dict_flipped.csv',index=False)
        print('illness_dict_flipped stored in ./index_data/',file=logfile)
        
        subsection_dict.to_csv('index_data/subsection_dict.csv',index=False)
        print('subsection_dict stored in ./index_data/',file=logfile)

    illness_dict_flipped['illness_link'] = illness_dict_flipped['illness_link'].map(true_link) 
    return dict(illness_dict_flipped[['illness_link','illness_ix_flipped']].values)

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
##名称匹配
docsetnamspc = {'疗效满意度':'tot_sat_eff','态度满意度':'tot_sat_att','累计帮助患者数':'tot_NoP','近两周帮助患者数':'NoP_in_2weeks'}

illnessix = get_illness()
# illness_ix = '1%02d%03d%03d' % (section,subsection,illness_name)
if 'illness_add_dict.csv' not in os.listdir('index_data'):
    illness_add_dict = pd.DataFrame(columns=['illness_ix','illness_link'])
else:
    illness_add_dict =  pd.read_csv('index_data/illness_add_dict.csv') 


def current_page_to_df(this_page,logfile,lblix,docix):
    # fetch dictionary of all illness
    global illnessix
    global illness_add_dict
    #从医生主页抓取所有患者信息
    if type(this_page)==type(None): return
    global sat_att, sat_eff, aim, reason, reservation, status, namspc, temp
    curpatdf = DataFrame(columns=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost','illness','patnam'])
    
    for pat in this_page.xpath('//table[@class="doctorjy"]'):
        curpat = pd.Series({'lblix':lblix,'docix':docix},index=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost','illness','patnam'])
        #Time Processing
        t = pat.xpath('.//td[contains(@style,"text-align:right;")]/text()').extract_first()
        try: t = parser.parse(t[3:]).strftime(r'%Y-%m-%d')
        except: t = np.nan
        curpat['time'] = t

        #dlemd Processing
        patbriefinfo = pat.xpath('.//td[@class="dlemd"]')
        ## illness
        try:
            tempilns = patbriefinfo.xpath('.//td[@colspan="3"]//@href').extract_first()
            tempilns = tempilns.strip() if tempilns else None
            if not tempilns: pass
            elif tempilns in illnessix:
                curpat['illness'] = illnessix[tempilns] 
            elif tempilns in illness_add_dict['illness_link'].unique():
                curpat['illness'] = int(illness_add_dict[illness_add_dict['illness_link']==tempilns]['illness_ix'])
            elif re.findall('.htm',tempilns):
                curpat['illness'] = len(illness_add_dict)+100000000
                illness_add_dict = illness_add_dict.append({'illness_link':tempilns,'illness_ix':len(illness_add_dict)+100000000},ignore_index=True)
                illness_add_dict.to_csv('index_data/illness_add_dict.csv',index=False) 
            else:
                print('Info: illness %s not found in database'%curpat['illness'],file=logfile)
        except Exception as e: print('Exception on adding illness raised: %s'%e)

        ## aim
        for i in patbriefinfo.xpath('.//td[@colspan="3"]/span/text()').extract():
            t = i.split('：')
            if t[0] in namspc.keys(): 
                curaim = [eval(namspc[t[0]])[i] if i in eval(namspc[t[0]]) else 1 for i in t[1].split('、')] 
                curpat[namspc[t[0]]] = str(curaim)
        t = patbriefinfo.xpath('.//td[@colspan="2"]/text()').extract_first().split('：')
        if t[0] == '患者':
            if re.findall('\*\*\*',t[1]):
                curpat['patnam'] = t[1][0]
            elif re.findall('\.\*',t[1]):
                curpat['patnam'] = t[1].split('(')[0]
            else:
                curpat['patnam'] = np.nan

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

def scrape_hospital_page(link,prov_name,hosp_name,logfile=sys.stdout):
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
        wc = WebContainer(link,logfile)
        ## get all sections
        sections = []
        for i in wc.xpath('//table[@id="hosbra"]//a[@class="blue"]'):
            sections.append((i.xpath('./text()').extract()[0],i.xpath('./@href').extract()[0]))

        ## get doctors in every section
        doctors = []
        doctors_labels = []
        for i in sections:
            wc = WebContainer(i[1],logfile)
            if wc.isempty: continue
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

            ### find all pages
            for j in all_pages:
                j = str(j).join(templatel)
                wc = WebContainer(j,logfile)
                if wc.isempty: continue
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

def scrape_doct_page(doctors,doctors_labels,logfile=sys.stdout):
    #从每一个医生主页抓取患者信息并返回
    patdf = DataFrame(columns=['lblix','docix','time','aim','reason','sat_eff','sat_att','reservation','status','cost'])
    doctdf = DataFrame(columns=['lblix','docix','hot','tot_sat_eff','tot_sat_att','tot_NoP','NoP_in_2weeks'])
    for lblix in range(len(doctors)):
        for docix in range(len(doctors[lblix])):
            # scrape the current page
            this_page = WebContainer(doctors[lblix][docix][1],logfile)
            if this_page.isempty: continue
            # get doctor's info
            curdoct = Series({'lblix':lblix,'docix':docix},index=['lblix','docix','hot','tot_sat_eff','tot_sat_att','tot_NoP','NoP_in_2weeks'])
            curdoct['hot'] = this_page.xpath('//div[@class="fl r-p-l"]/p[@class="r-p-l-score"]/text()').extract_first()
            tscore = [i.strip() for i in this_page.xpath('//div[@class="fl score-part"]//text()').extract() if i.strip()]
            for scl in tscore:
                sclp = scl.split('：')
                try:
                    curdoct[docsetnamspc[sclp[0]]] = int(split_wrd(sclp[1],'%',''))
                except:
                    pass

            # check if there is multiple pages of patients' comments
            a = this_page.xpath('//td[@class="center orange"]/a/@href').extract_first()

            # if multiple pages exists
            if a:
                # handling all patient data
                wc = WebContainer(a,logfile)
                if wc.isempty: continue
                a = wc.xpath('//div[@class="p_bar"]/a[@class="p_num"]/@href').extract_first()
                templatel = a.split('2.htm'); templatel[1]+='.htm'
                if len(templatel)!=2: print('Error in handling adress: %s.Skipping'%a,file=logfile);continue
                ## get all page numbers
                curpagnum = 1
                try:
                    totpagnum = int(wc.xpath('//a[@class="p_text"][@rel="true"]/text()').extract_first()[1:-1])
                except Exception as e:
                    print('Error raised when finding all page numbers on page %s:\n\t%s'%(a,e))
                    continue
                while curpagnum<=totpagnum:
                    ## scrape all pages
                    if curpagnum != 1: 
                        wc = WebContainer(str(curpagnum).join(templatel),logfile)
                    else: wc = this_page
                    resdf = current_page_to_df(wc,logfile,lblix,docix)
                    if type(resdf) != type(None): patdf = patdf.append(resdf,ignore_index=True)
                    curpagnum += 1
                    
            else:
                # only one page exists
                resdf = current_page_to_df(this_page,logfile,lblix,docix)
                if type(resdf) != type(None): patdf = patdf.append(resdf,ignore_index=True)

            doctdf = doctdf.append(curdoct,ignore_index=True)
    return doctdf, patdf


def get_all_hosp(link,prov_name,logfile=sys.stdout):
    # 抓取所有本页面上医院清单并以n×2列表返回
    # read metadata if exists
    if prov_name not in os.listdir(): os.mkdir('%s'%prov_name)
    curdir = './'+prov_name
    if 'hosp_list.data' in os.listdir(curdir):
        with open(curdir+'/hosp_list.data','rb') as f:
            l = pickle.load(f)
    else:
        wc = WebContainer(link,logfile)
        l = []
        for i in wc.xpath('//li/a[@target="_blank"]'):
            cn = i.xpath('./text()').extract_first()
            cl = i.xpath('./@href').extract_first()
            if cl[:4] != 'http': cl = 'http://www.haodf.com'+cl
            if cn and cl: l.append((cn,cl))
        with open(curdir+'/hosp_list.data','wb') as f:
            pickle.dump(l,f)
    return l


def get_all_prov(logfile=sys.stdout):
    if 'all_prov.data' in os.listdir():
        with open('all_prov.data','rb') as f:
            l = pickle.load(f)
    else:
        wc = WebContainer('http://www.haodf.com/yiyuan/hebei/list.htm',logfile)
        l = []
        for i in wc.xpath('//div[@class="kstl"]/a'):
            cn = i.xpath('./text()').extract_first()
            cl = i.xpath('./@href').extract_first()
            if cn and cl: l.append((cn,cl))
        with open('all_prov.data','wb') as f:
            pickle.dump(l,f)
    return l

