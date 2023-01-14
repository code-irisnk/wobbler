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


def get_oauth():
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

    # save the access key and secret to keys.json
    #keys = json.load(open("keys.json"))
    #keys["twitter-access_token"] = oauth_tokens["oauth_token"]
    #keys["twitter-access_token_secret"] = oauth_tokens["oauth_token_secret"]
    #json.dump(keys, open("keys.json", "w"))
    #print the keys instead of saving them
    print("Token:",oauth_tokens["oauth_token"])
    print("Secret:",oauth_tokens["oauth_token_secret"])


def doAuth():
    keyfile = open("keys.json")
    keys = json.load(keyfile)

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

## check if keys.json has access tokens
if "twitter-access_token" not in json.load(open("keys.json")):
    get_oauth()
    exit()
doAuth()


def postCurrentStatus(api, user):
    # get the last scrobble
    lastScrobble = user.get_recent_tracks(limit=1)[0]
    lastScrobbleTime = lastScrobble.timestamp
    lastScrobbleTime = int(lastScrobbleTime)
    # wait 10 seconds

    time.sleep(10)
    # get the current scrobble
    currentScrobble = user.get_recent_tracks(limit=1)[0]
    currentScrobbleTime = currentScrobble.timestamp
    currentScrobbleTime = int(currentScrobbleTime)
    # if the current scrobble is not the same as the last scrobble, post the current song
    if currentScrobbleTime != lastScrobbleTime:
        songName = currentScrobble.track.title
        songArtist = currentScrobble.track.artist.name
        songUnix = currentScrobbleTime
        status = "\"" + songName + "\"" + "\nby " + songArtist + "\nat UNIX_time=[" + str(songUnix) + "]"
        api.update_status(status)
        logger.info("Posted current song!")
    postCurrentStatus(api, user)
postCurrentStatus(api, user)