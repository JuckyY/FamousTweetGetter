#!/usr/bin/python3

import tweepy
import pandas as pd
import environ

import logging
import time
import datetime

######################################
## 環境変数の.envファイルを読み込み      ##
######################################
BASE_DIR = environ.Path(__file__) - 1
env = environ.Env()
env_file = str(BASE_DIR.path('.env'))
env.read_env(env_file)

######################################
##     ロガーを呼出し、ファイル出力      ##
######################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
h = logging.FileHandler('FamousTweetGetter.log')
logger.addHandler(h)

########################################
## Twitter API                        ##
## Consumerキー、アクセストークン設定      ##
########################################
CONSUMER_KEY = env('CONSUMER_KEY')
CONSUMER_SECRET = env('CONSUMER_SECRET')
ACCESS_TOKEN = env('ACCESS_TOKEN')
ACCESS_SECRET = env('ACCESS_SECRET')

# 処理実行日
now_date = datetime.datetime.now()
now_date_str = now_date.strftime("%y%m%d")

# エクセルのヘッダーカラム名を定義
COLUMNS_NAME = ['ツイート時間', 'ツイート内容', 'いいね数', 'リツイート', 'ユーザー名', 'ユーザーID', 'フォロー数', 'フォロワー数']

# 取得するツイート数
GET_TWEET_CNT = 50000

# 15分のインターバル API制限回避
INTERVAL_POINT = list(range(2499, GET_TWEET_CNT, 2500))


def twitter_auth():
    """Twitter 認証

    Return Tweepy: api
    """
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    logger.debug('Twitter 認証が成功しました。')
    print('Twitter 認証が成功しました。')

    return api


def get_tweets(api):
    """ツイートデータ取得"""
    search_word = 'プログラミング'
    over_100_fav = []

    for i in range(1):

        # 最初の1件だけ取得して、max_idをセット
        for num, tweet in enumerate(tweepy.Cursor(api.search, q=search_word, exclude_replies=True).items(1)):
            max_id = tweet.id

        for num, tweet in enumerate(
                tweepy.Cursor(api.search, q=search_word, exclude_replies=True, max_id=max_id - 1).items(GET_TWEET_CNT)):
            try:
                if list(tweet.text)[:4] != ['R', 'T', ' ', '@'] and tweet.favorite_count >= 100:
                    # ['ツイート時間', 'ツイート内容', 'いいね数', 'リツイート', 'ユーザー名', 'ユーザーID', 'フォロー数', 'フォロワー数']
                    over_100_fav.append([tweet.created_at,
                                         tweet.text.replace('\n', ''),
                                         tweet.favorite_count,
                                         tweet.retweet_count,
                                         tweet.user.name,
                                         tweet.user.screen_name,
                                         tweet.user.friends_count,
                                         tweet.user.followers_count,
                                         ])

                    # pandasで[over_100_fav]をデータフレーム型に変換　⇒　[df]に格納
                    df = pd.DataFrame(over_100_fav, columns=COLUMNS_NAME)

                    # pandasで[df]をExcelに出力
                    df.to_excel(f'いいね100超ツイート分析データ_{now_date_str}.xlsx', sheet_name='Sheet1')
                    print('ツイートを取得しました。')

                elif num in INTERVAL_POINT or (num == (GET_TWEET_CNT - 1) and i != 1):
                    time.sleep(60 * 15)
                    api = twitter_auth()

                print(num)
                max_id = tweet.id

            except Exception as e:
                print(e)
                api = twitter_auth()


################################
##         処理を行う           ##
################################
if __name__ == '__main__':
    start = time.time()

    api = twitter_auth()

    get_tweets(api)

    print('処理時間：' + str(time.time() - start))

