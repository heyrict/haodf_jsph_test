from haodf_jsph_test_1 import *
q = input('Where to store log data?[l(ogfile)/s(tdout)]: ')[0].lower()
while 1:
    if q == 'l': logfile = open('log.txt','a');break
    elif q == 's': import sys;logfile=sys.stdout;break
    else: print('Cannot recognize input. Check if you entered [l(ogfile)/s(tdout)]')
print('\n----------\nlog start: %s\n----------'%datetime.today().strftime(r'%Y-%m-%d %H:%M'),file=logfile)

#all_prov: n*2 list
all_prov = get_all_prov(logfile)

for prov in all_prov:
    all_hosp = get_all_hosp(prov[1],prov[0],logfile)

    for hosp in all_hosp:
        if '%s'%prov[0] not in os.listdir(): os.mkdir(prov[0])
        if '%s'%(hosp[0]) not in os.listdir(prov[0]): os.mkdir('%s/%s'%(prov[0],hosp[0]))
        if 'pat_data.csv' not in os.listdir('%s/%s'%(prov[0],hosp[0])):

            doctors,doctors_labels = scrape_hospital_page(hosp[1],prov[0],hosp[0],logfile)
            doct_data = pd.DataFrame(columns=['docix','lblix','doct_name','lblname'])
            for i, j in zip(doctors,range(len(doctors_labels))):
                t = pd.DataFrame(np.array(i).T[0],columns=['doct_name'])
                t['docix'] = range(len(t))
                t['lblix'] = j
                t['lblname'] = doctors_labels[j]
                doct_data = doct_data.append(t)
            curdoct, patdf = scrape_doct_page(doctors,doctors_labels,logfile)
            patdf.to_csv('%s/%s/pat_data.csv'%(prov[0],hosp[0]),index=False)
            doct_data.merge(curdoct).to_csv('%s/%s/doct_data.csv'%(prov[0],hosp[0]),index=False)
            print('-----End Scraping hosp %s at %s-----'%(hosp[0],datetime.today().strftime(r'%Y-%m-%d %H:%M')),file=logfile)
        else:
            print('pat_data.csv found in ./%s/%s. Skipping...'%(hosp[0],prov[0]))

log.close()
