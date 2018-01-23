# Python libraries
import sys
import time
import telepot
import requests
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import pandas as pd
import xlrd
from pandas import ExcelWriter
from pandas import ExcelFile
import imgkit
from telepot import DelegatorBot
from telepot.delegate import pave_event_space, per_chat_id, create_open

start = """Are you constantly wanting to change phones or to change plans? Fret not, TelcoBot will aid you in your search of that desired plan or dream phone.
Based on the selections you make, TelcoBot will help you find a suitable plan based on the your desired requirements. 
TelcoBot will also help you check out the latest phone prices. All these information will be output to you for you to consider which phone to purchase and which contract plan to commit to. 
Press /request to begin"""
TOKEN = '-----YOUR BOT TOKEN HERE--------'

# Read from Excel (not needed in the actual version - only for technical demo)
df_con = pd.read_excel('telecom.xlsx', 'Contract')
df_sim = pd.read_excel('telecom.xlsx', 'SIMonly')

# Set parameters for printing dataframe as an image using imgkit
path_wkthmltoimage = 'wkhtmltoimage.exe' 
config = imgkit.config(wkhtmltoimage=path_wkthmltoimage) 
filename = 'out.html' 
outname = 'out.jpg'

# Store phone,plan and telco lists (for functions 0 and 2)
plan_list = df_con['Plan'].unique()
phone_list = df_con['Phone'].unique()
phone_list.sort()
telco_list = df_con['Provider'].unique()

class TelcoBot(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(TelcoBot, self).__init__(include_callback_query=True, *args, **kwargs)
        self.data_u = None
        self.data_l = None
        self.price_u = None
        self.price_l = None
        self.plan_type = None
        self.telco = None
        
    # Choose by Model to display prices for a specific phone model
    def function0(self,phone):
        df_phone = df_con[df_con.loc[:,'Phone']==phone]
        plan_cat = []
        for permonth in df_phone.loc[:,'PerMonth($)']:
            if (permonth>25 and permonth<32): #value
                plan_cat += ['1. Value Plan $28']
            elif (permonth>39 and permonth<49): #basic
                plan_cat += ['2. Basic Plan $42']
            elif (permonth>60 and permonth<70): #Mid-tier
                plan_cat += ['3. Mid-Tier   $68']
            elif (permonth>80 and permonth<96): #Mid high
                plan_cat += ['4. Mid-High   $88']
            elif (permonth>100 and permonth<110):#high tier
                plan_cat += ['5. High-Tier $108']
            elif (permonth>200):                #premium
                plan_cat += ['6. Premium   $238']
            else:
                plan_cat += ['NIL']
        plan_series = pd.Series(plan_cat)
        df_phone.loc[:,('Plan Cat')] = plan_series.values

        df_phone = df_phone.reset_index()
        df_phone_pivot = pd.pivot_table(df_phone,index=['Plan Cat'],columns=['Provider'],values=['PayNow($)'],fill_value='N.A.')
        #droping unclass plan cats
        try:
            df_phone_pivot = df_phone_pivot.drop(['NIL'])
        except:
            None
        df_phone_pivot.columns = df_phone_pivot.columns.set_levels([str(phone)], level=0) #renaming the table title

        return df_phone_pivot

    # Choose by Plan to display sim only mobile plans
    def function1_sim(self,data_l,data_u,price_l,price_u):

        df_out = df_sim[(df_sim['Data(GB)'] >= data_l) & (df_sim['Data(GB)'] <= data_u) & (df_sim['PerMonth($)'] >= price_l) & (df_sim['PerMonth($)'] <= price_u)]
        df_out = df_out.sort_values(['Provider','PerMonth($)'],ascending=[1,1])
        #df_filtered = df_filtered.sort_values(['PerMonth($)'],ascending=[1])
        df_out = df_out.reset_index()
        df_out = df_out.drop(['index'],axis=1)
        return df_out

    # Choose by Plan to display contract mobile plans
    def function1_con(self,data_l,data_u,price_l,price_u):
        df_out = df_con[(df_con['Data(GB)'] >= data_l) & (df_con['Data(GB)'] <= data_u) & (df_con['PerMonth($)'] >= price_l) & (df_con['PerMonth($)'] <= price_u)]
        df_out = df_out.drop(['Column1','Phone','PayNow($)'],axis=1)
        df_out = df_out.drop_duplicates('Plan',keep='last')
        df_out = df_out.sort_values(['Provider'],ascending=[1])
        df_out = df_out.sort_values(['PerMonth($)'],ascending=[1])
        df_out = df_out.reset_index()
        df_out = df_out.drop(['index'],axis=1)
        return df_out

    # Choose by Telco to display all phone prices based on user's current telco and plan
    def function2(self,telco,plan):
        df_out = df_con[(df_con.loc[:,'Plan'] == plan) & (df_con.loc[:,'Provider'] == telco)]
        df_out = df_out.reset_index()
        df_out = df_out.drop(['Column1','index'],axis=1)
        return df_out


    def sendImage(self,chat_id):
        url = "https://api.telegram.org/bot" + TOKEN + "/sendPhoto";
        files = {'photo': open(outname, 'rb')}
        data = {'chat_id' : chat_id}
        requests.post(url, files=files, data=data)
        #r= requests.post(url, files=files, data=data)
        #print(r.status_code, r.reason, r.content)

    def convertImage(self,df,fn):
        with open(filename, 'w') as f:
                f.write(df.to_html()) 
        if(fn==0):
            imgkit.from_url(filename, outname ,options={'width':'512'}) #pass options values here
        elif(fn==1):
            imgkit.from_url(filename, outname ,options={'width':'620'}) #pass options values here
        elif(fn==2):
            imgkit.from_url(filename, outname ,options={'width':'768'}) #pass options values here

    ## Bot functions ##
    def on_chat_message(self,msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        #bot.sendMessage(chat_id,'Welcome to TelcoBot, it is my pleasure to serve you')

        if content_type == 'text':
                msg_text = msg['text']

        if (msg_text == '/start'):
            bot.sendMessage(chat_id, start)

        elif (msg_text == '/help'):
            bot.sendMessage(chat_id, 'To begin, type /request to start the bot. ')
                
        elif (msg_text == '/request'):  
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='Choose by Model', callback_data='Choose by Model')],
               [InlineKeyboardButton(text='Choose by Plan', callback_data='Choose by Plan')],
               [InlineKeyboardButton(text='Choose by Telco', callback_data='Choose by Telco')]
                   ])
            bot.sendMessage(chat_id, """How may I help you? \nBelow there are three options.
The first option will allow you to choose the phone model and prints out the prices of the phone model from various mobile plans.
The second option will allow you to choose your requirements for data and monthly subscription price and filter out all suitable plans.
The third option will allow you to choose what telco you want and sorts out all the phones price under the chosen telco and plan. """)
            bot.sendMessage(chat_id, 'Select an option:', reply_markup=keyboard)
                

    def on_callback_query(self,msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        print('Callback Query:', query_id, from_id, query_data)
        inline_message_id = msg['message']['chat']['id'], msg['message']['message_id']
        
        bot.editMessageReplyMarkup(inline_message_id, reply_markup=None)
        ## Choose by Model
        if (query_data == 'Choose by Model'):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text= phone, callback_data=phone)] for phone in phone_list
                   ])
            bot.sendMessage(from_id, 'Select a phone model: ', reply_markup=keyboard)
        if (query_data in phone_list):
            bot.sendMessage(from_id, query_data)
            self.convertImage(self.function0(query_data),0)
            self.sendImage(from_id)
            
        ##Choose by Plan goes here
        keyboard_price = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='Under 20', callback_data='price1')],
               [InlineKeyboardButton(text='$20 - $40', callback_data='price2')],
               [InlineKeyboardButton(text='$40 - $70', callback_data='price3')],
               [InlineKeyboardButton(text='$70 - $100', callback_data='price4')],
               [InlineKeyboardButton(text='Above $100', callback_data='price5')]
                   ])
        keyboard_data = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='0 - 1GB', callback_data='data1')],
               [InlineKeyboardButton(text='1 - 3GB', callback_data='data2')],
               [InlineKeyboardButton(text='3 - 5GB', callback_data='data3')],
               [InlineKeyboardButton(text='5 - 8GB', callback_data='data4')],
               [InlineKeyboardButton(text='Above 8GB', callback_data='data5')],
                   ])
        keyboard_plan = InlineKeyboardMarkup(inline_keyboard=[
               [InlineKeyboardButton(text='SIM Only', callback_data='SIM Only')],
               [InlineKeyboardButton(text='Contract', callback_data='Contract')],
                   ])
        if (query_data == 'Choose by Plan'):
            bot.sendMessage(from_id, 'Please choose your preference for mobile plan type: ', reply_markup=keyboard_plan)
            
        if (query_data == 'SIM Only' or query_data == 'Contract'):
            bot.sendMessage(from_id, query_data)
            bot.sendMessage(from_id, 'Please choose your preference for data: ', reply_markup=keyboard_data)
            self.plan_type = query_data

        if (query_data[:4] =='data'):
            if query_data[4] == '1':
                self.data_u, self.data_l = 1,0
            elif query_data[4] == '2':
                self.data_u, self.data_l = 3,1
            elif query_data[4] == '3':
                self.data_u, self.data_l = 5,3
            elif query_data[4] == '4':
                self.data_u, self.data_l = 8,5
            elif query_data[4] == '5':
                self.data_u, self.data_l = 25,8
            bot.sendMessage(from_id, 'Please choose your preference for price: ', reply_markup=keyboard_price)
            
        if (query_data[:5] == 'price'):
            if query_data[5] == '1':
                self.price_u,self.price_l = 20,0
            elif query_data[5] == '2':
                self.price_u,self.price_l = 40,20
            elif query_data[5] == '3':
                self.price_u,self.price_l = 70,40
            elif query_data[5] == '4':
                self.price_u,self.price_l = 100,70
            elif query_data[5] == '5':
                self.price_u,self.price_l = 300,100
            if (self.plan_type == 'SIM Only'):
                df_filtered = self.function1_sim(self.data_l,self.data_u,self.price_l,self.price_u)
            else:
                df_filtered = self.function1_con(self.data_l,self.data_u,self.price_l,self.price_u)
            
            if(df_filtered.empty):
                bot.sendMessage(from_id, 'No results were found')
            else:
                self.convertImage(df_filtered,1)
                self.sendImage(from_id)

        ##Choose by Telco
        if (query_data == 'Choose by Telco'):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text=telco, callback_data=telco)] for telco in telco_list
                   ])
            bot.sendMessage(from_id, 'Select a telco provider: ', reply_markup=keyboard)
            
        if (query_data in telco_list):
            self.telco = query_data
            plan_list_l = df_con[df_con.loc[:,'Provider'] == query_data]
            plan_list_l = plan_list_l.loc[:,'Plan'].unique()
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text=plan, callback_data=plan)] for plan in plan_list_l
                   ])
            bot.sendMessage(from_id, query_data)
            bot.sendMessage(from_id, 'Select a plan: ', reply_markup=keyboard)
            
        if(query_data in plan_list):
            bot.sendMessage(from_id, query_data)
            self.convertImage(self.function2(self.telco,query_data),2)
            self.sendImage(from_id)
        ##end     
        bot.answerCallbackQuery(query_id, text='Wait a moment...')

## bot delegator   
bot = DelegatorBot(TOKEN, [
    pave_event_space()
    (per_chat_id(), create_open, TelcoBot, timeout=100)
])
MessageLoop(bot).run_as_thread()

print ('Bot Started')

while 1:
    time.sleep(10)   
