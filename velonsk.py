# -*- coding: utf-8 -*-
import jinja2
import os

import webapp2
import logging
import generalcounter
import json
import math
import re

from datetime import datetime, timedelta

from my_restore import restore_video, restore_images, restore_refs, format_cutheader

from velo_cache import *
from data_model import *
from my_timedelta import *
import velo_fetch

def format_datetime_delta(value):
	return format_timedelta(datetime.now() - value + timedelta(hours=7), value)
		
def get_pages_header(page_num, max_page_num):
	ret = []
	if page_num>1:
		ret.append({'num' : 1, 'name': u'первая'})
	if page_num>2:
		ret.append({'num' : (page_num-1), 'name': u'предыдущая'})
	
	first_pages = 3
	if first_pages>= page_num-3:
		first_pages = page_num-4
	for page in range(1, first_pages+1):
		ret.append({'num' : page, 'name': page})
	if first_pages + 1 < page_num-3:
		ret.append({'num' : 0, 'name': "..."})
	

	first_pages=page_num-3;
	if first_pages<1:
		first_pages=1;
	for page in range(first_pages, page_num):
		ret.append({'num' : page, 'name': page})
	  
	ret.append({'num' : 0, 'name': page_num})

	last_page = page_num+3;
	if last_page>max_page_num:
		last_page = max_page_num;
	for page in range(page_num+1, last_page+1):
		ret.append({'num' : page, 'name': page})
	
	if last_page<max_page_num-3:
		ret.append({'num' : 0, 'name': "..."})
	if last_page<max_page_num:
		last_page2 = max_page_num - 2
		if last_page2<last_page:
			last_page2 = last_page + 1
		for page in range(last_page2, max_page_num + 1):
			ret.append({'num' : page, 'name': page})
	
	if page_num<(max_page_num-1):
		ret.append({'num' : (page_num+1), 'name': u'следующая'})
	if page_num<max_page_num:
		ret.append({'num' : max_page_num, 'name': u'последняя'})
	return ret

def get_pages_line(max_page_num):
	ret = []
	if max_page_num > 3:
		first_pages = 3
	else: 
		first_pages = max_page_num - 1
	
	for page in range(1, first_pages+1):
		ret.append({'num' : page, 'name': page})
	
	if (max_page_num -1) > first_pages:
		last_pages = max_page_num - 2
		if last_pages > first_pages:
			ret.append({'num' : 0, 'name': '...'})
		else:
			last_pages = first_pages+1
		
		for page in range(last_pages,max_page_num):
			ret.append({'num' : page, 'name': page})
	ret.append({'num' : max_page_num, 'name': str(max_page_num) + u' последняя'})
	return ret;

		
jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')))
jinja_environment.filters['timedelta'] = format_datetime_delta 
jinja_environment.filters['cutheader'] = format_cutheader 
	

def get_post_title(p_title, p_text):
	title = clear_post_title(p_title)
	if title:
		return p_title
	return p_text
	
def limit_range(p_value, p_min, p_max):
	if p_value < p_min:
		return p_min
	if p_value > p_max:
		return p_max
	return p_value

class RefreshForumTopics(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		forums = get_forums_cache()
		for forum_item in forums:
			velo_fetch.fetch_forum_topics(forum_item.forum_key)	  
		self.response.out.write("OK")  

class RefreshForums(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		velo_fetch.fetch_forums()	  
		self.response.out.write("OK")		

		
class RefreshTopicFromQueue(webapp2.RequestHandler):
	def post(self):
		logging.debug("Starting RefreshTopicsFromQueue")
		self.response.headers['Content-Type'] = 'text/plain'
		forum_key = self.request.get('forum_key')
		topic_id = self.request.get('topic_id')
		topic_name = self.request.get('topic_name')
		topic_posts = int(self.request.get('topic_posts'))
		logging.debug("updating topic %s.%s %s", forum_key, topic_id, topic_name)
		forum = get_forum_cache(forum_key, False);
		if forum.forum_topics is None:
			logging.error("error retrieving forum %s",forum_key)
		else:
			topic = get_topic_cache(topic_id, True)
			if topic.topic_posts is None:
				logging.debug("new topic")
				topic.topic_true_posts = 0
				topic.forum_key = forum_key
				topic.topic_id = topic_id
				topic.topic_name = topic_name
				forum.forum_topics += 1
			topic.topic_posts = topic_posts
			velo_fetch.get_posts(self,forum_key, topic_id, forum, topic)
			put_topic_cache(topic)
			put_forum_cache(forum)
		
		logging.debug("  deleting topic %s from queue", topic_id)
		del_from_topics_queue(forum_key,topic_id)
		
		self.response.out.write("OK")		
		
	
class MainPage(webapp2.RequestHandler):
	def get(self):
		forums = get_forums_cache()
		template_values = {'forums': forums}
		template = jinja_environment.get_template('index.html')
		self.response.out.write(template.render(template_values))

class ViewForum(webapp2.RequestHandler):
	def get(self, p_forum_key):
		forums = get_forums_cache()
		cur_forum = None
		options = get_options_cache()
		for forum_item in forums:
			if forum_item.forum_key == p_forum_key:
				cur_forum = forum_item
		if cur_forum is None:
			self.response.out.write("Forum, " + p_forum_key + " not found")
		else:
			max_page_num = int(math.ceil(cur_forum.forum_topics/float(options.topics_per_page)))
			page_num = self.request.get_range("p", min_value=1, max_value=max_page_num, default=1)
			page_num = limit_range(page_num, 1, max_page_num)
			topics_query = Topic.all()
			topics_query.filter("forum_key =",p_forum_key)
			topics_query.order("-topic_last_post_date")
			topics = topics_query.fetch(limit=options.topics_per_page, offset=((page_num-1)*options.topics_per_page))
			for topic_item in topics:
				topic_item.topic_views = generalcounter.get_count(topic_item.topic_id)
				topic_item.max_page_num = int(math.ceil(topic_item.topic_true_posts/float(options.posts_per_page)))
				topic_item.pages = get_pages_line(topic_item.max_page_num)
			template_values = {'forums': forums, 'topics' : topics, 'cur_forum':cur_forum, 'page_num':page_num, 'max_page_num':max_page_num, 'pages':get_pages_header(page_num, max_page_num)}
			template = jinja_environment.get_template('viewforum.html')
			self.response.out.write(template.render(template_values))
		

def get_post_by_num(p_list, p_num):
	for p in p_list:
		if p['post_num'] == p_num:
			return p
	
def get_quote_text(p_post):
	rez_text = p_post['post_text']
	if p_post['post_title'] != u'ответ' and p_post['post_title'] != u'ни о чем':
		rez_text = p_post['post_title'] + '[br]' +rez_text
	rez_text = rez_text.replace('[br]','<br />')
	rez_text = restore_video(rez_text, 1)
	rez_text = restore_images(rez_text, 1)
	rez_text = restore_refs(rez_text)
	return rez_text
	
class ViewTopic(webapp2.RequestHandler):
	def get(self, p_forum_key, p_topic_id, p_page = 1):
		cur_topic = get_topic_cache(p_topic_id, False)
		options = get_options_cache()
		if cur_topic:
			forums = get_forums_cache()
			for forum_item in forums:
				if forum_item.forum_key == cur_topic.forum_key:
					cur_forum = forum_item
			if cur_forum:
				generalcounter.increment(p_topic_id)
				max_page_num = int(math.ceil(cur_topic.topic_true_posts/float(options.posts_per_page)))
				page_num = self.request.get_range("p", min_value=1, max_value=max_page_num, default=1)
				page_num = limit_range(page_num, 1, max_page_num)
				first_post_num = (page_num - 1)*options.posts_per_page + 1
				last_post_num = page_num*options.posts_per_page

				posts_list = json.loads(cur_topic.topic_posts_text, 'windows-1251')
				posts = []
				post_cnt = 0
				for post in posts_list:
					post_cnt = post_cnt + 1
					if post_cnt>=first_post_num and post_cnt<=last_post_num:
						new_post = post.copy()
						post_text = post['post_text']
						post_text = post_text.replace('[br]','<br />')
						# выделим видео
						post_text = restore_video(post_text, 0)
						# выделим картинки
						post_text = restore_images(post_text, 0)
						# выделим сцылки
						post_text = restore_refs(post_text)
						new_post['post_text'] = post_text
						new_post['post_title'] = restore_video(new_post['post_title'], 0)
						new_post['post_title'] = restore_images(new_post['post_title'], 0)
						new_post['post_title'] = restore_refs(new_post['post_title'], 0)
						
						post_parent_num = post['parent_post']
						post_num = post['post_num']
						
						
						if post_parent_num != post_num-1:
							parent_post = get_post_by_num(posts_list, post_parent_num)
							new_post['post_quote'] = get_quote_text(parent_post)
							new_post['post_quote_author'] = parent_post['author_name']
						posts.append(new_post)
				template_values = {'forums': forums, 'cur_forum':cur_forum, 'posts' :posts, 'cur_topic':cur_topic, 'page_num':page_num, 'max_page_num':max_page_num, 'pages':get_pages_header(page_num, max_page_num)}
				template = jinja_environment.get_template('viewposts.html')
				self.response.out.write(template.render(template_values))
			else:
				self.response.out.write("Forum, " + cur_topic.forum_key + " not found")
		else:
			self.response.out.write("Topic, " + p_topic_id + " not found")
		
app = webapp2.WSGIApplication([('/', MainPage),
							   ('/refresh', RefreshForumTopics),
							   ('/refreshforums', RefreshForums),
							   ('/refreshtopic', RefreshTopicFromQueue),
							   ('/([^/]+)/?', ViewForum),
							   ('/([^/]+)/([^/]+)/?', ViewTopic),
							   ('/([^/]+)/([^/]+)/([^/]+)/?', ViewTopic)],
							  debug=True)