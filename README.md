# Telcobot
**telcom.py** -
This script does the Webscrapping for M1 and Circles.life and stores all the data to the new excel file, telecom_demo.xlsx.

**telcobot.py** -
This is the main Telegram Bot script that runs and interacts with the user, when the bot is accessed via Telegram.
Replace the bot token 

**telecom_demo.xlsx** -
This excel file stores all the data scrapped from M1 and Circle.life, in 2 sheets - Contract and SIM only.

**telecom.xlsx** -
This is the same file as telecom_demo, except for the missing data from Singtel and Starhub, which was manually added.
This is the excel file that Telco Bot reads from, which is converted into a dataframe, allows us to answer any queries from our 3 features easily.

**out.jpg** -
Sample output of a query on Telegram. 
