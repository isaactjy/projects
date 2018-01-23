from bs4 import BeautifulSoup
import pandas as pd
import re
import datetime
from urllib.request import Request, urlopen

print(datetime.datetime.now()) # For checking the speed of the code
# M1

site = urlopen("https://www.m1.com.sg/personal/mobile/phones/filters/all-plans/all/all/0/1500/0/0/none")
soup = BeautifulSoup(site.read(),"html.parser")
links=[]

# For parsing the data
def clean_text(s):
    # Check for two exceptions - Unlimited and empty
    if "Unlimited" in s:
        num = 10000
        return num

    if s == "":
        num = ""
        return num

    # Otherwise clean the string and split into cases
    new_s = re.sub("[^0-9+.]","",s)
    # For "3 + 2 GB" Case
    if new_s == "300+1":
        num = 1.3
    # For empty case
    elif new_s == "":
        num = new_s
    # For unlimited
    else:
        # For X GB + Y GB
        if "+" in new_s:
            num = float(eval(new_s))
        # For the case 300MB
        elif new_s == "300":
            num = 0.3
        else:
            num = float(new_s)
    return num

#################################
## Contract
#################################

for link in soup.find_all("a", { "class" : "light-blue hidetag" }): 
    new_link = link['href']
    new_link_split = new_link.split()
    final_link = ""
    for i in range(0,len(new_link_split)):
        if i < len(new_link_split) - 1:
            final_link += new_link_split[i] + '%20'
        else:
            final_link += new_link_split[i]
    links.append(final_link)

df_contract = pd.DataFrame(columns=('Provider','Phone','Plan','TalkTime(Mins)','SMS/MMS','Data(GB)','PayNow($)','PerMonth($)'))
# Going through of each of the phone links
for link in links:
    site2 = urlopen("https://www.m1.com.sg" + link)
    soup2 = BeautifulSoup(site2.read(),"html.parser")

    df_model = pd.DataFrame(columns=('Provider','Phone','Plan','TalkTime(Mins)','SMS/MMS','Data(GB)','PayNow($)','PerMonth($)'))

    name = soup2.find("div",{"class":"title"})
    # Get the model name
    model = name.get_text()
    # Remove whitespaces and \ characters
    model = re.sub('\s+',' ',model)

    plans = []
    # Plan name
    for div in soup2.find_all("div", { "class" : "title color-orange font-size-14 font-weight-bold" }):
        plans.append(div.get_text())

    details = []
    import csv
    # TalkTime, SMS/MMS, Data
    for div in soup2.find_all("div", { "class" : "desc font-size-14" }):
        num = clean_text(div.get_text())
        details.append(num)

    price1 = []
    # Pay Now 
    for div in soup2.find_all("div", { "class" : "font-size-15 line-height-20 color-orange font-weight-bold" }):
        num = clean_text(div.get_text())
        price1.append(num)

    # Per Month
    price2 = []
    for div in soup2.find_all("div", { "class" : "font-size-15 line-height-20 color-3" }):
        num = clean_text(div.get_text())
        price2.append(num)
        
    # Store the data in a dataframe (by rows)
    for i in range(0,len(plans)):
        # print(i)
        # This would be price2 is missing (no monthly installments)
        if plans[i] == 'Equipment Only':
            df_model.loc[i] = ['M1',model,plans[i],details[3*i],details[3*i + 1],details[3*i + 2],price1[i],'']
        else:
            df_model.loc[i] = ['M1',model,plans[i],details[3*i],details[3*i + 1],details[3*i + 2],price1[i],price2[i]]
    # Add our data frame for this model to the full dataframe
    # print('Dataframe done.')
    df_contract = df_contract.append(df_model)

# Circles.life
req = Request("https://pages.circles.life/devices/",headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(urlopen(req).read(),"html.parser")

df_model2 = pd.DataFrame(columns=('Provider','Phone','Plan','TalkTime(Mins)','SMS/MMS','Data(GB)','PayNow($)','PerMonth($)'))
# Get the names of all the phones avaliable
phones = []
for p in soup.findAll("p", { "class" : "tl f4 mb0 fw6 mt0" }):
    phones.append(p.get_text())
# This class tag contains both the phone name and prices, so we will just work with this list
for i in range(len(phones)):
    # First split to obtain the phone name
    first_split = phones[i].split("FROM")
    # first_split contains the phone name in first_split[0] and prices in first_split[1] 
    # Split the other half which contains the prices and plan
    second_split = first_split[1].split()

    # We all the components we need. Time to assemble the dataframe!  
    df_model2.loc[i] = ['Circles.life',first_split[0],'Basic',clean_text(second_split[13]),0,6,clean_text(second_split[2]),clean_text(second_split[0])]

df_contract = df_contract.append(df_model2)

#################################
## SIM only 
#################################


site = urlopen("https://www.m1.com.sg/personal/mobile/plans#mysim")
soup = BeautifulSoup(site.read(),"html.parser")

df_sim = pd.DataFrame(columns=('Provider','Plan','TalkTime(Mins)','SMS/MMS','Data(GB)','PerMonth($)'))

plans = []
details = []

# M1
for td in soup.find_all("td", { "class" : "width-20p bold color-orange vertical-align-middle margin-0 text-left margin-0 background-color-fb" }):
    plans.append(td.get_text())

for td in soup.find_all("td", { "class" : "width-15p center vertical-align-middle margin-0 background-color-fb" }):
    details.append(td.get_text())

for i in range(0,len(plans)):
    df_model = pd.DataFrame(columns=('Provider','Plan','TalkTime(Mins)','SMS/MMS','Data(GB)','PerMonth($)'))
    if "mySIM" in plans[i]:
        df_model.loc[i] = ['M1',plans[i],clean_text(details[4*i + 1]),clean_text(details[4*i + 2]),clean_text(details[4*i + 3]),clean_text(details[4*i])]
        df_sim = df_sim.append(df_model)

#################################
## Write to excel
#################################

from pandas import ExcelWriter
writer = ExcelWriter('telecom_demo.xlsx')
df_contract.to_excel(writer,'Contract')
df_sim.to_excel(writer,'SIMonly')
writer.save()


print('Done.')
print(datetime.datetime.now())
