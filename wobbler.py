import time
import sys
import logging
from requests_oauthlib import OAuth1Session
import json
import requests
import pylast
import tweepy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Twitter and Last.fm auth functions are brought to you by
# pylast / Tweepy documentation , StackOverflow and GitHub Copilot
# PRs are more than welcome!

def getTwitterKeys():
    
    # This function gets the access tokens for Twitter
    
    consumer_key = json.load(open("keys.json"))["twitter-consumer_key"]
    consumer_secret = json.load(open("keys.json"))["twitter-consumer_secret"]
    request_token_url = "https://api.twitter.com/oauth/request_token"
    
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)
    fetch_response = oauth.fetch_request_token(request_token_url)
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')
    
    base_authorization_url = 'https://api.twitter.com/oauth/authorize'
    authorization_url = oauth.authorization_url(base_authorization_url)
    print('Please go here and authorize,', authorization_url)
    
    verifier = input('Paste the PIN here: ')
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    
    oauth = OAuth1Session(consumer_key,
                            client_secret=consumer_secret,  
                            resource_owner_key=resource_owner_key,
                            resource_owner_secret=resource_owner_secret,
                            verifier=verifier)
    
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    #print the keys instead of saving them
    print("Token:",oauth_tokens["oauth_token"])
    print("Secret:",oauth_tokens["oauth_token_secret"])

def doAuth():
    
    # This function does the auth for both Twitter and Last.fm
    
    keyFile = open("keys.json")
    keys = json.load(keyFile)

    API_KEY = keys['lastfm-API_KEY']
    API_SECRET = keys['lastfm-API_SECRET']

    username = keys['lastfm-username']
    password_hash = pylast.md5(keys['lastfm-password'])

    network = pylast.LastFMNetwork(
        api_key=API_KEY,
        api_secret=API_SECRET,
        username=username,
        password_hash=password_hash,
    )

    global user 
    user = network.get_user(username)
    print("LastFM Authenticated!")

    auth = tweepy.OAuthHandler(keys['twitter-consumer_key'] , keys['twitter-consumer_secret'])
    auth.set_access_token(keys['twitter-access_token'] , keys['twitter-access_token_secret'])

    global api
    api = tweepy.API(auth, wait_on_rate_limit=True)

    try:
        api.verify_credentials()
    except Exception as e:
        logger.error("Error creating API", exc_info=True)
        raise e
    logger.info("Twitter API initated :P")

# check if keys.json has Twitter access tokens, if not, use terminal oauth
if "twitter-access_token" not in json.load(open("keys.json")):
    getTwitterKeys()
    exit()
doAuth()


def postCurrentStatus(api, user):
    
    # cache the latest scrobble
    # unfortunately this makes us lose the first scrobble from every startup
    cachedScrobble = user.get_recent_tracks(limit=1)[0]
    cachedScrobbleTime = cachedScrobble.timestamp
    cachedScrobbleTime = int(cachedScrobbleTime)
    
    # wait 10 seconds
    time.sleep(10)
    
    # get the latest scrobble
    latestScrobble = user.get_recent_tracks(limit=1)[0]
    latestScrobbleTime = latestScrobble.timestamp
    latestScrobbleTime = int(latestScrobbleTime)
    sessionAlive = False
    
    # this code does the following:
    # if user != listening && sessionAlive == True, post status & sessionAlive = False
    # if user == listening, post status & sessionAlive = True
    if ((user.get_now_playing() == None) & (sessionAlive == True)):
        sessionAlive = False
        songName = latestScrobble.track.title
        songArtist = latestScrobble.track.artist.name
        status = "\"" + songName + "\"" + "\nby " + songArtist + "\nat UNIX_time=[" + str(latestScrobbleTime) + "]"
        api.update_status(status)
        logger.info("Posted current song!") 
    else:
        if (latestScrobbleTime != cachedScrobbleTime):
            sessionAlive = True
            songName = latestScrobble.track.title
            songArtist = latestScrobble.track.artist.name
            status = "\"" + songName + "\"" + "\nby " + songArtist + "\nat UNIX_time=[" + str(latestScrobbleTime) + "]"
            api.update_status(status)
            logger.info("Posted current song!") 

    postCurrentStatus(api, user) # mfw infinite recursion

postCurrentStatus(api, user)