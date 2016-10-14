#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import absolute_import

import celery
from celery import states
from celery.task import Task, TaskSet
from celery.result import TaskSetResult
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from celery.registry import tasks
from celery import task, subtask, group
from celery.utils import gen_unique_id, cached_property

import time
import math
from pymongo import MongoClient
import random
import logging
import inspect
from datetime import timedelta

# from App import app
from Testing_colored_print import bcolors
from Testing_main_scrape_celery import scrape_links, eatery_specific, eateries_from_page, pagination_again, return_local_area_dict_from_big_area

# connection = pymongo.Connection()
# db = connection.intermediate
# collection = db.intermediate_collection

from celery import Celery

app = Celery()
app.config_from_object("celeryconfig")

# client = MongoClient("localhost", 27017, w=1, j=True)
# db = client.celery_canwork
# collection = db.celery_collection


logger = logging.getLogger(__name__)

"""
To run tasks for scraping one restaurant 
runn.apply_async(["https://www.zomato.com/ncr/pita-pit-lounge-greater-kailash-gk-1-delhi", None, None, "one_eatery"])

TO scrape a list of restaurant use this
runn.apply_async(args=["https://www.zomato.com/ncr/south-delhi-restaurants", 30, 270, "local_area"])
	 Task.acks_late
	     If set to True messages for this task will be acknowledged after the task has been executed, 
	     not just before, which is the default behavior.
	
	Task.ErrorMail
	    If the sending of error emails is enabled for this task, then this is the class defining the 
	    logic to send error mails.
	
	Task.store_errors_even_if_ignored
	    If True, errors will be stored even if the task is configured to ignore results.

	
	Task.ErrorMail
	    If the sending of error emails is enabled for this task, then this is the class defining the 
	    logic to send error mails.


	 Task.rate_limit
	     Set the rate limit for this task type which limits the number of tasks that can be run in a 
	     given time frame. Tasks will still complete when a rate limit is in effect, but it may take 
	     some time before it’s allowed to start.
	     If this is None no rate limit is in effect. If it is an integer or float, it is interpreted as 
	     “tasks per second”.
	     The rate limits can be specified in seconds, minutes or hours by appending “/s”, “/m” or “/h” 
	     to the value. Tasks will be evenly distributed over the specified time frame.
	     Example: “100/m” (hundred tasks a minute). This will enforce a minimum delay of 600ms between 
	     starting two tasks on the same worker instance.
"""
global temp_eateries_list
temp_eateries_list=[]

@app.task(ignore_result=True, max_retries=3, retry=True)
def eateries_list(url, number_of_restaurants, skip, Type_of_url):
	print "{color} Execution of the function {function_name} starts".format(color=bcolors.OKBLUE, function_name=inspect.stack()[0][3])
	eateries_list = scrape_links(url, number_of_restaurants, skip, Type_of_url)
	return eateries_list

@app.task()
class process_eatery(celery.Task):
	ignore_result=True, 
	max_retries=3, 
	acks_late=True
	default_retry_delay = 5
	def run(self,item):
		print "{color} Execution of the function {function_name} starts".format(color=bcolors.OKBLUE, function_name=inspect.stack()[0][3])
		eatery_specific(item[0],item[1],item[2])
		return

	def after_return(self, status, retval, task_id, args, kwargs, einfo):
		#exit point of the task whatever is the state
		logger.info("Ending run")
		pass

	def on_failure(self, exc, task_id, args, kwargs, einfo):
		print "fucking faliure occured"
		self.retry(exc=exc)

@app.task()
class process_page(celery.Task):
	global temp_eateries_list
	temp_eateries_list=[]
	ignore_result=True, 
	max_retries=3, 
	acks_late=True
	default_retry_delay = 5
	def run(self,item):
		global temp_eateries_list
		print "{color} Execution of the function {function_name} starts".format(color=bcolors.OKBLUE, function_name=inspect.stack()[0][3])
		temp_eateries_list=None
		temp_eateries_list=eateries_from_page(item)
		# print "The length of final_eateries_list before EXTENDING : " + str(len(final_eateries_list))
		# final_eateries_list.extend(one for one in temp_eateres_list)
		# print "The length of final_eateries_list after EXTENDING  : " + str(len(final_eateries_list))
		# no_of_tasks_by_each_task-=1
		return

	def after_return(self, status, retval, task_id, args, kwargs, einfo):
		# global final_eateries_list
		global temp_eateries_list
		print "The length of temp_eateries_list : " + str(len(temp_eateries_list))
		process_list = dmap.s(temp_eateries_list,process_eatery.s())
		process_list()
		logger.info("Ending run")
		pass

	def on_failure(self, exc, task_id, args, kwargs, einfo):
		print "fucking faliure occured"
		self.retry(exc=exc)

@app.task(ignore_result=True, max_retries=3, retry=True, acks_late= True)
def dmap(it, callback):
	# global final_eateries_list
	# Map a callback over an iterator and return as a group
	callback = subtask(callback)
	return group(callback.clone([arg,]) for arg in it)()

@app.task(ignore_result=True, max_retries=3, retry=True)
def runn(url, number_of_restaurants, skip, Type_of_url):
	# global final_eateries_list
	# global no_of_tasks_by_each_task

	if Type_of_url=="local_area":
		pages_url=pagination_again(url)
		process_local_area = dmap.s(pages_url,process_page.s())
		process_local_area()

	elif Type_of_url=="one_page" or Type_of_url=="one_eatery":
		process_list = eateries_list.s(url, number_of_restaurants, skip, Type_of_url)| dmap.s(process_eatery.s())
		process_list()
	
	elif Type_of_url=="big_area":
		#"lets take url is : https://www.zomato.com/varanasi"
		pages_url=pagination_again(str(url)+"/restaurants")
		# no_of_tasks_by_each_task = int(math.ceil(float(len(pages_url))/2))
		process_local_area = dmap.s(pages_url,process_page.s())
		process_local_area()
		# local_area_dict = return_local_area_dict_from_big_area(url)
		# for one_local_area_dict in local_area_dict:
		# 	pages_url = pagination_again(one_local_area_dict["area_url"])

		# 	process_local_area = dmap.s(pages_url,process_page.s())
		# 	process_local_area()
	return