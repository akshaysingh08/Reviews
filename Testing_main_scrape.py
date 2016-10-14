#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import os
# import csv
# import codecs
import time
import random
# import goose
import BeautifulSoup
import re
import math
import timeit
from Testing_database import DB, collection, client
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from Testing_reviews_scrape import Reviews
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Testing_db_insertion import DBInsert
from Testing_colored_print import bcolors

class EateriesList(object):

	def __init__(self, url, number_of_restaurants, skip, is_eatery):
		global driver

		self.driver = driver

		if is_eatery:
			#This implies that the url that has been given to initiate this class is the restaurant url not a url on which 
			#lots of restaurant urls are present
			self.url = url
			eatery_dict= {"eatery_url":self.url}
			self.eatery_specific(eatery_dict,"check",1)
		
		else:
			self.url = url
			self.number_of_restaurants = number_of_restaurants
			self.skip = skip

			if self.url.find("page=")==-1:
				self.soup_only_for_pagination = self.prepare_soup(self.url)
				pagination_divs = self.soup_only_for_pagination.findAll("div", {"class": "col-l-3 mtop0 alpha tmargin pagination-number"})
				for div in pagination_divs:
					try:
						pages_number=int(div.div.string.split(" ")[-2])
					except :
						pages_number=1
				try:
					pages_url = ["%s?page=%s"%(self.url, page_number) for page_number in range(1, int(pages_number)+1)]
					"""Pagination Done"""

					for page_link in pages_url:
						print "{color} -<Loading  {val}>-".format(color=bcolors.OKBLUE,val=page_link)
						if page_link == self.url:
							# self.prepare_and_return_eateries_list(self.soup_only_for_pagination,page_link)
							temp_list=self.prepare_and_return_eateries_list(self.soup_of_each_page,page_link)
							self.Calling_Processing_one_eatery______(temp_list)
						else:
							self.soup_of_each_page = self.prepare_soup(page_link)
							temp_list=self.prepare_and_return_eateries_list(self.soup_of_each_page,page_link)
							self.Calling_Processing_one_eatery______(temp_list)

						print """\n"""
						print "{color} -<Done {val}>-".format(color=bcolors.OKGREEN,val=page_link)

				except UnboundLocalError:
					driver.close()
			else:
				self.soup_of_each_page = self.prepare_soup(self.url)
				# return self.prepare_and_return_eateries_list(self.soup_of_each_page,self.url)
	        	# self.Calling_Processing_one_eatery______......(temp_list)

        def prepare_soup(self, url):
        	global driver
        	# if url.find("=")==-1:
        	self.driver.get(url)
        	html = driver.page_source
        	# f=open("Testingfile.txt","w")
        	content = html.encode('ascii', 'ignore').decode('ascii')
        	# f.write(content)
        	# f.close()

        	# with open("Testingfile.txt","r") as content_file:
        	# 	content = content_file.read()
        	soup = BeautifulSoup.BeautifulSoup(content)
        	return soup
        	"""
        	Now we can go that page no. for ex say 10
        	like

        	http://www.zomato.com/ncr/malviya-nagar-delhi-restaurants?page=1
        	.
        	.
        	.
        	http://www.zomato.com/ncr/malviya-nagar-delhi-restaurants?page=10
        	"""

	def prepare_and_return_eateries_list(self):

		eatries_lis = self.soup_of_each_page.findAll("li",{"class":"resZS mbot0 pbot0 bb even  status1"})
		try:
			eatries_lis = eatries_lis + self.soup_of_each_page.findAll("li",{"class":"resZS mbot0 pbot0 bb even near status1"})
		except Exception as e:
			pass
		eateries_list=list()
		for eatery_soup in eatries_lis:
			eatery = dict()
			eatery["eatery_id"] = eatery_soup.get("data-res_id")
			eatery["eatery_url"] = eatery_soup.find("a").get("href")
			eatery["eatery_name"] = eatery_soup.find("a").text
			try:
				eatery["eatery_address"] = eatery_soup.find("span", {"class": "search-result-address"})["title"]
			except Exception:
				eatery["eatery_address"] = None

			try:
				eatery["eatery_cuisine"] = eatery_soup.find("div", {"class": "res-snippet-small-cuisine truncate search-page-text"}).text
			except Exception:
				eatery["eatery_cuisine"] = None

			try:
				eatery["eatery_cost"] = eatery_soup.find("div", {"class": "search-page-text"}).text
			except Exception:
				eatery["eatery_cost"] = None

			soup = eatery_soup.find("div", {"class": "right"})

			try:
				eatery["eatery_rating"] = {"rating": soup.findNext().text.replace(" ", "").replace("\n", ""),"votes": soup.find("div",  {"class": "rating-rank right"}).findNext().text }
			except Exception:
				eatery["eatery_rating"] = None

			try:
				eatery["eatery_title"] = eatery_soup.findNext().get("title")
			except Exception:
				eatery["eatery_title"] = None
			
			try:
				collection_of_trending =  eatery_soup.find("div", {"class": "srp-collections"}).findAll("a")
				eatery["eatery_trending"] = [element.text for element in collection_of_trending]

			except Exception:
				eatery["eatery_trending"] = None

			##Finding total number of reviews for each eatery soup
			try:
				eatery["eatery_total_reviews"] = eatery_soup.find("a", {"data-result-type": "ResCard_Reviews"}).text.split(" ")[0]
			except Exception:
				eatery["eatery_total_reviews"] = 0

			eateries_list.append(eatery)

		return eateries_list

class EateryData(object):

	def __init__(self, eatery,no_of_reviews_to_be_scrapped,got_soup,soup_for_test_case):
		global driver
		global no_of_blogs

		self.eatery = eatery

		self.no_of_reviews_to_be_scrapped=no_of_reviews_to_be_scrapped

		"""Preparing Soup of each eatry"""
		if not got_soup:

			self.soup = self.with_selenium()

			if self.soup != "No review to scrape" and self.soup !=None:
				"""Prepared Soup"""
				print "{color} \n-<Eatery Soup Prepared Successfully>-".format(color=bcolors.OKGREEN)

				self.retry_eatery_id()
				self.retry_eatery_name()
				self.retry_eatery_address()
				self.retry_eatery_cost()
				# self.retry_eatery_trending()    # Not gettin what exactly it needs to extract
				# self.retry_eatery_title()       # Not gettin what exactly it needs to extract
				self.retry_eatery_rating()
				self.retry_eatery_cuisine()
				self.eatery_highlights()
				self.eatery_popular_reviews()
				self.eatery_opening_hours()
				# self.eatery_metro_stations()    #to scrape that a new link of Nearby Metro will have to open
				# self.eatery_photos()            # not requiredd
				# self.eatery_recommended_order() #not listed on page now
				#self.eatery_buffet_price()       #not listed on page now
				# self.eatery_buffet_details()      #not listed on page now
				self.eatery_longitude_latitude()
				self.eatery_total_reviews()         #Nothing but total reviews
				self.eatery_area_or_city()
				self.eatery_known_for()
				self.eatery_scrapping_year()
				self.eatery_scrapping_month()
				self.eatery_scrapping_day()
				# self.eatery_establishment_type()

				self.eatery_reviews()

				self.last_no_of_reviews_to_be_scrapped = int(self.no_of_reviews_to_be_scrapped) - int(no_of_blogs)

		else:
			self.soup = soup_for_test_case

	def with_selenium(self):

		global driver
		global no_of_blogs
		"""
		chromedriver = "{path}/chromedriver".format(path=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
		os.environ["webdriver.chrome.driver"] = chromedriver
		driver = webdriver.Chrome(chromedriver)
		"""
		driver.get(self.eatery.get("eatery_url"))

		if self.no_of_reviews_to_be_scrapped=="check":
			time.sleep(3)
			html_content= driver.page_source
			content = html_content.encode('ascii', 'ignore').decode('ascii')
			soup = BeautifulSoup.BeautifulSoup(content)

			if not self.eatery.get("eatery_id"):
				try:
					self.eatery["eatery_id"] = soup.find("div", {"itemprop": "ratingValue"}).get("data-res-id")
				except Exception:
					self.eatery["eatery_id"] = None
				print "{color}-< checking....eatery_id..............................{val} >-".format(color=bcolors.OKBLUE,val=str(self.eatery["eatery_id"]))

			try:
				self.eatery["eatery_total_reviews"]=soup.find("div", {"class": "res-main-stats-num"}).text
			except Exception as e:
				self.eatery["eatery_total_reviews"] = 0
			print "{color}-< checking....eatery_total_reviews...................{val} >-".format(color=bcolors.OKBLUE,val=str(self.eatery["eatery_total_reviews"]))

			"Now checking the no of reviews to be scrapped"
			
			review_collection = collection("review")

			try:
				reviews_in_collection = review_collection.find({"eatery_id":self.eatery["eatery_id"]}).count()
				print "{color}-< checking....reviews in collection..................{val} >-".format(color=bcolors.OKBLUE,val=str(reviews_in_collection))
				if reviews_in_collection<self.eatery["eatery_total_reviews"]:
					self.no_of_reviews_to_be_scrapped = int(self.eatery["eatery_total_reviews"]) - int(reviews_in_collection)
					print "{color}-< checking....no_of_reviews_to_be_scrapped...........{val} >-".format(color=bcolors.OKBLUE,val=str(self.no_of_reviews_to_be_scrapped))
					if self.no_of_reviews_to_be_scrapped<0:
						self.no_of_reviews_to_be_scrapped=0
				else:
					self.no_of_reviews_to_be_scrapped = 0
					print "{color}-< checking....no_of_reviews_to_be_scrapped...........{val} >-".format(color=bcolors.OKBLUE,val=str(self.no_of_reviews_to_be_scrapped))
			except Exception as e:
				self.no_of_reviews_to_be_scrapped = int(self.eatery["eatery_total_reviews"])

		reviews_exists=False
		# WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.default-section-title.everyone.empty")))

		if self.no_of_reviews_to_be_scrapped!=0:
			time.sleep(15)
			try:
				driver.find_element_by_css_selector("a.default-section-title.everyone.empty").click()
				reviews_exists = True
				print "{color}-< Total Reviews Button was Clicked in 1st try>-".format(color=bcolors.OKGREEN)
			except Exception,e:
				print "{color}-< Total Reviews could not clicked in 1st try>-".format(color=bcolors.FAIL)
				try:
					time.sleep(5)
					driver.find_element_by_css_selector("a.default-section-title.everyone.empty").click()
					print "{color}-< Total Reviews Button was Clicked in 2nd try>-".format(color=bcolors.OKGREEN)
					reviews_exists = True
				except Exception as e:
					print "{color}-< Total Reviews could not clicked in 2nd try>-".format(color=bcolors.FAIL)
					try:
						driver.find_element_by_css_selector("a.default-section-title.everyone.active.selected").click()
						print "{color}-< Total Reviews button was already Clicked >-".format(color=bcolors.OKGREEN)
						reviews_exists = True
					except Exception as e:
						# print "hibgb" + str(e)
						# print "{color}-< Total Reviews could not 3 Clicked May be Reviews are less than 5 or Reviews button is already active selected>-".format(color=bcolors.FAIL)
						# pass
						print "{color} -< Reviews are not available>-".format(color=bcolors.WARNING)
						reviews_exists=False
						return "No review to scrape"
						pass
		else:
			# print "{color}-< No review to scrape >-".format(color=bcolors.OKGREEN)
			return "No review to scrape"

		if reviews_exists:
			try:
				no_of_blogs=0
				no_of_blogs = driver.find_element_by_css_selector("a.default-section-title.top.empty").text.split(" ")[1]
				print no_of_blogs
			except Exception as e:
				pass

			limit=int(math.ceil(float(int(self.no_of_reviews_to_be_scrapped))/5))-1
			print "{color}-< load more has to be clicked {num} times>-".format(color=bcolors.WARNING,num=limit)
			for i in xrange(limit):
				try:
					# time.sleep(random.choice(range(5,10)))
					WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "load-more")))
					driver.find_element_by_class_name("load-more").click()
					if i+1!=limit:
						sys.stdout.write("\r {color}-< load more clicked {i_num}/{val} time>- \r".format(color=bcolors.OKGREEN,i_num=i+1,val=limit))
						sys.stdout.flush()
					else:
						sys.stdout.write("{color}-< load more clicked {i_num}/{val} time>- ".format(color=bcolors.OKGREEN,i_num=i+1,val=limit))
						sys.stdout.flush()
					# print "{color} -< load more clicked {i_num}/{val} time>-\r".format(color=bcolors.OKGREEN,i_num=i+1,val=limit),
					if i>=100:
						time.sleep(random.choice(range(3,6)))
					elif i>=180:
						time.sleep(random.choice(range(4,8)))
					elif i>=240:
						time.sleep(random.choice(range(5,9)))
					elif i>=300:
						time.sleep(random.choice(range(9,10)))
					else:
						time.sleep(random.choice(range(2,5)))
				except Exception as e:
					if i+1!=limit:
						try:
							time.sleep(random.choice(range(8,15)))
							driver.find_element_by_class_name("load-more").click()
							if i+1!=limit:
								sys.stdout.write("\r {color}-< load more clicked {i_num}/{val} time>- \r".format(color=bcolors.OKGREEN,i_num=i+1,val=limit))
								sys.stdout.flush()
							else:
								sys.stdout.write("{color}-< load more clicked {i_num}/{val} time>-".format(color=bcolors.OKGREEN,i_num=i+1,val=limit))
								sys.stdout.flush()
							# print "{color} -< load more clicked {i_num}/{val} time>-\r".format(color=bcolors.OKGREEN,i_num=i+1,val=limit),
						except Exception as e:
							if str(e).find("Message: no such element")!=-1:
								print "{color}-< Catching Exception with messege -<No More Loadmore tag present>-  ->".format(color=bcolors.OKGREEN)
							else:
								print "{color}-< Catching Exception -<{error}>- with messege -<No More Loadmore tag present>-".format(color=bcolors.FAIL, error=e)
							break
					else:
						print "{color} <-All Loadmore clicked >-".format(color=bcolors.OKGREEN)
						break
					pass

			if limit==0:
				time.sleep(6)
			read_more_links = driver.find_elements_by_xpath("//div[@class='rev-text-expand']")
			print "{color}\n-< Waiting to click all {val} read more>-".format(color=bcolors.WARNING,val=len(read_more_links))
			i=0
			for link in read_more_links:
				time.sleep(random.choice([2, 3]))
				try:
					link.click()
				except Exception as e:
					pass
				i+=1
				if i!=len(read_more_links):
					sys.stdout.write("\r {color}-< read more clicked {i_num}/{val} time>- \r".format(color=bcolors.OKGREEN,i_num=i,val=len(read_more_links)))
					sys.stdout.flush()
				else:
					sys.stdout.write("{color}-< read more clicked {i_num}/{val} time>-".format(color=bcolors.OKGREEN,i_num=i,val=len(read_more_links)))
					sys.stdout.flush()

			# f=open("mehfil_dhaba_html_2_june_2015.txt","w")
			html_content= driver.page_source
			content = html_content.encode('ascii', 'ignore').decode('ascii')
			# f.write(content)
			# f.close()

			# with open("mehfil_dhaba_html_2_june_2015.txt","r") as content_file:
			# 	content = content_file.read()

			return BeautifulSoup.BeautifulSoup(content)

		else:
			return "No review to scrape"

	def retry_eatery_name(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_name"):
			try:
				self.eatery["eatery_name"] = self.soup.find("h1", {"class": "res-name left"}).find("a").text
			except Exception:
				self.eatery["eatery_name"] = None
		return self.eatery["eatery_name"]
	def eatery_scrapping_year(self):

		self.eatery["eatery_scrapping_year"] = time.localtime().tm_year
	def eatery_scrapping_month(self):

		self.eatery["eatery_scrapping_month"] = time.localtime().tm_mon
	def eatery_scrapping_day(self):

		self.eatery["eatery_scrapping_day"] = time.localtime().tm_mday
	def eatery_area_or_city(self):
		self.eatery["eatery_area_or_city"] = self.eatery.get("eatery_url").split("/")[3]
		return self.eatery["eatery_area_or_city"]
	def retry_eatery_id(self):
		if not self.eatery.get("eatery_id"):
			try:
				self.eatery["eatery_id"] = self.soup.find("div", {"itemprop": "ratingValue"}).get("data-res-id")
			except Exception:
				self.eatery["eatery_id"] = None
		return self.eatery["eatery_id"]
	def retry_eatery_address(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_address"):
			try:
				self.eatery["eatery_address"] = self.soup.find("div", {"class": "res-main-address-text"}).text
			except Exception as e:
				self.eatery["eatery_address"] = None
		return self.eatery["eatery_address"]
	def retry_eatery_cuisine(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_cuisine"):
			try:
				self.eatery["eatery_cuisine"]=self.soup.find("div", {"class": "res-info-cuisines clearfix"}).text
			except Exception:
				self.eatery["eatery_cuisine"] = None

		return self.eatery["eatery_cuisine"]
	def eatery_establishment_type(self):
		try:
			self.eatery["eatery_establishment_type"] = self.soup.findAll("div", {"class": "res-info-cuisines clearfix"})[1].text
		except Exception:
			self.eatery["eatery_establishment_type"] = None

		if self.eatery["eatery_cuisine"].find(self.eatery["eatery_establishment_type"])!=-1:
			self.eatery["eatery_cuisine"]=self.eatery["eatery_cuisine"].split(self.eatery["eatery_establishment_type"])[1]
		return self.eatery["eatery_establishment_type"],self.eatery["eatery_cuisine"]
	def retry_eatery_cost(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_cost"):
			try:
				self.eatery["eatery_cost"] = self.soup.find("span", {"itemprop": "priceRange"}).text
			except Exception:
				self.eatery["eatery_cost"] = None

		return self.eatery["eatery_cost"]
	def retry_eatery_rating(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_rating"):
			try:
				self.eatery["eatery_rating"] = {"rating": self.soup.find("div", {"itemprop": "ratingValue"}).text.split("/")[0],
						"votes": self.soup.find("span", {"itemprop": "ratingCount"}).text}

			except Exception:
				self.eatery["eatery_rating"] = None
		return self.eatery["eatery_rating"]
	def retry_eatery_title(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_title"):
			self.eatery["eatery_title"] = None
		return self.eatery["eatery_title"]
	def retry_eatery_trending(self):
		"""
		This method tries to get the eatery url if the eatery dict supplied doesnt contain eatery name, Which happens
		if we want to scrape only one particular eatery
		"""
		if not self.eatery.get("eatery_trending"):
			try:
				collection =  self.soup.find("div", {"class": "collections_res_container"}).findAll("a")
				self.eatery["eatery_trending"] = [element.text for element in collection]
			except Exception:
				self.eatery["eatery_trending"] = None
		return self.eatery["eatery_trending"]
	def eatery_total_reviews(self):
		try:
			variable = self.soup.find("div", {"class": "res-main-stats-num"})
			self.eatery["eatery_total_reviews"] = variable.text
		except Exception:	
			self.eatery["eatery_total_reviews"] = None
		return self.eatery["eatery_total_reviews"]
	def eatery_highlights(self):
		try:
			self.eatery["eatery_highlights"] = [dom.text.replace("\n", "") for dom in self.soup.findAll("div", {"class": "res-info-feature"})]
		except AttributeError:
			self.eatery["eatery_highlights"] = None
		return self.eatery["eatery_highlights"]
	def eatery_popular_reviews(self):
		try:
			self.eatery["eatery_popular_reviews"] = self.soup.find("li", {"class": "text-tab-link"}).find("span").text
		except AttributeError:
			self.eatery["eatery_popular_reviews"] = None
		return self.eatery["eatery_popular_reviews"]
	def eatery_known_for(self):
		try:
			self.eatery["eatery_known_for"]= self.soup.find("div", {"class": "res-info-known-for-text mr5"}).text
		except Exception:	
			self.eatery["eatery_known_for"] = None
		return self.eatery["eatery_known_for"]
	def eatery_opening_hours(self):
		try:
			line = self.soup.find("div", {"class": "res-week-timetable"}).text
			self.eatery["eatery_opening_hours"]=dict()
			self.eatery["eatery_opening_hours"]["Mon"]=line.split("Mon")[1].split("Tue")[0]
			self.eatery["eatery_opening_hours"]["Tue"]=line.split("Mon")[1].split("Tue")[1].split("Wed")[0]
			self.eatery["eatery_opening_hours"]["Wed"]=line.split("Mon")[1].split("Tue")[1].split("Wed")[1].split("Thu")[0]
			self.eatery["eatery_opening_hours"]["Thu"]=line.split("Mon")[1].split("Tue")[1].split("Wed")[1].split("Thu")[1].split("Fri")[0]
			self.eatery["eatery_opening_hours"]["Fri"]=line.split("Mon")[1].split("Tue")[1].split("Wed")[1].split("Thu")[1].split("Fri")[1].split("Sat")[0]
			self.eatery["eatery_opening_hours"]["Sat"]=line.split("Mon")[1].split("Tue")[1].split("Wed")[1].split("Thu")[1].split("Fri")[1].split("Sat")[1].split("Sun")[0]
			self.eatery["eatery_opening_hours"]["Sun"] =line.split("Mon")[1].split("Tue")[1].split("Wed")[1].split("Thu")[1].split("Fri")[1].split("Sat")[1].split("Sun")[1]
		except AttributeError:
			self.eatery["eatery_opening_hours"] = None
		return self.eatery["eatery_opening_hours"]
	def eatery_metro_stations(self):
		stations = self.soup.findAll("a", {"class": "res-metro-item clearfix left tooltip_formatted-e"})
		try:
			self.eatery["eatery_F_M_Station"] = {"distance": stations[0].find("div", {"class": "left res-metro-distance"}).text,
			 "name": stations[0].find("div", {"class": "left res-metro-name"}).text}
		except Exception as e:
			self.eatery["eatery_F_M_Station"] = None

		try:
			self.eatery["eatery_S_M_Station"] = {"distance": stations[1].find("div", {"class": "left res-metro-distance"}).text, 
					"name": stations[1].find("div", {"class": "left res-metro-name"}).text}
		except Exception:
			self.eatery["eatery_S_M_Station"] = None

		return self.eatery["eatery_S_M_Station"]
	def eatery_recommended_order(self):
		try:
			self.eatery["eatery_should_order"]= self.soup.find("div", {"class": "res-info-dishes-text"}).text
		except AttributeError:
			self.eatery["eatery_should_order"] = None

		return self.eatery["eatery_should_order"]
	def eatery_buffet_price(self):
		try:
			self.eatery["eatery_buffet_price"] = self.soup.find("span", {"class": "res-buffet-price rbp3"}).text
		except AttributeError:
			self.eatery["eatery_buffet_price"] = None
		return self.eatery["eatery_buffet_price"]
	def eatery_buffet_details(self):
		try:
			self.eatery["eatery_buffet_details"] = self.soup.find("span", {"class": "res-buffet-details"}).text
		except AttributeError:
			self.eatery["eatery_buffet_details"] = None
		
		return self.eatery["eatery_buffet_details"]
	def eatery_longitude_latitude(self):
		try:
			# coord = re.findall("\d+.\d+,\d+.\d+", self.soup.find("div", {"id": "res-map-canvas"}).find("img").get("data-original"))
			line = self.soup.find("div",{"class": "resmap-img"}).get("style")
			self.eatery["eatery_coordinates"]= line[line.index("center")+7:line[line.index("center"):].index("&size")+line.index("center")].split(",")
		except AttributeError, TypeError:
			self.eatery["eatery_coordinates"] = None
		return self.eatery["eatery_coordinates"]
	def eatery_total_reviews(self):
		try:
			variable = self.soup.find("div", {"class": "res-main-stats-num"})
			self.eatery["eatery_total_reviews"] = variable.text
		except Exception:
			self.eatery["eatery_total_reviews"] = None
		return self.eatery["eatery_total_reviews"]
	def eatery_reviews(self):
		eatery_area_or_city = self.eatery["eatery_area_or_city"]
		instance = Reviews(self.soup, eatery_area_or_city,int(self.no_of_reviews_to_be_scrapped),int(no_of_blogs))
		self.eatery["reviews"] = instance.reviews_data
		self.eatery["eatery_reviews_in_collection"]=len(self.eatery["reviews"])
		return

def csv_writer(name):
	csvfile = codecs.open('%s.csv'%("-".join(name.split())), 'wb', encoding="utf-8")
	writer = csv.writer(csvfile, delimiter=" ")
	row_one = ['eatery_adddress', 	'eatery_cost', 		'eatery_cuisine', 	'eatery_id', 		'eatery_name', 
			'eatery_F_M_Station', 		'', 		'eatery_S_M_Station', 		'', 		'eatery_highlights', 
			'eatery_buffet_price', 		'eatery_buffet_details', 	'eatery_photos', 	'eatery_should_order', 
			'eatery_popular_reviews', 	'eatery_trending', 		'eatery_opening_hours', 	'eatery_coordinates', 
			'eatery_rating', 	'', 	"eatery_wishlists",	'eatery_title', 	'eatery_url', 		'converted_epoch',
			'eatery_id', 		'review_likes', 	'review_summary', 	'review_text', 		'review_time', 
			'review_url', 		'scraped_epoch', 	'user_followers', 	'user_id', 	'user_name', 
			'user_reviews', 	'user_url',]
	
	row_two = ['', '', '', '', '', 'distance', 'name', 'distance', 'name', '', '', '', '', '', '', '', '', '', 'rating', 'votes', '', '','', '', '','', '', '', '', '', '', '', '', '',]

	writer.writerow(row_one)
	writer.writerow(row_two)
	return (writer, csvfile)

def scrape_links(url, number_of_restaurants, skip, is_eatery):
	"""
	Args:
		url: 
			Url at which the resturants list is present, and is to be scraped 
			example 'http://www.zomato.com/ncr/malviya-nagar-delhi-restaurants"
			and is_eatery=False

			or

			Url of a Particular restaurant is present, and is to be scraped
			example 'https://www.zomato.com/ncr/kylin-premier-vasant-kunj-delhi'
			and is_eatery=True

		number_of_restaurants:
			The number of restaurants to be scraped, In detail, stop_at argument stop the code from scraping more restaurants 
			by going on the pagination links, And one page has around 30 restaurants, so even if you set stop_at at 1, it will still 
			have 30 restaurants or more, So to stop the code to scrape reviews of restaurants, number of restaurants is used.
			So for example if you set number of restaurants = 2, The code will scrape all the reviews and details of only two 
			restaurants

		skip: If you know how many restaurants has already been scraped then you can enter that number to skip that
			number of restaurants, and then their details and reviews will not be scraped

	Returns:
		a list of restaurants dictionaries with their details required and the review list:
		The keys included in one restaurant doictionary are as follows
		
	"""
	if not skip:
		skip = 0
	
	if not number_of_restaurants:
		number_of_restaurants = 0

	# global driver

	# driver = webdriver.PhantomJS(executable_path="/home/shubhanshu/Review/Reviews/phantomjs/bin/phantomjs")
	# driver.set_window_size(1024,720)


	# path_to_chromedriver = '/home/shubhanshu/selenium/chromedriver'
	# driver = webdriver.Chrome(executable_path = path_to_chromedriver)

	# print "{color} There are the number of restaurants {0} and skip is {1}".format(int(number_of_restaurants), int(skip),color=bcolors.OKBLUE)

	instance = EateriesList(url, int(number_of_restaurants), int(skip), is_eatery)

	eateries_list = instance.prepare_and_return_eateries_list()

	eatery_count=0

	final_eateries_list=list()

	review_collection = collection("review")
	eatery_collection = collection("eatery")


	for one_eatery_dict in eateries_list:
		eatery_count+=1
		# eatery_count=0
		# for one_eatery_dict in eateries_list:
		"""Checking How many reviews are present of the above eatery_id
		in the review collection and if the no. is less than the eatery_total_reviews
		Then only that eatery has to be scrpped and forwarded to eatery_specific

		Which means that if all the reviews of the eatery have been scrapped than 
		no need to do it again
		"""
		try:
			if eatery_collection.find({"eatery_id":one_eatery_dict["eatery_id"]}).count()==0:
				final_eateries_list.append([one_eatery_dict,one_eatery_dict["eatery_total_reviews"],eatery_count])
			else:
				print "\n {color} <----------Scrapping Eatery {val}---------->".format(color=bcolors.HEADER,val=eatery_count)
				print "{color} -< {val1} Already in eatery collection, eatery_id =  {val2}>-".format(color=bcolors.OKGREEN,val1=one_eatery_dict["eatery_name"],val2=one_eatery_dict["eatery_id"])
				try:
					reviews_in_collection = review_collection.find({"eatery_id":one_eatery_dict["eatery_id"]}).count()
					if int(reviews_in_collection)<int(one_eatery_dict["eatery_total_reviews"]):
						no_of_reviews_to_be_scrapped = int(one_eatery_dict["eatery_total_reviews"]) - int(reviews_in_collection)
						if no_of_reviews_to_be_scrapped!=0:
							final_eateries_list([one_eatery_dict,no_of_reviews_to_be_scrapped,eatery_count])
						# self.eatery_specific(one_eatery_dict,no_of_reviews_to_be_scrapped)
					else:
						print "{color} -<reviews in collection are equal to the eatery reviews>-".format(color=bcolors.OKGREEN)
				except Exception as e:
					print str(e)
		except Exception as e:
			print str(e)

	return final_eateries_list

def eatery_specific(eatery_dict,no_of_reviews_to_be_scrapped,eatery_count):
	if no_of_reviews_to_be_scrapped=="check":
		print "\n {color} <-Scrapping Single Eatery >-".format(color=bcolors.HEADER)
	else:
		print "\n {color} <----------Scrapping Eatery {val}---------->".format(color=bcolors.HEADER,val=eatery_count)

	try:
		print "{color}Opening Eatery--<{eatery}> with url --<{url}>\n".format(color=bcolors.HEADER, eatery=eatery_dict.get("eatery_name"), url=eatery_dict.get("eatery_url"))
	except Exception:
		print "{color}Eatery url --<{url}>\n".format(color=bcolors.HEADER, url=eatery_dict.get("eatery_url"))

	##If the eatery is already present then there is no need to scrape it again
	##Here we check on the basis of url because it might be a possibility that we want to scrape eatery on the basis of url and in 
	#that case eatery id may not be present in the database

	print "{color} -<Waiting For Eatery Page To Load>-".format(color=bcolors.WARNING)

	instance = EateryData(eatery_dict,no_of_reviews_to_be_scrapped,got_soup=False,soup_for_test_case=None)

	if instance.soup != "No review to scrape" and instance.soup!=None:
		#eatery_modified_list.append(dict([(key, value) for key, value in instancsoup_for_test_casee.eatery.iteritems() if key.startswith("eatery")]))
		#reviews_list.extend(instance.eatery.get("reviews"))

		count=0
		print "{color} \n-<review insertion STARTING>-".format(color=bcolors.WARNING)
		reviews = instance.eatery.get("reviews")
		count=DBInsert.db_insert_reviews(reviews)
		print "{color}-<review insertion COMPLETE>-".format(color=bcolors.OKGREEN)

		eatery_modified = dict([(key, value) for key, value in instance.eatery.iteritems() if key.startswith("eatery")])
		try:
			eatery_modified["eatery_reviews_in_collection"] += count
		except Exception:
			eatery_modified["eatery_reviews_in_collection"] = count
		# print count,instance.no_of_reviews_to_be_scrapped

		if int(count)<int(instance.last_no_of_reviews_to_be_scrapped):

			print "{color}\n Reviews inserted Successfully = {val}".format(color=bcolors.FAIL,val=count)
			print "{color} Reviews had to scrape         = {val}".format(color=bcolors.FAIL,val=instance.last_no_of_reviews_to_be_scrapped)

			print "{color}\n I think something went wrong. Saving the eatery_url to scrape again and deleting inserted reviews".format(color=bcolors.FAIL)

			f=open("links_to_be_rescrape.txt","a")
			f.write(str(eatery_modified["eatery_url"])+",")
			f.close()

			DBInsert.db_delete_reviews(eatery_modified["eatery_id"])
			DBInsert.db_delete_eatery(eatery_modified["eatery_id"])
			reviews=[]

		else:
			print "{color}\n Reviews inserted Successfully = {val}".format(color=bcolors.OKGREEN,val=count)
			print "{color} Reviews had to scrape         = {val}".format(color=bcolors.OKGREEN,val=instance.last_no_of_reviews_to_be_scrapped)
			print "{color} \n-<eatery insertion STARTING>-".format(color=bcolors.WARNING)
			eatery_collection = collection("eatery")
			DBInsert.db_insert_eateries(eatery_modified)
			print "{color}-<eatery insertion COMPLETE>-".format(color=bcolors.OKGREEN)
			
		#Creating csvfile with the name of eatery name
		#writer = csv_writer(eatery_modified.get("eatery_name"))[0]
		#csvfile = csv_writer(eatery_modified.get("eatery_name"))[1]

		# It was applicable for the metro stations but now we are not fetchind nearby metro stations info	
		# station = lambda x : (x.get("name"), x.get("distance")) if x else (None, None)

		# eatery_row = [eatery_modified.get('eatery_adddress'), eatery_modified.get('eatery_cost'), eatery_modified.get('eatery_cuisine'), 
		# 		eatery_modified.get('eatery_id'), eatery_modified.get('eatery_name'), 
		# 		station(eatery_modified.get("eatery_F_M_Station"))[1], 
		# 		station(eatery_modified.get("eatery_F_M_Station"))[0],
		# 		station(eatery_modified.get("eatery_S_M_Station"))[1], 
		# 		station(eatery_modified.get("eatery_S_M_Station"))[0],
		# 		eatery_modified.get("eatery_highlights"), eatery_modified.get("eatery_buffet_price"),
		# 		eatery_modified.get("eatery_buffet_details"), eatery_modified.get("eatery_photos"),
		# 		eatery_modified.get("eatery_should_order"), eatery_modified.get("eatery_popular_reviews"), 
		# 		eatery_modified.get("eatery_trending"), eatery_modified.get("eatery_opening_hours"), 
		# 		eatery_modified.get("eatery_coordinates"), eatery_modified.get('eatery_rating').get('rating'), 
		# 		eatery_modified.get("eatery_rating").get('votes'), eatery_modified.get('eatery_title'), 
		# 		eatery_modified.get("eatery_wishlist"), eatery_modified.get('eatery_url'), 
		# 		eatery_modified.get('converted_to_epoch'),eatery_modified.get('eatery_id')]

		#Modified eatery_row

		# eatery_row = [eatery_modified.get('eatery_adddress'),eatery_modified.get('eatery_cost'),eatery_modified.get('eatery_cuisine'), 
		# 		eatery_modified.get('eatery_id'),
		# 		eatery_modified.get('eatery_name'),
		# 		eatery_modified.get("eatery_highlights"),
		# 		eatery_modified.get("eatery_popular_reviews"),
		# 		eatery_modified.get("eatery_opening_hours"), 
		# 		eatery_modified.get("eatery_coordinates"),
		# 		eatery_modified.get('eatery_rating').get('rating'), 
		# 		eatery_modified.get("eatery_rating").get('votes'), 
		# 		eatery_modified.get("eatery_wishlist"),
		# 		eatery_modified.get('eatery_url'), 
		# 		eatery_modified.get('converted_epoch'),
		# 		eatery_modified.get('eatery_id')]

		#writer.writerow(eatery_row)

		"""
		if eatery_collection.find_one({"eatery_id": eatery_dict.get("eatery_id")}):
			print "\n {color} The Eatery with the url --<{url} has already been scraped>\n".format(color=bcolors.WARNING, url=eatery_dict.get("eatery_url"))
			return
			"""

		if reviews!=[]:
			print "{color} \n-<user inserton STARTING>-".format(color=bcolors.WARNING)
			users_list = list()
			for review in  reviews:
				text = review.get("review_text")
				name = review.get("user_name")
				
				try:	
					review["review_text"] = text.decode("ascii", "ignore")
				except Exception:
					review["review_text"] = ''

				try:	
					review["user_name"] = name.decode("ascii", "ignore")
				except Exception:
					review["user_name"] = ''

				review_append = ["" for i in range(0, 22)]
				review_append.extend([value for key, value in review.iteritems()])
				#print review_append
				#writer.writerow(review_append)
				
				users = dict([(key, value) for key, value in review.iteritems()])
				users_list.append(users)
			DBInsert.db_insert_users(users_list)	
			print "{color}-<user inserton COMPLETE>-".format(color=bcolors.OKGREEN)
		return

	else:
		# print "{color} -<Worked Fine -<No review to scrape>-".format(color=bcolors.OKGREEN)
		print "\n {color} This eatery has no review to be scrapped>\n".format(color=bcolors.OKGREEN)
		return

if __name__ == "__main__":

	# start = timeit.default_timer()

	global driver
	# path_to_chromedriver = '/home/shubhanshu/selenium/chromedriver'
	# driver = webdriver.Chrome(executable_path = path_to_chromedriver)
	driver = webdriver.PhantomJS(executable_path="/home/shubhanshu/Review/Reviews/phantomjs/bin/phantomjs")
	driver.set_window_size(1024,720)

	"""If you want to scrape a particular restaurant do this"""
	"""Worked fine on Mon Jun 4 16:45:42 2015"""
	# url = "https://www.zomato.com/bangalore/jive-pub-1-indiranagar" 310078
	# url="https://www.zomato.com/ncr/bunker-dlf-phase-4-gurgaon"
	# number_of_restaurants = 0
	# skip = 0
	# is_eatery = True
	# scrape_links(url, number_of_restaurants, skip, is_eatery)
	# print "{color} \n-< Done>-".format(color=bcolors.ENDC)

	"""If you want to scrape with the big area name like ncr or bangalore...
	Do This"""
	"""Worked fine on Mon Jun 2 16:28:42 2015"""
	# url = "https://www.zomato.com/ncr"
	# driver.get(url)
	# time.sleep(10)
	# big_area_dict = list()
	# html_content= driver.page_source
	# content = html_content.encode('ascii', 'ignore').decode('ascii')
	# soup = BeautifulSoup.BeautifulSoup(content)

	# # with open("one_big_area_(bangalore)_html_2_june_2015.txt","r") as content_file:
	# # 	content = content_file.read()
	# # 	soup = BeautifulSoup.BeautifulSoup(content)

	# hidden = soup.find("div",{"class":"mob-slide row n-container"})

	# hd2=hidden.findAll("a",{"class":"col-s-16 "})
	# for element in hd2:
	# 		big_area_dict.append({"area_url":element["href"],"area_name":element.text[:element.text.index("  ")],"area_restaurents_count":int(element.text.split("(")[-1][:-1])})
	# # print big_area_dict
	# for area in big_area_dict:
	# 	print area["area_url"]
	# 	break
		# scrape_links(area["area_url"], number_of_restaurants=30, skip=0, is_eatery= False)

	"""And If You want to scrape a local area then
	Do This"""
	"""Worked fine on Mon Jun 2 14:28:42 2015"""
	# number_of_restaurants = 30
	# skip = 0
	# is_eatery = False
	# url = "https://www.zomato.com/ncr/sector-39-gurgaon-restaurants"
	# # url  = "https://www.zomato.com/ncr/munirka-delhi-restaurants"
	# scrape_links(url, number_of_restaurants, skip, is_eatery)
	# print "{color}-< Done >-".format(color=bcolors.OKGREEN)

	"""And If You want to scrape a particular page of local area then
	Do This"""
	"""Worked fine on Mon Jun 2 14:28:42 2015"""

	number_of_restaurants = 30
	skip = 0
	is_eatery = False
	url = "https://www.zomato.com/ncr/south-delhi-restaurants?page=20"
	finale=scrape_links(url, number_of_restaurants, skip, is_eatery)

	for item in finale:
		eatery_specific(item[0],item[1],item[2])
	# print "{color} -< Done>-".format(color=bcolors.ENDC)

	with open("links_to_be_rescrape.txt","r+") as f:
		url_list=f.read().split(",")[:-1]

	with open("links_to_be_rescrape.txt","w") as fil:
		fil.write("")

	if url_list!=[]:
		print "{color} -<Total {val} eateries has to be rescrapped>-".format(color=bcolors.WARNING,val=len(url_list))
		for url in url_list:
			number_of_restaurants = 0
			skip = 0
			is_eatery = True
			scrape_links(url, number_of_restaurants, skip, is_eatery)
	else:
		print "{color} -<Total {val} eateries has to be rescrapped>-".format(color=bcolors.WARNING,val=len(url_list))
	
	print "{color} -< Done>-".format(color=bcolors.ENDC)

	end = timeit.default_timer()

	driver.close()

	print "{color} -<This Complete script took {val} seconds>-".format(color=bcolors.WARNING,val=end-start)
	# Tue May 19 14:04:45 IST 2015

	"""Some Old code"""
	# for element in eateries_list:
	# 	eatery_specific(element)
	# instance = EateriesList(url, int(number_of_restaurants), int(skip),is_eatery)
	# eateries_list = instance.eateries_list()
	# print eateries_list
        #   scrape("http://www.zomato.com/ncr/malviya-nagar-delhi-restaurants?category=1", 30, 18) 
	###This is the right one for element in scrape_links("https://www.zomato.com/ncr/south-delhi-restaurants", 30, 30):
	# print element.get("eatery_name")
		
		#	scrape("http://www.zomato.com/ncr/khan-market-delhi-restaurants?category=1", 28, 1)
        #runn.apply_async(["https://www.zomato.com/ncr/south-delhi-restaurants", 30, 520]), this has been done for south delhi


        #Sun Sep  7 13:31:10 IST 2014
        #https://www.zomato.com/ncr/zee-restaurant-vijay-nagar-new-delhi