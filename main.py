from haodf_jsph_test_1 import *
logfile = open('log.txt','a')
print('----------\nlog start: %s\n----------'%datetime.today().strftime(r'%Y-%m-%d %H:%M'),file=logfile)

#all_prev: n*2 list
all_prov = get_all_prov(logfile)

for prov in all_prov:
    all_hosp = get_all_hosp(prov[1],prov[0],logfile)

    for hosp in all_hosp:
        doctors,doctors_labels = scrape_hospital_page(hosp[1],prov[0],hosp[0],logfile)
        
        if '%s'%prov[0] not in os.listdir(): os.mkdir(prov[0])
        if '%s'%(hosp[0]) not in os.listdir(prov[0]): os.mkdir('%s/%s'%(prov[0],hosp[0]))
        if hosp[0]+'.csv' not in os.listdir(prov[0]):
            print('%s.csv found in /%s. Skipping...'%(hosp[0],prov[0]))
            scrape_doct_page(doctors,doctors_labels,logfile).to_csv('%s/%s.csv'%(prov[0],hosp[0]),index=False)

log.close()
