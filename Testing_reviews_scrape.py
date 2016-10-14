#!/usr/bin/env python
#-*- coding: utf-8 -*-

import BeautifulSoup
import time
from Testing_colored_print import bcolors
import hashlib

class Reviews(object):

	def __init__(self, soup, area_or_city,no_of_reviews_to_be_scrapped,no_of_blogs):
		self.soup = soup
		self.area_or_city = area_or_city
		try:
			self.reviews_list = self.soup.findAll("div" ,{"class": "res-review clearfix js-activity-root mbot   item-to-hide-parent stupendousact"})
			if no_of_blogs!="For Testing":
				if no_of_blogs!=0:
					print "{color} -<Blogs Found                =  {val} >-".format(color=bcolors.OKBLUE,val=str(no_of_blogs))
					no_of_reviews_to_be_scrapped=no_of_reviews_to_be_scrapped - no_of_blogs
				print "{color} -<Reviews had to be scraped  =  {val} >-".format(color=bcolors.OKBLUE,val=str(no_of_reviews_to_be_scrapped))
				print "{color} -<Reviews we are scrapping   =  {val} >-".format(color=bcolors.OKBLUE,val=str(len(self.reviews_list)))
			self.DOM_SUCCESSFUL = True
		except Exception as e:
			self.DOM_SUCCESSFUL = False
			raise StandardError("Couldnt find the div tag that was specified.")
			self.reviews_data=[]
		if len(self.reviews_list)>=no_of_reviews_to_be_scrapped:
			self.reviews_data = list()
			self.reviews()
		else:
			self.reviews_data=[]

	def reviews(self):
		for review in self.reviews_list:
			reviews = dict()
			reviews["user_name"] = self.user_name(review)
			reviews["user_id"] = self.user_id(review)
			reviews["user_url"] = self.user_url(review)
			reviews["user_reviews"] = self.user_reviews(review)
			reviews["user_followers"] = self.user_followers(review)
			reviews["review_url"] = self.review_url(review)
			reviews["user_rating"] = self.user_rating(review)
			reviews["review_time"] = self.review_time(review)
			reviews["review_summary"] = self.review_summary(review)
			reviews["review_text"] = self.review_text(review)
			reviews["review_likes"] = self.review_likes(review)
			reviews["review_id"] = self.review_id(review)
			reviews["eatery_id"] = self.eatery_id(review)
			reviews["scraped_epoch"] = int(time.time())			
			reviews["converted_epoch"] = self.converted_to_epoch(review)
			reviews["area_or_city"] = self.area_or_city
			reviews["management_response"] = self.review_management_response(review)
			reviews["readable_review_year"] = self.review_year(review)
			reviews["readable_review_month"] = self.review_month(review)
			reviews["readable_review_day"] = self.review_day(review)
			reviews["__review_id"]=hashlib.md5(str(reviews["converted_epoch"])+str(reviews["review_text"])).hexdigest()

			#This is the check whether the review has been classified or not
			reviews["is_classified"] = False
			
			#These are the enteries added to the review which will be modified later
			#This will be list of ditionaries with keys "sentence" and "messege" sentences which would have error on them.
			#sentence: On which the error occureed and "messege" the user input about what he thinks about this error
			reviews["error"] = list() 

			#This will be a list of sentences which will somehow implies that the user who wrote this review, is a retuning one
			reviews["repeated_customers"] = list()

			
			#This will be a list of tuples like this 
			#(sentence, nounphrases list)
			#Noun phrases list will be the list of ngrams which represent noun phrases belonging to this sentence
			reviews["noun_phrases"] = list()
			#This will be a list of sentences
			#(sentence)
			#these will be the sentences which should be break on the basis of interjections
			reviews["break_by_interjection"] = list()
			
			#All the following list will have sentences related to each of the tags
			#service, ambience, cost, food, overall, null
			reviews.update(dict.fromkeys(["service", "food", "ambience", "cost", "overall", "null", "negative", "postive"], list()))

			self.reviews_data.append(reviews)
		return

	def exception_handling(func):
		def deco(self, review):
			try:
				return func(self, review)
			
			except ValueError as e:
				print "{color} ERROR <{error}> in function <{function}>".format(color=bcolors.FAIL, error=e, function=func.__name__)
				return None

			except Exception as e:
				print "{color} ERROR <{error}> in function <{function}>".format(color=bcolors.FAIL, error=e, function=func.__name__)
				return None
		return deco

	@exception_handling
	def converted_to_epoch(self, review):
		"""
		This is the time in epoch, when the reviewws was wrtitten by the user, This is just the review time converted in epoch in 
		order to make search query easy and fast.
		Now the time_string is in the form : 2014-04-10 16:57:07 and it will be converted to 1401525098
		"""
		time_stamp = review.find("a", {"class": "res-review-date"}).time.get("datetime")
		return time.mktime(time.strptime(time_stamp, "%Y-%m-%d %H:%M:%S"))

	@exception_handling
	def review_year(self, review):
		epoch = self.converted_to_epoch(review)
		return time.strftime("%Y", time.localtime(int(epoch)))

	@exception_handling
	def review_month(self, review):
		epoch = self.converted_to_epoch(review)
		return time.strftime("%m", time.localtime(int(epoch)))
		
	@exception_handling
	def review_day(self, review):
		epoch = self.converted_to_epoch(review)
		return time.strftime("%d", time.localtime(int(epoch)))
	
	@exception_handling
	def eatery_id(self, review):
		return self.soup.find("div", {"class": "res-review-body clearfix"})["data-res_id"]

	@exception_handling
	def review_id(self, review):
		return review["data-review_id"]

	@exception_handling
	def user_name(self, review):
		return review.find("div" , {"class": "snippet__name"}).find("a").text

	@exception_handling
	def user_id(self, review):
		return review.find("a" , {"class": "snippet__link"})["data-entity_id"]

	@exception_handling
	def user_url(self, review):
		return review.find("div" , {"class": "snippet__head"}).find("a")["href"]

	@exception_handling
	def user_reviews(self, review):
		# return review.find("span" , {"class": "snippet__reviews"}).text  #chnaged something
		try:
			return review.find("span" , {"class": "snippet__reviews"}).text
		except Exception:
			return review.find("span" , {"class": "snippet__expertise"}).text

	@exception_handling
	def user_followers(self, review):
		try:
			return review.find("span" , {"class": "snippet__followers"}).text
		except Exception:
			return review.find("span" , {"class": "snippet__expertise"}).text

	@exception_handling
	def review_url(self, review):
		return review.find("a", {"class": "res-review-date"}).get("href")

	@exception_handling
	def review_time(self, review):
		return review.find("a", {"class": "res-review-date"}).time.get("datetime")

	@exception_handling
	def review_summary(self, review):
		try:
			return review.find("div", {"class": "rev-text"}).findChild().findChild().get("title")
		except Exception:
			return None
		     
	@exception_handling
	def review_text(self, review):
		try:
			review_dom = review.find("div", {"class": "rev-text hidden"})
			review_dom.find("div", {"class": "left"}).extract()#This removes the unimportqant divs from the review text div
			return review_dom.text
		except Exception:
			review_dom = review.find("div", {"class": "rev-text"})
			review_dom.find("div", {"class": "left"}).extract()#This removes the unimportqant divs from the review text div
			return review_dom.text

		# return review.findAll("div",{"class" : "left bold zdhl2 tooltip icon-font-level-6"})[1].text

	@exception_handling
	def review_management_response(self, review):
		try:
			return review.find("div", {"class": "review-reply-text "}).text
		except Exception:
			return None

	@exception_handling
	def review_likes(self, review):
		return review.find("a", {"class": "left thank-btn js-btn-thank "}).get("data-likes")

	def user_rating(self,review):
		for num in [1,2,3,4,5,6,7,8,9]:
			try:
				review.find("div",{"class" : "ttupper fs12px left bold zdhl2 tooltip icon-font-level-"+str(num)}).get("title")
				return (num/2.0)+0.5
			except Exception,e:
				pass
# area_or_city = "ncr"

# with open("one_eatery_html.txt","r") as content_file:
# 	content = content_file.read()
# soup=BeautifulSoup.BeautifulSoup(content)

# instance = Reviews(soup, area_or_city)
# reviews = instance.reviews_data
# print reviews