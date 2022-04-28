import time
import sys
import logging
import json
import pylast
import tweepy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)


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

doAuth()


def postCurrentStatus(api, user):

    a = 0
    song = user.get_now_playing()

    def postTheDamnThing(api, user):

        currentUNIX=int(time.time())

        song = user.get_now_playing()
        song2 = (str(song) + '.')[:-1]

        stuffToJoin = [song2, "\n","at UNIX_time=[", str(currentUNIX),"]"]
        song3 = "".join(stuffToJoin)

        statusToPost = song3
        
        api.update_status(status=statusToPost)
        logger.info("Posted current song!")

        postCurrentStatus(api, user)

    while a < 90:
        time.sleep(1)
        a = a + 1
    

    else:
        
        if song != None:
            logger.info("Waited ", a ," seconds.")
            postTheDamnThing(api, user)
            postCurrentStatus(api, user)
        
        else:
            logger.info("Restarting Countdown.")
            logger.info("Waited ", a ," seconds.")
            postCurrentStatus(api, user)

postCurrentStatus(api=api, user=user)
