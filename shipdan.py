#@crossedOak
#2/10/2021

import shodan
from bs4 import BeautifulSoup
import requests
import tweepy
import json
import getopt, sys


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
	
#auth to twitter
auth = tweepy.OAuthHandler(consumerKey,  consumerSecret)
auth.set_access_token(accessToken, secretToken)
api = tweepy.API(auth)
try:
	api.verify_credentials()
	print("Authenticated")
	total = '{}'.format(results['total'])
	tweetHeader = total + " ship SATCOM terminals found on Shodan. \n"
	print( tweetHeader + '\n' + '\n'.join([str(i) for i in outputList]))
	api.update_status(tweetHeader + '\n' + '\n'.join([str(i) for i in outputList]))
	print("Tweeted successfully")
except:
	print("Authentication Failed")