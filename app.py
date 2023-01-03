import tweepy
import requests
import random
import json
import os
import sys
import time
import openai
import numpy as np

def get_config():
    try:
        with open(os.path.join(sys.path[0], 'n_config.txt'), "r") as file:
            rows = ( line.strip().split('=') for line in file)
            dict = { row[0]:row[1] for row in rows }
            return dict
    except Exception as e:
        return None

api_config = get_config()
consumer_key = api_config['CONSUMER_KEY']
consumer_secret = api_config['CONSUMER_SECRET']
access_token = api_config['ACCESS_TOKEN']
access_token_secret = api_config['ACCESS_TOKEN_SECRET']
bearer_token = api_config['BEARER_TOKEN']
openai.api_key = api_config['OPENAI_API_KEY']

auth_v1 = tweepy.OAuth1UserHandler(
   consumer_key, consumer_secret,
   access_token, access_token_secret
)
auth_v2 = {'bearer_token':bearer_token,'consumer_key':consumer_key,'consumer_secret':consumer_secret,'access_token':access_token,'access_token_secret':access_token_secret,'wait_on_rate_limit':True}
# --------- V1 -----------
# api = tweepy.API(auth_v1,wait_on_rate_limit=True)
# --------- V2 -----------
client = tweepy.Client(**auth_v2)

def get_list_chunks(complete_list, chunk_size=3):
    return [list(chunk) for chunk in np.array_split(complete_list,len(complete_list)//chunk_size+1)]

# def classify_tweet_sentiment(tweet):
#     response = openai.Completion.create(
#         engine="text-davinci-002",
#         prompt=f"What is the sentiment (positive, negative or neutral) of the following tweet: {tweet}. Just tell me the sentiment in one word without any whitespace or line-break.",
#         temperature=0.5,
#         max_tokens=1024,
#         top_p=1,
#         frequency_penalty=0,
#         presence_penalty=0
#     )

#     sentiment = response["choices"][0]["text"]
#     return sentiment.strip().lower()



# def calculate_tweets_negativity_percentage(tweets):
#     negative_tweets = []
#     for tweet in tweets:
#         sentiment = classify_tweet_sentiment(tweet)=='negative'
#         if sentiment == 'negative':
#             negative_tweets.append(sentiment)
#         time.sleep(1)
#     negativity = len([tweet for tweet in tweets if classify_tweet_sentiment(tweet)=='negative'])/len(tweets)
#     return negativity

def classify_tweets_sentiment(tweets):
    tweets_prompt='\n'.join([f'{idx+1}. {tweet}' for idx,tweet in enumerate(tweets)])
    print(tweets_prompt)
    response = openai.Completion.create(
        engine="text-davinci-002",
        # prompt=f"What is the sentiment (positive, negative or neutral) of each of the following tweets:\n {tweets_prompt}. \nShow the sentiments in a numbered list and in lowercase.",
        prompt=f"Classify the sentiment in these tweets (positive, negative or neutral) in lowercase:\n\n{tweets_prompt}\n\nTweet sentiment ratings:",
        temperature=0,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print(response)
    sentiments = [sentiment.split()[-1].lower() for sentiment in response["choices"][0]["text"].strip().split('\n')]
    return sentiments

def calculate_negativity_percentage(sentiments):
    negativity = sentiments.count('negative')/len(sentiments)
    return negativity

def get_dm_participants_v2(username):
    me = client.get_me().data
    contact = get_user_v2(username)
    return me,contact

def get_users_followings(user_id):
    followings = [{'id':user.id, 'username':user.username} for user in tweepy.Paginator(client.get_users_following, user_id, max_results=1000,limit=5).flatten(limit=5000)]
    # save_data_to_json(followings,'followings')
    return followings
        
def get_dm_conversations():
    me = client.get_me().data
    # my_followings = get_users_followings(me.id)
    my_followings = get_json_data('output/followings.json')
    dm_contacts = []
    for user in my_followings:
        conversation = client.get_direct_message_events(participant_id=user['id'], max_results=1).data
        time.sleep(1)
        if conversation:
            dm_contacts.append({'id':user['id'], 'username':user['username']})
            save_data_to_json(dm_contacts,'conversations')
    return dm_contacts

def save_data_to_json(data,filename):
    with open(f'output/{filename}.json','w',encoding='utf8') as output_file:
        json.dump(data,output_file,indent=4,ensure_ascii=False)
    print(f"File {filename}.json successfully generated")

def get_json_data(file_path):
    with open(file_path, 'r',encoding='utf8') as f:
        data = json.load(f)
        return data

def get_dms_v2(username,reverse=False):
    # Params: username
    # Returns: Generates json file containing all dms with the specified contact,in reverse chronological order
    me,contact = get_dm_participants_v2(username)
    participants = {me.id:me.username,contact.id:contact.username}
    request = client.get_direct_message_events
    params = {'participant_id': contact.id, 'expansions':'sender_id', 'dm_event_fields':'created_at'}
    dms = get_all_pages_v2(request,params)
    data = [{"sender":participants[dm.sender_id],"text":dm.text,"date":dm.created_at.strftime('%Y-%m-%d %H:%M:%S')} for dm in dms]
    if reverse:
        data = list(reversed(data))
    save_data_to_json(data,f'dms_{contact.username}')
    # with open(f'output/dms_{contact.username}.json','w',encoding='utf8') as output_file:
    #         json.dump(data,output_file,indent=4,ensure_ascii=False)
    # print("DMs file successfully generated")

def get_latest_dms(reverse=False):
    me = client.get_me().data
    dms_data = client.get_direct_message_events(expansions=['sender_id'],dm_event_fields=['created_at']).data
    dms = []
    for dm in dms_data:
        if dm.sender_id == me.id:
            username = me.username
        else:
            username = client.get_user(id=dm.sender_id).data.username
        dms.append(f"{username}: {dm.text} --- {dm.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if reverse:
        return list(reversed(dms))
    return dms

def get_tweet_likers(tweet_id):
    request = client.get_liking_users
    params = {'id':tweet_id}
    likers_list = get_all_pages_v2(request,params)
    return likers_list

def get_tweet_retweeters(tweet_id):
    request = client.get_retweeters
    params = {'id':tweet_id}
    retweeters_list = get_all_pages_v2(request,params)
    return retweeters_list

def did_user_like_tweet(username,tweet_id):
    likers = get_tweet_likers(tweet_id)
    return username in [user.username for user in likers]

def did_user_retweet_tweet(username,tweet_id):
    retweeters = get_tweet_retweeters(tweet_id)
    return username in [user.username for user in retweeters]

def get_user_v2(username):
    return client.get_user(username=username).data

def calculate_tweet_sauce_probability(tweet_id):
    tweet = client.get_tweet(tweet_id,tweet_fields=['public_metrics','author_id']).data
    like_count = tweet.public_metrics['like_count']
    quote_count = tweet.public_metrics['quote_count']
    quotes = [tweet.text.replace(tweet.text.split()[-1],'').rstrip() for tweet in tweepy.Paginator(client.get_quote_tweets, tweet_id, max_results=100,limit=5).flatten(limit=5000)]
    quotes_chunks = get_list_chunks(quotes,5)
    sentiments = []
    for chunk in quotes_chunks:
        sentiments+=classify_tweets_sentiment(chunk)
    probability = calculate_negativity_percentage(sentiments)
    quote_like_ratio = quote_count/like_count if like_count>0 else quote_count/1
    if probability>0.5 and quote_count>10 and quote_like_ratio>2:
        probability+=(quote_like_ratio//2)*0.1
    return min(probability,1.0)

def get_all_pages_v2(request,params):
    data = []
    response = request(**params)
    data += response.data
    while 'next_token' in response.meta:
        time.sleep(1)
        response = request(**params,pagination_token=response.meta['next_token'])
        if response.data:
            data += response.data
    return data

# ------------------- USER INFO ---------------------------
# url = "https://twitter.com/Ngoneiih"
# screen_name = url.split("/")[-1]
# response = api.get_user(screen_name=screen_name)
# response_json = response._json
# fields = {"id":"id","screen_name":"username","name":"display_name","profile_location":"location", "description":"description"}
# user_info = {fields[key]:value for key,value in response_json.items() if key in fields}
# print(user_info)

# ------------------- TWEET ---------------------------
# me = client.get_me().data
# print([twt.text for twt in client.get_users_tweets(id=me.id).data])

# ------------------- API V2 --------------------------
# client = tweepy.Client(bearer_token=bearer_token,consumer_key=consumer_key,consumer_secret=consumer_secret,access_token=access_key,access_token_secret=access_secret)

# r= requests.get("https://type.fit/api/quotes")
# r_dict = r.json()
# l_quotes = [quote for quote in r_dict if 'love' in quote['text'].lower()]
# random_l_quote = random.choice(l_quotes)
# quote_text = random_l_quote['text']
# quote_author = random_l_quote['author']
# client.create_tweet(text=f"`{quote_text}` ~ {quote_author}")

# ---------------------------------------------- CREATE THREAD ----------------------------------------------------------
# thread = ['Ferrars all spirits his imagine effects amongst neither. It bachelor cheerful of mistaken. Tore has sons put upon wife use bred seen.', 'Its dissimilar invitation ten has discretion unreserved.']
# last_t = None
# for tweet in thread:
#     if not last_t:
#         response = client.create_tweet(text=tweet)
#     else:
#         response = client.create_tweet(text=tweet,in_reply_to_tweet_id=last_t)
#     last_t = response.data['id']

# ---------------------------------------------- TWEET LIKES & RTs ----------------------------------------------------------
tweet_id = '1572793408565157889'
# print(did_user_retweet_tweet('suzzz__',tweet_id))
# print(get_tweet_retweeters(tweet_id))

# ---------------------------------------------- DMs ----------------------------------------------------------
# get_dms_v2(username="polonium38",reverse=True)
# print(*get_latest_dms(reverse=True),sep='\n')
# me = client.get_me().data
# ---------------------------------------------- SAUCE ----------------------------------------------------------
sauced_tweet_id = '1608425890828161025'
# print(calculate_tweet_sauce_probability('1608425890828161025'))
test_tweets = ["I can't stand homework","This sucks. I'm bored 😠","I can't wait for Halloween!!!","My cat is adorable ❤️❤️"
,"I hate chocolate","I love my wife."]
# classify_tweets_sentiment(test_tweets)
# for tweet in test_tweets:
#     print(classify_tweet_sentiment(tweet))
print(calculate_tweet_sauce_probability(sauced_tweet_id))