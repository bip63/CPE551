# The source code used to build this project can be found here: https://github.com/vprusso/youtube_tutorials/tree/master/twitter_python
# Youtube video for demonstration: https://www.youtube.com/watch?v=cSus5A0yFFA&feature=youtu.be

from tweepy import API 
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob
 
import twitter_credentials
import numpy as np
import pandas as pd
import re
import matplotlib.pyplot as plt
import os

# # # # TWITTER CLIENT # # # #
class TwitterClient():
    def __init__(self, twitter_user = None): # Specified user's timeline. Default user is self
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client
        
    def get_user_timeline_tweets(self, num_tweets): 
        tweets = []
        # Can get certain number of tweets of specified user's timeline. If no user is specified, own timeline will be used
        for tweet in Cursor(self.twitter_client.user_timeline, id = self.twitter_user).items(num_tweets): 
            tweets.append(tweet)
        return tweets

# # # # TWITTER AUTHENTICATOR # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth


# # # # TWEET ANALYZER # # # #
class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets.
    """

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    #Sentiment Analysis
    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))

        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1
        
    def tweets_to_data_frame(self, tweets):
        # Creating a list where each object in list is the text of the tweet
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])

        # Adds additional information columns to data frame
        df['id'] = np.array([tweet.id for tweet in tweets])
        df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['source'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])
        
        return df

if __name__ == "__main__":

    #User inputs number of desired tweets to analyze
    numberOfTweets = int(input("How many tweets would you like to analyze?: "))

    #Created objects
    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()
    api = twitter_client.get_twitter_client_api()

    #Tweets extracted from @PlayVALORANT twitter timeline
    tweets = api.user_timeline(screen_name="PlayVALORANT", count = numberOfTweets)

    #Dataframe created to analyze collected tweets
    df = tweet_analyzer.tweets_to_data_frame(tweets)

    #Sentiment Column added to dataframe
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']])

    #Prints dataframe to a .csv file. Tests to see if file is already created
    filePath = os.path.isfile("Tweets_Dataframe.csv")
    if filePath == True:
        replaceFile = input("There is already a dataframe file created. Enter 'y' to replace or 'n' to create a new file: ")
        if replaceFile == 'y':
            os.remove("Tweets_Dataframe.csv")
            df.to_csv("Tweets_Dataframe.csv")
        else:
            fileName = input("Please specify new file name: ")
            while os.path.isfile(fileName + ".csv") == True:
                fileName = input("That filename is already taken. Please specify a different name: ")
                if os.path.isfile(fileName + ".csv") == False:
                    break
            df.to_csv(fileName + ".csv")
    else:
        df.to_csv("Tweets_Dataframe.csv")

    #Initializes variables
    negative = 0
    positive = 0
    neutral = 0
    polarity = []
    generalOpinion = 0
    sentiment = []
    numberOfLikes = []
    numberOfRetweets = []

    #Finds how many positive, neutral, and negative tweets there are in the dataframe
    for polarity in df['sentiment']:
        sentiment.append(polarity) #Creates a list of tweet polarity in order
        if polarity == 0:
            neutral += 1
        elif polarity == 1:
            positive += 1
        else:
            negative += 1

    #Creates a list of number of tweet likes in order
    for likes in df['likes']:
        numberOfLikes.append(likes)

    for retweets in df['retweets']:
        numberOfRetweets.append(retweets)

    """
    The value of a tweet (positive or negative) also depends on the number of likes/retweets it has.
    Retweets matter more than likes because it helps endorse content and the user retweeting must be excited to spread the message.
    The below calculation considers each like as 1 point and each retweet by 2 points. 
    """
    #Multiplies the polarity of the tweet by the number of likes and retweets and their value and adds them together to find an overall positive or negative opinion
    for counter in range(numberOfTweets):
        generalOpinion += (sentiment[counter] * (numberOfLikes[counter] + 2 * numberOfRetweets[counter]))

    #Consider each positive tweet as a 5 star rating, neutral tweet as a 3 star rating, and negative tweet as a 1 star rating
    starRating = ((positive * 5) + (neutral * 3) + (negative * 1)) / numberOfTweets
    print("The overall general opinion has a value of: %s " % str(generalOpinion))
    print("The average star rating of the game is: %s" % str(starRating))
    
    #Prints out the number of tweets for each polarity
    print("Number of positive tweets: %s" % str(positive))
    print("Number of neutral tweets: %s" % str(neutral))
    print("Number of negative tweets: %s" % str(negative))

    #Creates and displays a bar chart to visual polarity data
    barChart = pd.DataFrame({'Polarity':['Positive', 'Neutral', 'Negative'], 'Value':[positive, neutral, negative]})
    ax = barChart.plot.bar(x = 'Polarity', y = 'Value', rot = 0)
    plt.show()
