#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
This is the file responsible for actually inserting data in the database.
"""

from Testing_database import DB, collection, client
#from custom_logging import exceptions_logger
import traceback
import sys
import logging
import inspect
#from main_scrape import scrape
import pymongo
import traceback
import time
from pymongo.errors import BulkWriteError
from Testing_colored_print import bcolors

#LOG_FILENAME = 'exceptions_logger.log'
#:wlogging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG,)

class DBInsert(object):

	@staticmethod
	def db_insert_eateries(eatery):
		eatery_collection = collection("eatery")
		# db = client.modified_canworks  I think needed for bulk
		try:
			eatery_collection.update({"eatery_id": eatery.get("eatery_id")}, {"$set": eatery}, upsert=True)
			print "{color} FUNCTION--<{function_name}>  SUCCESS--<{success}>".format(color=bcolors.OKBLUE, function_name=inspect.stack()[0][3],success="Eatery has been inserted successfully")
		except Exception as e:
			print "{color} FUNCTION--<{function_name}>  ERROR--<{error}>".format(color=bcolors.FAIL, function_name=inspect.stack()[0][3], error=e)

		"""bulk = db.eatery.initialize_unordered_bulk_op()
		bulk.insert(eatery)
		try:
			bulk.execute()
		except BulkWriteError as __error:
			print "{color} FUNCTION--<{function_name}>  ERROR--<{error}>".format(color=bcolors.OKGREEN, function_name=inspect.stack()[0][3], error=__error.details)
			"""
		return
	
	@staticmethod
	def db_insert_reviews(reviews):
		success = 0
		# failure = 0
		err=None
		review_collection = collection("review")
		for review in reviews:
			try:
				review_collection.insert(review)
				success+=1
			except Exception as e:
				print "{color} FUNCTION--<{function_name}>  ERROR--<{error}>".format(color=bcolors.FAIL, function_name=inspect.stack()[0][3], error=e)

		print "{color} FUNCTION--<{function_name}> SUCCESS--<{success}> {val1}/{val2} Times".format(val1=success,val2=len(reviews),color=bcolors.OKBLUE, function_name="db_insert_reviews", success="Reviews inserted successfully")
		# if err!=None:
			# print "{color} FUNCTION--<{function_name}>  ERROR--<{error}> {val}/{val2} Times".format(val=failure,val2=len(reviews),color=bcolors.FAIL, function_name="db_insert_reviews", error=err)
		return success

	@staticmethod
	def db_insert_users(users):
		new = 0
		exist = 0
		user_collection = collection("user")
		for user in users:
			try:
				result = user_collection.update({"user_id": user.get("user_id"), "user_name": user.get("user_name")},{"$set": {"user_url": user.get("user_url"), "user_followers": user.get("user_followers"), "user_reviews" : user.get("user_reviews"), "updated_on": int(time.time())}}, upsert=True)
				# sys.stdout.write("\r {color} FUNCTION--<{function_name}>  MESSEGE--<Update Existing={messege}>\r".format(color=bcolors.OKBLUE, function_name=inspect.stack()[0][3], messege=result.get("updatedExisting")))
				# sys.stdout.flush()
				if result.get("updatedExisting")==True:
					exist+=1
				else:
					new+=1
			except Exception as e:
				print "{color} FUNCTION--<{function_name}>  ERROR--<{error}>".format(color=bcolors.FAIL, function_name=inspect.stack()[0][3], error=e)

		print "{color} FUNCTION--<{function_name}> MESSEGE --<Update Existing={messege}> {val}/{val2} users".format(val=exist,val2=len(users),color=bcolors.OKBLUE, function_name="db_insert_users", messege="True")
		print "{color} FUNCTION--<{function_name}> MESSEGE --<Update Existing={messege}> {val}/{val2} users".format(val=new,val2=len(users),color=bcolors.OKBLUE, function_name="db_insert_users", messege="False")
		return

	@staticmethod
	def insert_db(url, number_of_restaurants, stop, skip):
		__data = scrape(url, number_of_restaurants, stop, skip)
		DBInsert.db_insert_eateries(__data[0])
		DBInsert.db_insert_reviews(__data[1])
		DBInsert.db_insert_users(__data[2])
		return

	@staticmethod
	def db_delete_reviews(eatery_id):
		review_collection = collection("review")
		try:
			review_collection.delete_many({"eatery_id":str(eatery_id)})
		except Exception as e:
			print "{color} FUNCTION--<{function_name}>  ERROR--<{error}>".format(color=bcolors.FAIL, function_name=inspect.stack()[0][3], error=e)
		return

	@staticmethod
	def db_delete_eatery(eatery_id):
		eatery_collection = collection("eatery")
		try:
			eatery_collection.delete_one({"eatery_id":str(eatery_id)})
		except Exception as e:
			print "{color} FUNCTION--<{function_name}>  ERROR--<{error}>".format(color=bcolors.FAIL, function_name=inspect.stack()[0][3], error=e)
		return
#if __name__ == "__main__":
#	DBInsert.insert_db("http://www.zomato.com/ncr/malviya-nagar-delhi-restaurants?category=1", 40, 40 , 2)


# {u'nYields': 0,
#  u'nscannedAllPlans': 25359,
#   u'allPlans': [{u'cursor': u'BasicCursor', u'indexBounds': {},
#    u'nscannedObjects': 25359, u'nscanned': 25359, u'n': 25359}],
#     u'millis': 19, u'nChunkSkips': 0, u'server': u'Shubh:27017',
#      u'n': 25359, u'cursor': u'BasicCursor',
#       u'scanAndOrder': False, u'indexBounds': {}, u'nscannedObjectsAllPlans': 25359,
#        u'isMultiKey': False,
#          u'indexOnly': False, u'nscanned': 25359, u'nscannedObjects': 25359}
