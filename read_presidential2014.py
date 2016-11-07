
# coding: utf-8

# The set of scripts in this notebook reads and retrives the results from first or second round of the Colombian presitential election in 2014. Its scrapes the data from the [Colombia's National Registry website](http://www3.registraduria.gov.co/elecciones/elecciones2014/presidente/1v/99PR1/DPR9999999_L1.htm) and returns two dataframes:  `df_regions14_1/2 and df_munis14_1/2`, containing data per region and per municipality/city respectively. 

# In[ ]:

import numpy as np, requests, re, pandas as pd, json
from bs4 import BeautifulSoup


# Regional and municipal results are in different `url` addresses with an standardized HTML format. The `read_data_page` function parses the HTML content to extract the desired information using `BeautifulSoup and regular expressions`. This function returns a dictionary:
# ```python
# {
#     'total_voters': (int) Total eligible voters
#     'voters': (int) Total actual votes
#     'CD_votes': (int) Votes for the candidate of the "Centro Democratico" party
#     'CD_votes_p': (float) Proportion of votes for the candidate of the "Centro Democratico" party
#     'UN_votes': (int) Votes for the candidate of the "Union Nacional" party
#     'UN_votes_p': (float) Proportion of votes for the candidate of the "Union Nacional" party
#     'CC_votes': (int) Votes for the candidate of the "Conservador Colombiano" party
#     'CC_votes_p': (float) Proportion of votes for the candidate of the "Conservador Colombiano" party
#     'PL_votes': (int) Votes for the candidate of the "Polo Democratico" party
#     'PL_votes_p': (float) Proportion of votes for the candidate of the "Polo Democratico" party
#     'AV_votes': (int) Votes for the candidate of the "Alianza Verde" party
#     'AV_votes_p': (float) Proportion of votes for the candidate of the "Alianza Verde" party
#     'blank_votes': (int) Votes for none of the candidates
#     'blank_votes_p': (float) Proportion of blank votes
#     'valid_votes': (int) Total valid votes
#     'unmarked_votes': (int) Votes not marked
#     'null_votes': (int) Null votes
# }
# ```

# In[146]:

def read_page_presidential14_1(url,suf):
    # This function reads the content of the 1st round of Colombian presidential election in 2014 
    
    candidates = {u'Juan Manuel Santos Calderón':'UN',u'Óscar Iván Zuluaga':'CD',u'Clara López':'PD',
              u'Martha Lucía Ramírez':'CC',u'Enrique Peñalosa':'AV'}
    
    output = {} # Dictionary containing the retrieved data
    raw = requests.get(url)
    pinput = BeautifulSoup(raw.content, "html.parser")
    
    # List of municipalities as xml tags
    try:
        muni_list = pinput.find('div', class_ = 'cajamunicip').find_all('li')
    except AttributeError:
        muni_list = []
    
    # Number of voters vs. number of people allowed to vote 
    nums = pinput.find('table', class_ = 'cdatos tizda').find_all('td', class_ = 'dato')[2:]
    output['total_voters'+suf] = int(nums[0].get_text().replace('.',''))
    output['voters'+suf] = int(nums[1].get_text().replace('.',''))
    
    #Blank votes
    temp = pinput.find('table', class_ = 'cdatos tder').find_all('tr')
    output['blank_votes'+suf] = int(temp[1].find('td', class_ = 'dato').get_text().replace('.',''))
    output['blank_votes_p'+suf] = float(temp[1].find('td', class_ = 'porciento').get_text().replace('%','').replace(',','.'))/100
    
    #Valid and invalid votes
    output['valid_votes'+suf] = int(temp[2].find('td', class_ = 'dato').get_text().replace('.',''))
    output['null_votes'+suf] = int(temp[3].find('td', class_ = 'dato').get_text().replace('.',''))
    output['unmarked_votes'+suf] = int(temp[4].find('td', class_ = 'dato').get_text().replace('.',''))
    
    #Votes per candidate
    results = pinput.find('table', title = 'Resultados de escrutinio final de candidatos').find('tbody').find_all('tr')
    for r in results:
        cand = r.find('div').get_text()
        party = candidates[cand]
        output[party+'_votes'+suf] = int(r.find('td', class_='abs').get_text().replace('.',''))
        output[party+'_votes_p'+suf] = float(r.find('td', class_='prc').get_text().replace('%','').replace(',','.'))/100
        pass
    
    return output, muni_list


# In[148]:

def data_pres2014(rd=2):
    # This function creates dictionaries for regions and municipalities with name, url votes statistics for each one
    # This script takes approximately 10 minutes
    
    if rd == 1:
        root_url = 'http://www3.registraduria.gov.co/elecciones/elecciones2014/presidente/1v'
        url  = root_url + "/99PR1/DPR9999999_L1.htm"
        suf = '14_1'
    else:
        root_url = 'http://www3.registraduria.gov.co/elecciones/elecciones2014/presidente/2v'
        url  = root_url + "/99PR2/DPR9999999_L1.htm"
        suf = '14_2'
    
    rurl = requests.get(url)
    pinput = BeautifulSoup(rurl.content, "html.parser")
    
    #Results for Colombia overall
    total_COL = read_page_presidential14_1(url,suf)
    
    reg_list = pinput.find('div', class_ = 'navsub').find_all('li') # List of regions as xml tags
    regions = {}; munis = {}; dc_zones = {} 
    for dpt in reg_list:
        reg_name = dpt.get_text().replace('.','').replace(',','')
        reg_url = root_url + dpt.find('a')['href'][2:]
        regions[reg_name] = {}
        regions[reg_name]['url'] = reg_url
        rdata = read_page_presidential14_1(reg_url,suf) # Extarcting data for the specific region
        regions[reg_name].update(rdata[0])

        # Creating dictionary for municipalities
        for muni in rdata[1]:
            muni_name = muni.get_text().replace('.','').replace(',','').replace('\n','').replace('Todo ','')

            if muni_name == 'Todo el departamento':
                continue
            
            if reg_name == 'BOGOTA DC':
                dc_zones[muni_name] = {}
                dc_zones_url = root_url + muni.find('a')['href'][2:]
                dc_zones[muni_name]['region'] = reg_name
                dc_zones[muni_name]['url'] = dc_zones_url

                rdata2 = read_page_presidential14_1(dc_zones_url,suf) # Extarcting data for the specific zone in BGOTA DC
                dc_zones[muni_name].update(rdata2[0]) 
            else:            
                munis[muni_name] = {}
                muni_url = root_url + muni.find('a')['href'][2:]
                munis[muni_name]['region'] = reg_name
                munis[muni_name]['url'] = muni_url

                rdata2 = read_page_presidential14_1(muni_url,suf) # Extracting data for the specific municipality
                munis[muni_name].update(rdata2[0])
        pass
    
    df_regions = pd.DataFrame.from_dict(regions, orient='index'); df_munis = pd.DataFrame.from_dict(munis, orient='index')
    df_dczones = pd.DataFrame.from_dict(dc_zones, orient='index')
    df_regions.drop('url', axis=1, inplace=True);
    
    return total_COL,df_regions,df_munis,df_dczones


# In[154]:

# total_COL,df_regions,df_munis,df_dczones = data_pres2014(2)
# df_regions.to_pickle('regions14_2')
# df_munis.to_pickle('munis14_2')
# df_dczones.to_pickle('dczones14_2')
# np.save('COL14_2.npy',total_COL)

