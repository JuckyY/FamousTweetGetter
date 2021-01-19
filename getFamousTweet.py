#!/usr/bin/python3

import tweepy
import pandas as pd
import environ

import logging
import time
import datetime

########################################
##  環境変数の.envファイルを読み込み  ##
########################################
BASE_DIR = environ.Path(__file__) - 1
env = environ.Env()
env_file = str(BASE_DIR.path('.env'))
env.read_env(env_file)

########################################
##    ロガーを呼出し、ファイル出力    ##
########################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
h = logging.FileHandler('FamousTweetGetter.log')
logger.addHandler(h)

########################################
## Twitter API                        ##
## Consumerキー、アクセストークン設定 ##
########################################
CONSUMER_KEY = env('CONSUMER_KEY')
CONSUMER_SECRET = env('CONSUMER_SECRET')
ACCESS_TOKEN = env('ACCESS_TOKEN')
ACCESS_SECRET = env('ACCESS_SECRET')

# 処理実行日
now_date = datetime.datetime.now()
now_date_str = now_date.strftime("%Y_%m_%d_%H%M")

# エクセルのヘッダーカラム名を定義
COLUMNS_NAME = ['ツイート時間', 'ツイート内容', 'いいね数', 'リツイート', 'ユーザー名', 'ユーザーID', 'フォロー数', 'フォロワー数']

# 取得するツイート数
GET_TWEET_CNT = 5000

# ループ回数
RANGE_CNT = 50

# 取得する「いいね」数の条件
SET_FAV_CNT = 100


def twitter_auth():
    """Twitter 認証

    Return Tweepy: api
    """
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    logger.debug('Twitter 認証が成功しました。')

    return api


def get_tweets(api):
    """ツイートデータ取得"""
    search_word = 'プログラミング'
    over_100_fav = []
    max_id = 0

    def limit_handled(cursor):
        while range(GET_TWEET_CNT):
            try:
                yield next(cursor)
            except tweepy.RateLimitError:
                time.sleep(15 * 60)
            except Exception as e:
                print(e)
                logger.debug(e)
                break

    for loop in range(RANGE_CNT):
        print(f"----------{loop + 1}周目　max_id: {max_id}----------")
        i = 0
        for tweet in limit_handled(
                tweepy.Cursor(api.search, q=search_word, exclude_replies=True, max_id=max_id - 1).items(GET_TWEET_CNT)):
            print(i)
            if max_id == 0 or i == (GET_TWEET_CNT - 1):
                max_id = tweet.id
                print(f"max_id更新: {max_id}")

            if list(tweet.text)[:4] != ['R', 'T', ' ', '@'] and tweet.favorite_count >= SET_FAV_CNT:
                print(str(i) + ":  " + tweet.text.replace('\n', ''))
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

            if i == (GET_TWEET_CNT - 1):
                i = 0
                break

            i += 1

    # pandasで[over_100_fav]をデータフレーム型に変換　⇒　[df]に格納
    df = pd.DataFrame(over_100_fav, columns=COLUMNS_NAME)

    # pandasで[df]をExcelに出力
    df.to_excel(f'いいね100超ツイート分析データ_{now_date_str}.xlsx', sheet_name='Sheet1')
    logger.debug('ツイートを取得しました。')


################################
##         処理を行う           ##
################################
if __name__ == '__main__':
    start = time.time()
    logger.debug(f'---------- 処理開始 ----------')

    api = twitter_auth()

    get_tweets(api)

    logger.debug('処理時間：' + str(time.time() - start))
