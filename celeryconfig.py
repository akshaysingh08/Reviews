#!/usr/bin/env python
#-*- coding: utf-8 -*-

import os
from kombu import Exchange, Queue
from celery.schedules import crontab
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read("global.cfg")
#from kombu import serialization
#serialization.registry._decoders.pop("application/x-python-serialize")
#BROKER_URL = 'redis://'
# BROKER_URL = 'redis://localhost:6379/0'
BROKER_URL = 'redis://'+config.get('redis','ip')+':'+config.get('redis','port')+'/0'

CELERY_QUEUES = (
		Queue('junk', Exchange('default', delivery_mode= 2),  routing_key='junk.import'),
		Queue('scrape_url', Exchange('default', delivery_mode= 2),  routing_key='scrape_url.import'),
		Queue('process_eatery_q', Exchange('default', delivery_mode=2),  routing_key='process_eatery_q.import'),
		Queue('intermediate', Exchange('default', delivery_mode=2),  routing_key='intermediate.import'),
		Queue('process_page_q',Exchange('default',delivery_mode=2),routing_key='process_page_q.import'),
		)

CELERY_ROUTES = {
		'tasks.runn': {
				'queue': 'junk',
				'routing_key': 'junk.import',
					},
		'tasks.eateries_list': {
				'queue': 'scrape_url',
				'routing_key': 'scrape_url.import',
				},

		'tasks.process_eatery': {
				'queue': 'process_eatery_q',
				'routing_key': 'process_eatery_q.import',
							        },
		'tasks.dmap': {
				'queue': 'intermediate',
				'routing_key': 'intermediate.import',
							        },

		'tasks.process_page': {
				'queue':'process_page_q',
				'routing_key':'process_page_q.import',
									},
		}

#BROKER_HOST = ''
#BROKER_PORT = ''
#BROKER_USER = ''
#BROKER_PASSWORD = ''
#BROKER_POOL_LIMIT = 20

#Celery result backend settings, We are using monngoodb to store the results after running the tasks through celery
CELERY_RESULT_BACKEND = 'mongodb'

# mongodb://192.168.1.100:30000/ if the mongodb is hosted on another sevrer or for that matter running on different port or on different url on 
#the same server

# CELERY_MONGODB_BACKEND_SETTINGS = {
# 		'host': '192.168.69.1',
# 		'port': 27017,
# 		'database': 'celery',
# #		'user': '',
# #		'password': '',
# 		'taskmeta_collection': 'celery_taskmeta',
# 			}


CELERY_MONGODB_BACKEND_SETTINGS = {
		'host': config.get('mongodb','host'),
		'port': config.getint('mongodb','port'),
		'database': 'celery',
#		'user': '',
#		'password': '',
		'taskmeta_collection': 'celery_taskmeta',
			}


#CELERY_TASK_SERIALIZER = 'json'
#CELERY_RESULT_SERIALIZER = 'json'#CELERY_ACCEPT_CONTENT=['application/json']
CELERY_ENABLE_UTC = True
CELERY_DISABLE_RATE_LIMITS = True
CELERY_RESULT_PERSISTENT = True #Keeps the result even after broker restart
# ENV_PYTHON="$CELERYD_CHDIR/env/bin/python"

CELERYD_NODES="w1 w2"
CELERYD_CONCURRENCY = 1
CELERYD_LOG_FILE="%s/celery.log"%os.path.dirname(os.path.abspath(__file__))
#CELERYD_POOL = 'gevent'