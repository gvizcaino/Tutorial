
# coding: utf-8

# The set of scripts in this notebook reads and retrives the results from the Colombian Peace Plebiscite in 2016. Its scrapes the data from the [Colombia's National Registry website](http://plebiscito.registraduria.gov.co/99PL/DPLZZZZZZZZZZZZZZZZZ_L1.htm) and returns two dataframes:  `df_regions and df_munis`, containing data per region and per municipality/city respectively. 

# In[ ]:

import numpy as np, requests, re, pandas as pd, json
from bs4 import BeautifulSoup


# Regional and municipal results are in different `url` addresses with an standardized HTML format. The `read_data_page` function parses the HTML content to extract the desired information using `BeautifulSoup and regular expressions`. This function returns a dictionary:
# ```python
# {
#     'total_voters': (int) Total eligible voters
#     'voters': (int) Total actual votes
#     'yes_votes': (int) Number of YES votes
#     'yes_votes_p': (float) Proportion of YES votes
#     'no_votes': (int) Number of NO votes
#     'no_votes_p': (float) Proportion of NO votes
#     'valid_votes': (int) Total valid votes
#     'unmarked_votes': (int) Votes not marked
#     'null_votes': (int) Null votes
# }
# ```

# An example of the dictionary structure for the municipality of SOACHA:
# ```python
# region:  'CUNDINAMARCA'
# url:  'http://plebiscito.registraduria.gov.co/99PL/DPL15247ZZZZZZZZZZZZ_L1.htm'
# total_voters : 201745
# voters : 90969
# yes_votes : 42449
# yes_votes_p : 0.4758
# no_votes : 46767
# no_votes_p:  0.5241
# valid_votes:  89216
# unmarked_votes:  289
# null_votes:  1464```

# In[146]:

def read_data_page(url):
    # This function reads the content of number of votes, type of votes, number of voters, etc... 
    
    output = {} # Dictionary containing the retrieved data
    raw = requests.get(url)
    pinput = BeautifulSoup(raw.content, "html.parser")
    
    # List of municipalities as xml tags
    try:
        muni_list = pinput.find('select', id = 'combo3').find_all('option')
    except AttributeError:
        muni_list = []
    
    # Number of voters vs. number of people allowed to vote 
    total_voters = pinput.find('div', class_ = 'cajaSupSegundaContainer').find('span', class_ = 'descripcionCaja').get_text()
    total_voters = total_voters.replace('.','')
    nums = re.compile(r"\d+").findall(total_voters)
    
    output['voters'] = int(nums[0])
    output['total_voters'] = int(nums[1])
    
    #Positive and negative votes
    votes = pinput.find_all('div', class_ = 'skill-bar-percent')
    temp = votes[0].get_text().replace('%','').replace(',','.')
    output['yes_votes_p'] = float(temp)/100
    temp = votes[1].get_text().replace('.','')
    output['yes_votes'] = int(re.compile(r"\d+").findall(temp)[0])
    temp = votes[2].get_text().replace('%','').replace(',','.')
    output['no_votes_p'] = float(temp)/100
    temp = votes[3].get_text().replace('.','')
    output['no_votes'] = int(re.compile(r"\d+").findall(temp)[0])
    
    #Valid and invalid votes
    temp = pinput.find('div', class_ = 'cajaInfPrimera').find('div', class_ = 'contenido').get_text().replace('.','')
    output['valid_votes'] = int(re.compile(r"\d+").findall(temp)[0])
    temp = pinput.find('div', class_ = 'cajaInfSegunda').find('div', class_ = 'contenido').get_text().replace('.','')
    output['unmarked_votes'] = int(re.compile(r"\d+").findall(temp)[0])    
    temp = pinput.find('div', class_ = 'cajaInfTercera').find('div', class_ = 'contenido').get_text().replace('.','')
    output['null_votes'] = int(re.compile(r"\d+").findall(temp)[0])    
    
    return output, muni_list


# In[148]:

# Creating dictionaries for regions and municipalities with name, url votes statistics for each one
# This script takes approximately 4.5 minutes
def data_plebiscite2016():
    root_url = 'http://plebiscito.registraduria.gov.co'
    url  = root_url + "/99PL/DPLZZZZZZZZZZZZZZZZZ_L1.htm"
    rurl = requests.get(url)
    pinput = BeautifulSoup(rurl.content, "html.parser")
    reg_list = pinput.find('select', id = 'combo2').find_all('option') # List of regions as xml tags
    regions = {}; munis = {}
    for dpt in reg_list:
        reg_name = dpt.get_text().replace('.','').replace(',','')

        if reg_name == 'Todos':
            reg_name = 'COLOMBIA'

        reg_url = root_url + dpt['value'][2:]
        regions[reg_name] = {}
        regions[reg_name]['url'] = reg_url
        rdata = read_data_page(reg_url) # Extracting data for the specific region
        regions[reg_name].update(rdata[0])

        if reg_name == 'COLOMBIA':
            continue

        # Creating dictionary for municipalities
        for muni in rdata[1]:
            muni_name = muni.get_text().replace('.','').replace(',','')

            if muni_name == 'Todos':
                continue

            munis[muni_name] = {}
            muni_url = root_url + muni['value'][2:]
            munis[muni_name]['region'] = reg_name
            munis[muni_name]['url'] = muni_url

            rdata2 = read_data_page(muni_url) # Extarcting data for the specific municipality
            munis[muni_name].update(rdata2[0])
        pass
    
    df_regions = pd.DataFrame.from_dict(regions, orient='index'); df_munis = pd.DataFrame.from_dict(munis, orient='index')
    df_regions.drop('url', axis=1, inplace=True); df_regions.drop('COLOMBIA', inplace=True); 
    df_munis.drop(df_munis[df_munis.no_votes == 0].index, axis=0, inplace=True)
    
    return df_regions,df_munis


# In[154]:

# df_regions,df_munis,df_dczones = data_plebiscite2016()
# df_regions.to_pickle('regions')
# df_munis.to_pickle('munis')

