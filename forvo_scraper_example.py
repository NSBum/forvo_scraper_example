#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait

import urllib.parse
import re
import os
from bs4 import BeautifulSoup, element

import time
import base64
from functools import total_ordering
from typing import Optional
import argparse

__version__ = '1.0'

DEBUG = False

FAVS = ['1640max', 'Spinster', 'szurszuncik', 'ae5s', 'Shady_arc', 'zhivanova', 'Selene71']

@total_ordering
class Pronunciation(object):
	def __init__(self, uname:str, positive: int, path: str):
		self.user_name = uname
		self.positive: int = positive
		self.path: str = path
		
	@property
	def score(self) -> int:
		subscore = 0
		if self.user_name in FAVS:
			subscore = 2
		return self.positive + subscore
	
	def __eq__(self, other):
		if not isinstance(other, type(self)): return NotImplemented
		return self.score == other.score
	
	def __lt__(self, other):
		if not isinstance(other, type(self)): return NotImplemented
		return self.score < other.score
	
	
	def __str__(self):
		return f'Pronunciation object: {self.user_name} - {self.positive}'
	
	def __repr__(self):
		return self.__str__()
	
def ogg_fn(word: str) -> str:
	"""Filename for the retrieved .off file
	
	word: str - word to use as filename

	Returns
	-------
	Filename of the .ogg file
	"""
	return f'{word}.ogg'
	
def retrieve_ogg(url: str, dst: str):
	"""Retrieves file from url, saving to destination

	url: str - the remote file to retrieve
	dst: str - the local filesystem path to save
	"""
#    urllib.request.urlretrieve(url, dst)
	url_request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
	response = urllib.request.urlopen(url_request)
	with open(dst, 'b+w') as fh:
		fh.write(response.read())

def forvo_url(word: str) -> str:
	"""URL for Forvo word
	
	word: str - the Russian word to research

	Returns
	-------
	URL for the Forvo pronunciations page (Russian)
	"""
	word = urllib.parse.quote(word)
	url = f'https://forvo.com/word/{word}/#ru'
	return url

def get_forvo_page(url: str) -> BeautifulSoup:
	"""Get the bs4 object from Forvo page
	
	url: str - the Forvo pronunciation page

	Returns
	-------
	BeautifulSoup 4 object for the page
	"""
	driver = webdriver.Safari()
	driver.get(url)
	driver.implicitly_wait(30)
	agree_button = driver.execute_script("""return document.querySelector("button[mode='primary']");""")
	try:
		agree_button.click()
	except AttributeError:
		pass
	try:
		close_button = driver.execute_script("""return document.querySelector("button.mfp-close");""")
		close_button.click()
	except AttributeError:
		pass
	time.sleep(1)
	soup = BeautifulSoup(driver.page_source, 'html.parser')
	return soup


def get_forvo_soup_word(word: str) -> BeautifulSoup:
	"""Get bs4 object for given Russian word
	
	word (str) - the word to research

	Returns
	-------
	Beautiful Soup 4 object for the pronunciation page for this word
	"""
	url = forvo_url(word)
	return get_forvo_page(url)

def user_from_info_span(element: element.Tag) -> str:
	"""Derive user from HTML element
	
	Username for a given list item resides in a particular span. This function
	extracts the user from that span.

	element (bs4.element.Tag) - the span containing user

	Returns
	-------
	User name as str
	"""
	clean_text = re.sub(r'\s{1,}', r" ", element.text)
	user = re.sub(r'\s+Pronunciation\s+by\s+(\w+)', r"\1", clean_text)
	return user

def num_votes_from_vote_span(element: element.Tag) -> int:
	"""
	Number of votes for this pronunciation from containing span

	A particular span element contains the vote count. Given that
	element, return the integer count of votes
	
	element (bs4.element.Tag) - the span containing the vote count

	Returns
	-------
	The integer count of votes for this pronunciation.
	"""
	try:
		clean_vote_text = re.sub(r'\s{1,}', r" ", element[0].text).strip()
	except IndexError:
		print(element)
		return 0
	votes = re.sub(r'(\d+)\s+vote[s]', r"\1", clean_vote_text)
	return int(votes)

def num_votes_from_li(element: element.Tag) -> int:
	"""Number of votes for the pronunciation in a given row

	Extracts the vote count from a given <li>

	element (bs4.element.Tag) - the <li> item that for this pronunciation

	Returns
	-------
	The integer count of votes for this pronunciation
	"""
	span = element.select('span.num_votes > span')
	return num_votes_from_vote_span(span)

def get_audio_link(onclickFunction: str) -> str:
	"""Extract an audio download link from the play button js
	
	onclickFunction (str) - the js for the play button

	Returns
	-------
	Decoded download link for the audio file
	"""
	# from Anki-Simple-Forvo-Audio
	# https://github.com/Rascalov/Anki-Simple-Forvo-Audio
	base64audio = onclickFunction.split(',')[2].replace('\'', "")
	decodedLink = base64.b64decode(base64audio.encode('ascii')).decode('ascii')
	return "https://audio00.forvo.com/ogg/" + decodedLink

def audio_link_for_li(element: element.Tag) -> Optional[str]:
	"""Audio download link for pronunciation <li> item
	
	Given the pronunciation list element, try to extract its
	download link.

	element (bs4.element.Tag) - the <li> item for this pronunciation

	Returns
	-------
	Decoded download link for the audio file
	"""
	play_div = element.find("div", {"class": "play"})
	if play_div is not None:
		oc_function = play_div["onclick"]
		url = get_audio_link(oc_function)
		return url
	return None

def pronunciation_for_li(element: element.Tag) -> Optional[Pronunciation]:
	"""Pronunciation object from its <li> element

	Returns an optional Pronunciation object from a
	<li> element that contains the required info.

	Returns
	-------
	Pronunciation object, or None
	"""
	info_span = element.find("span", {"class": "info"})
	if info_span is not None:
		user = user_from_info_span(info_span)
	votes = num_votes_from_li(element)
	url = audio_link_for_li(element)
	if url is not None:
		pronunciation = Pronunciation(user, votes, url)
		return pronunciation
	return None

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser = argparse.ArgumentParser(prog="Download pronunciation file from Forvo")
	parser.add_argument('--dest',
						help="The directory for download",
						type=str)
	parser.add_argument('--word',
						help="Word to research",
						type=str)
					
	if DEBUG:
		word = "товарищество"
		dest = '/Users/alan/Documents/mp3'
		
	# Parse the command line arguments
	args = parser.parse_args()
	word = args.word
	dest = args.dest
	
	# fixed erronuous й encoding
	word = word.replace(u"\u0438\u0306", u"\u0439")
	
	soup = get_forvo_soup_word(word)
	ru_pronunciation_list = soup.find("ul", {"id": "pronunciations-list-ru"})
	if ru_pronunciation_list is None:
		exit('ERROR - this word may not exist on Forvo!')
		
	pronunciations = []
	for li in ru_pronunciation_list.find_all("li"):
		pronunciation = pronunciation_for_li(li)
		if DEBUG:
			print(pronunciation)
		pronunciations.append(pronunciation)
		
	use_p  = max(pronunciations) if len(pronunciations) > 1 else pronunciations[0]
	
	save_path = os.path.join(dest, ogg_fn(word))
	retrieve_ogg(use_p.path, save_path)
