# -*- coding: utf-8 -*-

import os
import logging

SERVICE_NAME = "apiserver"

DEBUG = True
PROJECT_HOME = os.path.dirname(os.path.abspath(__file__))

MODE = 'develop'

if MODE == 'develop':
    OPERATION_DB = 'weapp'
    OPERATION_USER = 'weapp'
    OPERATION_HOST = 'db.weapp.com'
else:
    OPERATION_DB = 'operation'
    OPERATION_USER = 'operation'
    OPERATION_HOST = 'db.operation.com'


DATABASES = {
    'default': {
        'ENGINE': 'mysql+retry',
        'NAME': 'weapp',
        'USER': 'weapp',                      # Not used with sqlite3.
        'PASSWORD': 'weizoom',                  # Not used with sqlite3.
        'HOST': 'db.weapp.com',
        'PORT': '',
        'CONN_MAX_AGE': 100
    },
    'watchdog': {
        'ENGINE': 'mysql+retry',
        'NAME': OPERATION_DB,
        'USER': OPERATION_USER,                      # Not used with sqlite3.
        'PASSWORD': 'weizoom',                  # Not used with sqlite3.
        'HOST': OPERATION_HOST,
        'PORT': '',
        'CONN_MAX_AGE': 100
    }
}


MIDDLEWARES = [
    'middleware.OAuth_middleware.OAuthMiddleware',
    'middleware.core_middleware.ApiAuthMiddleware',

    
    # 'middleware.debug_middleware.SqlMonitorMiddleware',
    'eaglet.middlewares.zipkin_middleware.ZipkinMiddleware',
    'middleware.debug_middleware.RedisMiddleware',
    #账号信息中间件
    'middleware.webapp_account_middleware.WebAppAccountMiddleware',
]
#sevice celery 相关
EVENT_DISPATCHER = 'redis'

# settings for WAPI Logger
if MODE == 'develop':
    WAPI_LOGGER_ENABLED = True # Debug环境下不记录wapi详细数据
    WAPI_LOGGER_SERVER_HOST = 'mongo.weapp.com'
    WAPI_LOGGER_SERVER_HOST = 'mongo.weapp.com'
    WAPI_LOGGER_SERVER_PORT = 27017
    WAPI_LOGGER_DB = 'wapi'
    IMAGE_HOST = 'http://dev.weapp.com'
    PAY_HOST = 'api.weapp.com'
    #sevice celery 相关
    EVENT_DISPATCHER = 'local'
    ENABLE_SQL_LOG = False

    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(levelname)s : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        #filename='myapp.log',
        #filemode='w'
        )

else:
    # 真实环境暂时关闭
    #WAPI_LOGGER_ENABLED = False
    # 生产环境开启API Logger
    WAPI_LOGGER_ENABLED = True
    WAPI_LOGGER_SERVER_HOST = 'mongo.weapp.com'
    WAPI_LOGGER_SERVER_PORT = 27017
    WAPI_LOGGER_DB = 'wapi'
    IMAGE_HOST = 'http://dev.weapp.com'
    PAY_HOST = 'api.weapp.com'
    ENABLE_SQL_LOG = False

    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(levelname)s : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        #filename='apiserver.log',
        #filemode='w+'
        )


#缓存相关配置
REDIS_HOST = 'redis.weapp.com'
REDIS_PORT = 6379
REDIS_CACHES_DB = 1

REDIS_COMMON_DB = 4

# BDD_SERVER相关配置
BDD_SERVER2PORT = {
    'weapp': 8170,
    'weizoom_card': 8171,
    'apiserver': 8172
}


ENABLE_BDD_DUMP_RESPONSE = True

#watchdog相关
#WATCH_DOG_DEVICE = 'mysql'
WATCH_DOG_DEVICE = 'mongo'
WATCH_DOG_LEVEL = 200
WATCHDOG_CONFIG = {
    'TYPE': 'mongo',
    'SERVER_HOST': 'mongo.weapp.com',
    'SERVER_PORT': 27017,
    'DATABASE': 'watchdog'
}


IS_UNDER_BDD = False
# 是否开启TaskQueue(基于Celery)
TASKQUEUE_ENABLED = True


# Celery for Falcon
INSTALLED_TASKS = [
    #'resource.member.tasks',
    #'core.watchdog.tasks.send_watchdog',
    'api.tasks',
    
    'services.example_service.tasks.example_log_service',
    'services.order_notify_mail_service.task.notify_order_mail',
    'services.record_member_pv_service.task.record_member_pv',
    'services.update_member_from_weixin.task.update_member_info',
    'services.record_order_status_log_service.task.record_order_status_log',
    'services.update_product_sale_service.task.update_product_sale',
    'services.send_template_message_service.task.send_template_message',
    'services.order_notify_mail_service.task.notify_group_buy_after_pay',
    ]

#redis celery相关
REDIS_SERVICE_DB = 2

CTYPT_INFO = {
    'id': 'weizoom_h5',
    'token': '2950d602ffb613f47d7ec17d0a802b',
    'encodingAESKey': 'BPQSp7DFZSs1lz3EBEoIGe6RVCJCFTnGim2mzJw5W4I'
}

WZCARD_ENCRYPT_INFO = {
    'id': 'wzcard',
    'token': '23d0d602ffb6k3f47d7ec49d0a80k9',
    'encodingAESKey': 'BPQSp7DFZSs1lz7EBToIGe6RVC8CFTnGZm2mzJw5W4I'
}

if MODE == 'test':
    APPID = 'wx9b89fe19768a02d2'
else:
    APPID = 'wx8209f1f63f0b1d26'

COMPONENT_INFO = {
        'app_id' : APPID,
    }


PROMOTION_RESULT_VERSION = '2' #促销结果数据版本号


UPLOAD_DIR = os.path.join(PROJECT_HOME, '../static', 'upload')

# 通知用邮箱
# MAIL_NOTIFY_USERNAME = u'noreply@weizoom.com'
# MAIL_NOTIFY_PASSWORD = u'#weizoom2013'
# MAIL_NOTIFY_ACCOUNT_SMTP = u'smtp.mxhichina.com'
# MAIL_NOTIFY_USERNAME = u'972122220@qq.com'
# MAIL_NOTIFY_PASSWORD = u'irocwdrjrpkzbcfa'
# MAIL_NOTIFY_ACCOUNT_SMTP = u'smtp.qq.com'

MAIL_NOTIFY_USERNAME = u'noreply@notice.weizoom.com'
MAIL_NOTIFY_PASSWORD = u'Weizoom2015'
MAIL_NOTIFY_ACCOUNT_SMTP = u'smtp.dm.aliyun.com'


#最为oauthserver时候使用
if MODE == 'test':
    OAUTHSERVER_HOST = 'http://api.mall3.weizzz.com/'
    H5_DOMAIN = 'h5.mall3.weizzz.com'
    WEAPP_DOMAIN = 'docker.test.weizzz.com'
    MARKETAPP_DOMAIN = 'm_marketapp.weapp.weizzz.com'
elif MODE == 'develop':
    OAUTHSERVER_HOST = 'http://api.weizoom.com/'
    H5_DOMAIN = 'mall.weizoom.com'
    WEAPP_DOMAIN = 'dev.weapp.com'
    MARKETAPP_DOMAIN = 'm_marketapp.weapp.com'
else:
    OAUTHSERVER_HOST = 'http://api.weizoom.com/'
    H5_DOMAIN = 'mall.weizoom.com'
    WEAPP_DOMAIN = 'weapp.weizoom.com'
    MARKETAPP_DOMAIN = 'm_marketapp.weapp.weizoom.com'


DEV_SERVER_MULTITHREADING = False

REDIS_CACHE_KEY = ':1:api'

# redis锁，前缀lk
REGISTERED_LOCK_NAMES = {
	'__prefix': 'lk:',
	'coupon_lock': 'co:',
	'integral_lock': 'in:',
	'wz_card_lock': 'wc:',
	'wapi_lock': 'wapi:',
}
if 'deploy' == MODE:
    MNS_ACCESS_KEY_ID = 'eJ8LylRwQERRqOot'
    MNS_ACCESS_KEY_SECRET = 'xxPrfGcUlnsL7IPweJRqVekHTCu6Ad'
    MNS_ENDPOINT = 'http://1615750970594173.mns.cn-hangzhou-internal.aliyuncs.com/'
    MNS_SECURITY_TOKEN = ''
    TOPIC_PAID_ORDER = "paid-order"
else:
    MNS_ACCESS_KEY_ID = 'eJ8LylRwQERRqOot'
    MNS_ACCESS_KEY_SECRET = 'xxPrfGcUlnsL7IPweJRqVekHTCu6Ad'
    MNS_ENDPOINT = 'http://1615750970594173.mns.cn-hangzhou.aliyuncs.com/'
    MNS_SECURITY_TOKEN = ''
    TOPIC_PAID_ORDER = "paid-order-test"
# import simplejson
# try:
#     #TODO 可遍历所以配置文件
#     file = open("common-conf/mns-conf/mns_conf.json", "r")
#     MNS_CONF = file.read()
#     file.close()
#     MNS_CONF = simplejson.loads(MNS_CONF)
# except Exception, e:
#     logging.error("--------ERROR MNS CONF------------")
#     logging.error(e)


COMMON_SERVICE_ERROR_TYPE = 'common:wtf'

if 'deploy' == MODE:
    MNS_ACCESS_KEY_ID = 'LTAICKQ4rQBofAhF'
    MNS_ACCESS_KEY_SECRET = 'bPKU71c0cfrui4bWgGPO96tLiOJ0PZ'
    MNS_ENDPOINT = 'http://1615750970594173.mns.cn-hangzhou.aliyuncs.com/'
    MNS_SECURITY_TOKEN = ''
    SUBSCRIBE_QUEUE_NAME = 'mall-cache-manager'

else:
    MNS_ACCESS_KEY_ID = 'LTAICKQ4rQBofAhF'
    MNS_ACCESS_KEY_SECRET = 'bPKU71c0cfrui4bWgGPO96tLiOJ0PZ'
    MNS_ENDPOINT = 'https://1615750970594173.mns.cn-beijing.aliyuncs.com/'
    MNS_SECURITY_TOKEN = ''
    SUBSCRIBE_QUEUE_NAME = 'test-mall-cache-manager'

# event service相关设置
MESSAGE_BROKER = os.environ.get('_MESSAGE_BROKER', 'redis')
# 临时
TOPIC_NAME = "test-topic"

if 'deploy' == MODE:
    #锦歌饭卡的第三方支付公司host
    #如果apiserver在线上增加了部署节点，一定要把新ip告知该公司进行增加白名单操作，不然可能会出现饭卡无法消费的情况
    #目前的白名单ip有：114.55.86.248 114.55.74.184 114.55.74.184 114.215.255.147
    JINGE_HOST = 'http://59.110.52.17:8088/wxPay/'
    #可以使用锦歌饭卡的账号id列表
    CAN_USE_JINGE_CARD_ACCOUNT_IDS = [119, 1375]  #ceshi01和锦歌商城
else:
    JINGE_HOST = 'http://101.200.142.53:8088/wxPay/'
    CAN_USE_JINGE_CARD_ACCOUNT_IDS = [3, 119, 1375]  #jobs, ceshi01和锦歌商城