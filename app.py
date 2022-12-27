import tweepy
import requests
import random
import json
import os
import sys

def get_config():
    try:
        with open(os.path.join(sys.path[0], 'config.txt'), "r") as file:
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

auth_v1 = tweepy.OAuth1UserHandler(
   consumer_key, consumer_secret,
   access_token, access_token_secret
)
auth_v2 = {'bearer_token':bearer_token,'consumer_key':consumer_key,'consumer_secret':consumer_secret,'access_token':access_token,'access_token_secret':access_token_secret}
# --------- V1 -----------
# api = tweepy.API(auth_v1,wait_on_rate_limit=True)
# --------- V2 -----------
client = tweepy.Client(**auth_v2)


def get_dm_participants_v2(username):
    me = client.get_me().data
    contact = get_user_v2(username)
    return me,contact

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
    with open(f'output/dms_{contact.username}.json','w',encoding='utf8') as output_file:
            json.dump(data,output_file,indent=4,ensure_ascii=False)
    print("DMs file successfully generated")

def get_user_v2(username):
    return client.get_user(username=username).data

def get_all_pages_v2(request,params):
    data = []
    response = request(**params)
    data += response.data
    while 'next_token' in response.meta:
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
# tweet = input("What do you want to tweet ? ")
# api.update_status(status=tweet)

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

# ---------------------------------------------- TWEET LIKES ----------------------------------------------------------
# tweet_id = '1572793408565157889'
# request = client.get_liking_users
# params = {'id':tweet_id}
# liking_users_list = get_all_pages_v2(request,params)
# desired_username = "elonmusk"
# print(desired_username in [user.username for user in liking_users_list])

# ---------------------------------------------- DMs ----------------------------------------------------------
get_dms_v2(username="eltomstore",reverse=True)