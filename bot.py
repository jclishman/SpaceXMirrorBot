from bot_logging import logger
import requests
import tweepy
import json
import praw
import time
import re

# Secret credentials :)
credentials = json.load(open('_config.json'))

# Reddit API Authentication
reddit_api = praw.Reddit(
    client_id=credentials["reddit_id"], 
    client_secret=credentials["reddit_secret"], 
    username='SpaceXMirrorBot', 
    password=credentials['reddit_password'], 
    user_agent = "SpaceX Mirror Bot by u/jclishman"
)

# Tweepy API Authentication
auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
auth.set_access_token(credentials["access_token"], credentials["access_secret"])
twitter_api = tweepy.API(auth)

# Imgur API Authentication
imgur_auth_data = {'Authorization': f"Client-ID {credentials['imgur_client_id']}"}
imgur_upload_url = "https://api.imgur.com/3/image"


# Twitter Status ID Regex
# Matches the numeric ID from a tweet URL
status_regex = re.compile('status\/(\d+)')

subreddits = [reddit_api.subreddit('SpaceX'), reddit_api.subreddit('SpaceXLounge')]

# Individual "last post" times for both subreddits
last_post_time = {
    subreddits[0]: time.time(),
    subreddits[1]: time.time()
}

def get_twitter_fullres(tweet_url):

    # RegEx's the status URL for the numeric status ID
    tweet_id = status_regex.search(tweet_url).group(1)

    # Get the status JSON from Twitter
    tweet_data = twitter_api.get_status(tweet_id, include_entities=True, tweet_mode='extended')
    tweet = tweet_data._json

    twitter_url_list = []

    try:

        # Check if the tweet has media attached
        for tweet_media in tweet["extended_entities"]["media"]:

            if tweet_media["type"] == "photo":

                # Appends ":orig" to URL for max resolution
                twitter_url_list.append(tweet_media["media_url_https"]+":orig")

            else:
                logger.info("Media attached is not a picture")
                return -1

        return twitter_url_list

    except:
        logger.info("Tweet has no media attached")
        return -1

        
def upload_to_imgur(url_list):


    imgur_url_list = []

    for url in url_list:


        # Uploads image to Imgur and adds the link to a list
        upload = requests.post(imgur_upload_url, headers=imgur_auth_data, data=url)
        upload_link = upload.json()["data"]["link"]
        
        imgur_url_list.append(upload_link)
        time.sleep(1)

    return imgur_url_list


def comment_on_thread(submission, twitter_url_list, imgur_url_list):

    # Assembles the comment
    thread_comment = "**Max Resolution Twitter Link(s)**\n\n"

    for twitter_url in twitter_url_list:
        thread_comment += (f"{twitter_url}\n\n")

    thread_comment += "**Imgur Mirror Link(s)**\n\n"

    for imgur_url in imgur_url_list:
        thread_comment += (f"{imgur_url}\n\n")

    thread_comment += "---\n\n^The ^bot ^is ^back! ^Apologies ^for ^the ^downtime."
    thread_comment += "\n\n^^I'm ^^a ^^bot ^^made ^^by ^^[u\/jclishman](https://reddit.com/user/jclishman)!"
    thread_comment += " [^^[Code]](https://github.com/jclishman/SpaceXMirrorBot)"

    # Posts the comment
    retries = 0
    while retries < 5:

        try:
            thread_comment_id = submission.reply(thread_comment)
            logger.info(f"Comment made with ID: {thread_comment_id}")

            # Break from the while loop after successful post submission
            break

        except praw.exceptions.APIException as e:
            retries += 1
            logger.error(f"Hit ratelimit, will try again in 5 minutes. (Attempt {retries}/5)")
            time.sleep(300)

while True:

    try:

        for subreddit in subreddits:
            logger.info("Checked subreddit")

            # Find the most recent submission
            for submission in subreddit.new(limit=1):

                post_time = submission.created_utc

                # Is it new?
                if post_time > last_post_time[subreddit]:

                    last_post_time[subreddit] = post_time

                    # Ignore if it's not a link post
                    if submission.is_self:
                        #logger.info("Not a link post")
                        pass

                    # Check if it's a link to Twitter
                    elif "twitter.com" in submission.url:

                        logger.info("="*30)
                        logger.info(f"Found a tweet post ({submission.shortlink})")
                        #logger.info(submission.url)

                        twitter_url_list = get_twitter_fullres(submission.url)

                        # get_twitter_fullres() returns -1 if the tweet has no/incorrect media type
                        if twitter_url_list != -1:

                            logger.info("Uploading to imgur")
                            imgur_url_list = upload_to_imgur(twitter_url_list)

                            logger.info("Max Res Twitter URLs: ")
                            logger.info(twitter_url_list)
                            logger.info("Mirror Imgur URLs: ")
                            logger.info(imgur_url_list)

                            comment_on_thread(submission, twitter_url_list, imgur_url_list)

                    # Ignore if it's a link to anywhere else
                    else:
                        #logger.info("Not a tweet")
                        pass

            time.sleep(4)

    except Exception as e:
        logger.error(str(e))
