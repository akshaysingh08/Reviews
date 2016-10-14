#!/usr/bin/env python
#-*- coding: utf-8 -*-

import BeautifulSoup
import time
import sys
import os
import pwd
import random
from texttable import Texttable
# from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

from Testing_main_scrape import EateryData
from Testing_reviews_scrape import Reviews
from Testing_database import DB, collection, client
from Testing_colored_print import bcolors
from Testing_reviews_scrape import Reviews

"""

This Test is to be dome by running following command in the MadMachinesNLP01Scraping dir.
Command : nosetests --nocapture
it will ask for user input of either a no. less than total no of eateries in collectio or eatery_url that must be in collection.

"""


class TestCase_Testing_main_scrape(object):
	@classmethod
	def setup_class(klass):

		"""This method is run once for each class before any tests are run"""

	def setup(self):
		"""This method is run once before _each_ test method is executed"""

	def test_eatery(self):

		eatery_collection = collection("eatery")
		review_collection = collection("review")
		# user_collection   = collection("user") No Use to call this beacause review collection conatain the user details

		count_eatery_collection = eatery_collection.count()

		print "Total No of eateries in collection  = {val}".format(val=count_eatery_collection)

		# eatery_dict = eatery_collection.find_one({},{"eatery_id":1,"_id":0,"eatery_url":1},skip=user_input)

		user_input = raw_input("Enter the skip parameter or eatery link: ")

		if user_input.find("www.zomato.com")==-1:
			eatery_dict_from_collection = eatery_collection.find_one({},skip=int(user_input))
			review_dict_from_collection = review_collection.find_one({"eatery_id":eatery_dict_from_collection["eatery_id"]})
			print "Eatery Url : {val} ".format(val=eatery_dict_from_collection["eatery_url"])
		else:
			eatery_dict_from_collection = eatery_collection.find_one({"eatery_url":str(user_input)})
			if eatery_dict_from_collection==None:
				print "Eatery Url : {val}  is not in collection".format(val=user_input)
			else:
				review_dict_from_collection = review_collection.find_one({"eatery_id":eatery_dict_from_collection["eatery_id"]})

		service_args = ['--proxy=127.0.0.1:9050','--proxy-type=socks5',]
		executable_path="/home/{username}/Review/Reviews/phantomjs/bin/phantomjs".format(username=pwd.getpwuid( os.getuid() )[ 0 ])
		driver = webdriver.PhantomJS(executable_path=executable_path,service_args=service_args)
		driver.set_window_size(1024,720)
		driver.get(eatery_dict_from_collection["eatery_url"])

		# body = driver.find_element_by_tag_name("body")
		# body.send_keys(Keys.CONTROL + 't')
		driver.save_screenshot("testing.png")
		time.sleep(15)

		# html_content= driver.page_source
		# content = html_content.encode('ascii', 'ignore').decode('ascii')
		# self.soup = BeautifulSoup.BeautifulSoup(content)
		self.eatery_dict = {"eatery_url":eatery_dict_from_collection["eatery_url"]}

		"""Checking the DOM for Clickable objects"""

		# total_reviews = instance.eatery_total_reviews()
		total_reviews = eatery_dict_from_collection["eatery_total_reviews"]

		Reviews_Clickable = "False, Reviews are absent"
		try:
			if str(driver.find_element_by_css_selector("a.default-section-title.everyone.empty")).find("object")!=-1:
				Reviews_Clickable = "True"
				driver.find_element_by_css_selector("a.default-section-title.everyone.empty").click()
				time.sleep(5)
		except Exception as e:
			print "Reviews is not clickable beacause : " + str(e)
			Reviews_Clickable = "False"


		if Reviews_Clickable!="True":
			Reviews_Already_Clicked = "False, Reviews are absent"
			try:
				if str(driver.find_element_by_css_selector("a.default-section-title.everyone.active.selected")).find("object")!=-1:
					Reviews_Already_Clicked = "True"
			except Exception:
				Reviews_Already_Clicked = "False"
		else:
			Reviews_Already_Clicked = "False"

		load_more_Clickable = "False , Right now load more is absent "
		read_more_Clickable = "False , Right now read more is absent "
		# print Reviews_Clickable,Reviews_Already_Clicked
		if Reviews_Clickable=="True" or Reviews_Already_Clicked=="True":
			if int(total_reviews)>5:
				try:
					if str(driver.find_element_by_class_name("load-more")).find("object")!=-1:
						load_more_Clickable = "True"
						driver.find_element_by_class_name("load-more").click()
						time.sleep(5)
				except Exception as e:
					print "Load more is not clickable beacause : " + str(e)
					load_more_Clickable = "False"
			else:
				load_more_Clickable = "False , Right now load more is absent "

			try:
				if str(driver.find_elements_by_xpath("//div[@class='rev-text-expand']")).find("object")!=-1:
					read_more_Clickable = "True"
					read_more_links = driver.find_elements_by_xpath("//div[@class='rev-text-expand']")
					for link in read_more_links:
						time.sleep(random.choice([2, 3]))
						try:
							link.click()
						except Exception as e:
							pass
			except Exception as e:
				print "Read more is not clickable beacause : " + str(e)
				read_more_Clickable = "False"

		"""Checking The DOM of review"""

		html_content= driver.page_source
		content = html_content.encode('ascii', 'ignore').decode('ascii')
		self.soup = BeautifulSoup.BeautifulSoup(content)

		try:
			instance_for_Reviews = Reviews(soup=self.soup, area_or_city=None,no_of_reviews_to_be_scrapped=5000,no_of_blogs="For Testing")
			if instance_for_Reviews.DOM_SUCCESSFUL==True:
				Review_DOM_Status="True"
			# print instance_for_Reviews.user_name(review=instance_for_Reviews.reviews_list[0])
		except Exception as e:
			Review_DOM_Status="False"

		"""Checking the DOM of eatery details"""
		instance = EateryData(eatery=self.eatery_dict,no_of_reviews_to_be_scrapped=None,got_soup=True,soup_for_test_case=self.soup)

		# print Reviews_Clickable
		# print Reviews_Already_Clicked
		# print load_more_Clickable
		# print read_more_Clickable

		t = Texttable()
		t.set_cols_width([25,65,65])
		t.set_cols_align(["c","c","c"])
		t.set_cols_valign(["m","m","m"])
		t.add_rows([["Eatery Attributes","From Live Testing","From Collection"],

			["Name",str(instance.retry_eatery_name()),str(eatery_dict_from_collection["eatery_name"])],

			["Id",instance.retry_eatery_id(),eatery_dict_from_collection["eatery_id"]],

			["Area or City",instance.eatery_area_or_city(),eatery_dict_from_collection["eatery_area_or_city"]],

			["Address",instance.retry_eatery_address(),eatery_dict_from_collection["eatery_address"]],

			["Rating",instance.retry_eatery_rating(),eatery_dict_from_collection["eatery_rating"]],

			["Total Reviews",instance.eatery_total_reviews(),eatery_dict_from_collection["eatery_total_reviews"]],

			["Popular Reviews",instance.eatery_popular_reviews(),eatery_dict_from_collection["eatery_popular_reviews"]],

			["Cost",instance.retry_eatery_cost(),eatery_dict_from_collection["eatery_cost"]],

			["Cuisine",instance.retry_eatery_cuisine(),eatery_dict_from_collection["eatery_cuisine"]],

			["Highlights",instance.eatery_highlights(),eatery_dict_from_collection["eatery_highlights"]],

			["Known For",instance.eatery_known_for(),eatery_dict_from_collection["eatery_known_for"]],

			["Opening Hours",instance.eatery_opening_hours(),eatery_dict_from_collection["eatery_opening_hours"]],

			["","",""],

			["Reviews Button Clickable",Reviews_Clickable,"-"],

			["Reviews Button Already Clicked",Reviews_Already_Clicked,"-"],

			["Load More Clickable",load_more_Clickable,"-"],

			["Read More Clickable",read_more_Clickable,"-"],

			["Reviews Can be Scrapped",Review_DOM_Status,"-"],

			["","",""],

			["User Name",instance_for_Reviews.user_name(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["user_name"]],

			["User Id",instance_for_Reviews.user_id(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["user_id"]],

			["User url",instance_for_Reviews.user_url(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["user_url"]],

			["User Reviews",instance_for_Reviews.user_reviews(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["user_reviews"]],

			["User Followers",instance_for_Reviews.user_followers(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["user_followers"]],

			["User Rating",instance_for_Reviews.user_rating(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["user_rating"]],

			["Review url",instance_for_Reviews.review_url(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["review_url"]],

			["Review time",instance_for_Reviews.review_time(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["review_time"]],

			["Review Summary",instance_for_Reviews.review_summary(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["review_summary"]],

			["Review Text",instance_for_Reviews.review_text(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["review_text"]],

			["Review Id",instance_for_Reviews.review_id(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["review_id"]],

			["Review Likes",instance_for_Reviews.review_likes(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["review_likes"]],

			["Review Management Response",instance_for_Reviews.review_management_response(review=instance_for_Reviews.reviews_list[0]),review_dict_from_collection["management_response"]]])

		print t.draw()

		if Reviews_Clickable=="False" and Reviews_Already_Clicked=="False":
			print "\n{color} Total Reviews Button is not clickable and was not Already clicked, CHECK DOM".format(color=bcolors.FAIL)
		else:
			print "\n{color} One out of Reviews_Clickable or Reviews_Already_Clicked is True".format(color=bcolors.OKGREEN)

		driver.close()