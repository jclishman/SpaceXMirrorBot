from imgurpython import ImgurClient
from bot_logging import logger
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
imgur_api = ImgurClient(credentials["imgur_client_id"], credentials["imgur_client_secret"])

# Twitter Status ID Regex
# Matches the numeric ID from a tweet URL
status_regex = re.compile('(\d+)(?:\/?)$')

subreddits = [reddit_api.subreddit('jclishmantest'), reddit_api.subreddit('test')]
last_post_time = time.time()


def get_twitter_fullres(tweet_url):

    # RegEx's the status URL for the numeric status ID
    tweet_id = status_regex.search(tweet_url)

    # Get the status JSON from Twitter
    tweet_data = twitter_api.get_status(tweet_id.group(1), include_entities=True, tweet_mode='extended')
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

        return twitter_url_list

    except:
        logger.info("Tweet has no media attached")

        
def upload_to_imgur(url_list):

    imgur_url_list = []

    for url in url_list:

        # Uploads image to Imgur and adds the link to a list
        image = imgur_api.upload_from_url(url, anon=True)
        logger.info("Uploaded to Imgur with ID: %s" % image["id"])
        imgur_url_list.append(image["link"])
        time.sleep(1)

    return imgur_url_list


def comment_on_thread(submission, twitter_url_list, imgur_url_list):

    # Assembles the comment
    thread_comment = "**Max Resolution Twitter Link(s)**\n\n"

    for twitter_url in twitter_url_list:
        thread_comment += ("%s\n\n" % twitter_url)

    thread_comment += "**Imgur Mirror Link(s)**\n\n"

    for imgur_url in imgur_url_list:
        thread_comment += ("%s\n\n" % imgur_url)

    thread_comment += "---\n\n^^I'm ^^a ^^bot ^^made ^^by ^^[u\/jclishman](https://reddit.com/user/jclishman)!"
    thread_comment += " [^^[FAQ/Discussion]](http://reddit.com/user/SpaceXMirrorBot/comments/ad36dr/)  [^^[Code]](https://github.com/jclihman/SpaceXMirrorBot)"

    # Posts the comment
    retries = 0
    while retries < 5:

        try:
            thread_comment_id = submission.reply(thread_comment)
            logger.info("Comment made with ID: %s" % thread_comment_id)

            # Break from the while loop after successful post submission
            break

        except praw.exceptions.APIException as e:
            retries += 1
            logger.error("Hit ratelimit, will try again in 5 minutes. (Attempt %d/5)" % retries)
            time.sleep(300)

while True:

    try:

        for subreddit in subreddits:

            # Find the most recent submission
            for submission in subreddit.new(limit=1):

                post_time = submission.created_utc

                # Is it new?
                if post_time > last_post_time:

                    last_post_time = post_time

                    # Ignore if it's not a link post
                    if submission.is_self:
                        #logger.info("Not a link post")
                        pass

                    # Check if it's a link to Twitter
                    elif "twitter.com" in submission.url:
                        logger.info("Found a tweet post (%s)" % submission.shortlink,)
                        #logger.info(submission.url)

                        twitter_url_list = get_twitter_fullres(submission.url)
                        imgur_url_list = upload_to_imgur(twitter_url_list)

                        logger.info("Max Res Twitter URLs: ")
                        logger.info(twitter_url_list)
                        logger.info("Mirror Imgur URLs: ")
                        logger.info(imgur_url_list)

                        comment_on_thread(submission, twitter_url_list, imgur_url_list)

                    # Ignore if it's a link to anywhere else
                    else:
                        pass
                        #logger.info("Not a tweet")


            time.sleep(4)

    except Exception as e:
        logger.error(str(e))
