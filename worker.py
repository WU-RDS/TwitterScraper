import json, time
from TwitterAPI import TwitterAPI, TwitterPager
from asyncio import Lock

from multiprocessing import Process

# this module should keep track of that in
workers_count = 0


def download_tweets_for_day(api, msg_dct):
    query = msg_dct['query']
    start = msg_dct['start']
    end = msg_dct['end']
    save_as = msg_dct['save_as']

    # print(save_as)
    # print(end)
    # print(query)
    r = TwitterPager(api, 'tweets/search/all', {
        'query': query,
        'max_results': 100,
        'start_time': start,
        'end_time': end,

        'expansions': 'attachments.media_keys,author_id,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id',
        'tweet.fields': 'public_metrics,reply_settings,source,text,id,author_id,entities,created_at,attachments,context_annotations,lang,possibly_sensitive,withheld,conversation_id,geo,in_reply_to_user_id,referenced_tweets',
        'user.fields': 'created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,username,verified,withheld',
        'place.fields': 'contained_within,country,country_code,full_name,geo,id,name,place_type',
    }, hydrate_type=2)

    with open(f'{save_as}_res.jsonl', 'w') as of:
        for i, item in enumerate(r.get_iterator(wait=5)):
            if 'text' in item:
                of.write(json.dumps(item) + '\n')
                of.flush()

            elif 'message' in item and item['code'] == 88:
                print('rate limit')
                time.sleep(10)

    ## store query information
    with open(f'{save_as[:-10]}req.jsonl', 'a') as of:
        json.dump(r.params, of)


def start_worker(qu, consumer_key, consumer_secret):
    q, counter = qu
    global workers_count
    workers_count += 1
    print(f'starting worker with {workers_count}')

    # consumer_key = 'pNJRnQ12vRHBZYj0HQlB5aEBC'
    # consumer_secret = 'fG2M11dNyYxNhcbzztVyr9T8Z3YG3yOF0iEuJrAFbfvDbCtTTz'
    api = TwitterAPI(consumer_key, consumer_secret, auth_type='oAuth2', api_version='2')

    while True:
        print('before received')

        msg_dct = q.get()
        print('received')
        download_tweets_for_day(api, msg_dct)
        time.sleep(7)
        print(" [x] Worked off this day: " + msg_dct['start'])
        counter.decrement()


def dispatch_workers(q):
    with open('./creds.txt', 'r') as f:
        for l in f:
            dct_l = json.loads(l)
            consumer_key = dct_l['consumer_key']
            consumer_secret = dct_l['consumer_secret']
            p = Process(target=start_worker, args=(q, consumer_key, consumer_secret))
            p.start()
