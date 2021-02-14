#@crossedOak
#2/10/2021

import shodan
from bs4 import BeautifulSoup
import requests
import tweepy
import json
import getopt, sys
import sqlite3
import re

#get command line arguments
argumentList = sys.argv[1:]

options = "fh:"

long_options = ["file", "help"]

try:
	arguments, values = getopt.getopt(argumentList, options, long_options)
	for currentArgument, currentValue in arguments:
		
		if currentArgument in ("-f", "--file"):
			keyFile = sys.argv[2]
		
		elif currentArgument in ("-h", "--help"):
			print("################################################################## \n Use -f to specify the json file that has your shodan and twitter API keys. \n You need to specify a shodanKey, a Twitter consumerKey, \n consumerSecret, accessToken, and secretToken \n Or provide a .json file (-f [PATH]) with the keys \n listed in the with the same key:value as listed above \n################################################################## ")
			exit(0)

except getopt.error as err:
	print (str(err))

#retrieve keys and set values
with open(keyFile) as k:
	data = json.load(k)
	SHODAN_API_KEY = data['shodan']
	consumerKey = data['consumerKey']
	consumerSecret = data['consumerSecret']
	accessToken = data['accessToken']
	secretToken = data['secretToken']

#Shodan API interaction
api = shodan.Shodan(SHODAN_API_KEY)

try:
 	#searching
	results = api.search('thrane port:10000')
	totalSearch1 = '{}'.format(results['total'])


except shodan.APIError as e:
		print ('Error: {}'.format(e))

outputList = []
#soupy things
for result in results['matches']:
	IPlist = result['ip_str']
	page = BeautifulSoup(requests.get('http://' + IPlist + ':10000').text, "html.parser")
	rawTitle = page.find(id="status_hostname").text
	title = rawTitle.split(" - ")[0]
	outputList.append(rawTitle + ' - ' + result['ip_str'] + '\nSeen: ' + result['timestamp'] + '\n')
	
#Shodan search 2
unitList = []
titleList = []
shipIPList = []
shipTimestampList = []
try:
	results = api.search('title:"SAILOR" port:8080')
	totalSearch2 = '{}'.format(results['total'])
except shodan.APIError as e:
		print ('Error: {}'.format(e))
for result in results['matches']:
	IPlist = result['ip_str']
	try:
		page = BeautifulSoup(requests.get('http://' + IPlist + ':8080').text, "html.parser")
		rawTitle = page.find(id="status_hostname").text
		title = rawTitle.split(" - ")[0]
		unit = rawTitle.split(" - ")[1]
		outputList.append(rawTitle + ' - ' + result['ip_str'] + '\nSeen: ' + result['timestamp'] + '.\n')
		unitList.append(unit)
		titleList.append(title)
		shipIPList.append(IPlist)
		shipTimestampList.append(result['timestamp'])
	except:
		print ('Error connecting to host: {}'.format(result['ip_str']))


#Shodan search 3
try:
	fleetBroadbandListIP = []
	fleetBroadbandListTimestamp = []
	results = api.search('title:"Thrane &amp;"')
	totalFleetBroadband = '{}'.format(results['total'])
	for result in results['matches']:
		fleetBroadbandListIP.append(result['ip_str'])
		fleetBroadbandListTimestamp.append(result['timestamp'])
	
		
		
except shodan.APIError as e:
		print ('Error: {}'.format(e))

aptusWebListIP = []
aptusWebListTimestamp = []
try:
 	#searching
	results = api.search('title:"Intellian Aptus Web"')
	totalAptusWeb = '{}'.format(results['total'])
	for result in results['matches']:
		aptusWebListIP.append(result['ip_str'])
		aptusWebListTimestamp.append(result['timestamp'])

except shodan.APIError as e:
		print ('Error: {}'.format(e))
print(aptusWebListIP)

#refine the list
refinedoutputList = list(set(outputList))

#database things start here
def create_connection(db_file):
    conn = None
    print(db_file)
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
        return conn
    except Error as e:
    	print("made it to the error of create connection " + str(e))
    return conn


def create_table(conn, create_table_sql):
	try:
		c = conn.cursor()
		c.execute(create_table_sql)
	except Error as e:
		print(e)

def create_fleetBroadband(conn, FleetBroadband):
	sql = '''INSERT OR IGNORE INTO FleetBroadband(id,ip,timestamp)
			 VALUES(?,?,?) '''
	cur = conn.cursor()
	cur.execute(sql, FleetBroadband)
	conn.commit()
	return cur.lastrowid

def create_Ships(conn, ship):
	sql = '''INSERT OR IGNORE INTO ships(id,ip,unit,name,timestamp)
			 VALUES(?,?,?,?,?) '''
	cur = conn.cursor()
	cur.execute(sql, ship)
	conn.commit()
	return cur.lastrowid

def create_AptusWeb(conn, AptusWeb):
	sql = '''INSERT OR IGNORE INTO AptusWeb(id,ip,timestamp)
			 VALUES(?,?,?) '''
	cur = conn.cursor()
	cur.execute(sql, AptusWeb)
	conn.commit()
	return cur.lastrowid


def main():
	database = r"/root/Documents/shipdan/shipdan.db"

	sql_create_ships_table = """ CREATE TABLE IF NOT EXISTS ships (
									id int,
									ip text PRIMARY KEY,
									unit text,
									name text NOT NULL,
									timestamp text
									); """

	sql_create_FleetBroadband = """CREATE TABLE IF NOT EXISTS FleetBroadband (
									id int,
									ip text PRIMARY KEY,
									timestamp text
									); """
	sql_create_AptusWeb = """CREATE TABLE IF NOT EXISTS AptusWeb (
									id int,
									ip text PRIMARY KEY,
									timestamp text
									); """

	conn = create_connection(database)

	if conn is not None:
		create_table(conn, sql_create_ships_table)
		create_table(conn, sql_create_FleetBroadband)
		create_table(conn, sql_create_AptusWeb)
	else:
		print("error! cannot create the database connection")

	with conn:
		count = 0
		for item, item2 in list(zip(fleetBroadbandListIP, fleetBroadbandListTimestamp)):
			count += 1
			fleetBroadband = (count, item, item2)
			fleetBroadband_id = create_fleetBroadband(conn, fleetBroadband)
		for item, item2, item3, item4 in list(zip(shipIPList, unitList, titleList, shipTimestampList)):
			count += 1
			ships = (count, item, item2, item3, item4)
			ships_id = create_Ships(conn, ships)
		for item, item2 in list(zip(aptusWebListIP, aptusWebListTimestamp)):
			count += 1
			aptusWeb = (count, item, item2)
			aptusWeb_id = create_AptusWeb(conn, aptusWeb)

if __name__ == '__main__':
	main()



'''
#auth to twitter
auth = tweepy.OAuthHandler(consumerKey,  consumerSecret)
auth.set_access_token(accessToken, secretToken)
api = tweepy.API(auth)
try:
	api.verify_credentials()
	print("Authenticated \n")
except:
	print("Authentication Failed \n")

#Verify contents to tweet
total = int(totalFleetBroadband) + int(totalAptusWeb) + int(totalSearch1) + int(totalSearch2)
tweetHeader = str(total) + " vessel terminals found on Shodan. \n" + totalFleetBroadband + " Thrane Fleet Broadband\n" + totalAptusWeb + " Intellian AptusWeb portals\n" 
print( tweetHeader + '\n' + '\n'.join([str(i) for i in refinedoutputList]))

userChoice = input('\nIs this what you want to tweet? (Y/N): ')
if userChoice.lower() == 'y' or userChoice.lower() == 'yes': 
	#api.update_status(tweetHeader + '\n' + '\n'.join([str(i) for i in refinedoutputList]))
	#split if needed
	completeTweet = tweetHeader + '\n' + '\n'.join([str(i) for i in refinedoutputList])
	preTweet = ""
	tweet_list = []
	text_list = re.split(r'(\.)', completeTweet)

	for word in text_list:
		if len(preTweet + word) > 137:
			tweet_list.append(preTweet)
			preTweet = word
		else:
			preTweet = preTweet + word
	tweet_list.append(preTweet)
	for post in tweet_list:
		#api.update_status(post)
		print("Tweeted Successfully")
	
	
elif userChoice.lower() == 'n' or userChoice.lower() == 'no':
	print("No tweet created. Check inputs.")
	exit(0)
else: 
	print("Invalid choice, exiting")
	exit(0)
'''



