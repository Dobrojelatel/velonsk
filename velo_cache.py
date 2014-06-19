import logging
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache 
from data_model import *

def clear_post_title(p_title):
	if p_title == u'ответ':
		return ""
	elif p_title == u'ни о чем':
		return ""
	return p_title
	
def forum_key(forum_code):
	return db.Key.from_path('Forum',forum_code)
 
def topic_key(topic_code):
	return db.Key.from_path('Topic',topic_code)

			
def get_options_cache():
	options = memcache.get('options')
	if options is None:
		logging.debug("retrieving options from datastore")
		options_query = Options.all()
		options_lst = options_query.fetch(1)
		for options_item in options_lst:
			memcache.set('options', options_item)
			return options_item
		options = Options()
		options.topics_per_page = 20
		options.posts_per_page = 50
		options.put()
		memcache.set('options', options)
		return options
	else:
		return options

def get_forums_cache():
	forums = memcache.get('forums_array')
	if forums is None:
		logging.debug("retrieving forums from datastore")
		forums_query = Forum.all()
		forums_query.order('forum_order')
		forums = forums_query.fetch(20)
		memcache.set('forums_array', forums) 
	return forums
		
def get_topic_cache(p_topic_id, p_create):
	logging.debug("get_topic_cache %s", p_topic_id)
	topic = memcache.get('topic_'+p_topic_id)
	if topic is None:
		topic = Topic.get_by_key_name(p_topic_id)
		if not topic is None:
			memcache.set("topic_"+p_topic_id,topic)
			logging.debug("got topic %s from datastore",p_topic_id)
		else:
			if p_create:
				topic = Topic(key_name = p_topic_id)
				logging.debug("created topic %s",p_topic_id)
	else:
		logging.debug("got topic %s from cache", p_topic_id)
	return topic
	
def put_topic_cache(p_topic):
	p_topic.put()
	memcache.set("topic_"+p_topic.topic_id, p_topic)
	
def get_forum_cache(p_forum_key, p_create_new):
	forums = get_forums_cache()
	for forum_item in forums:
		if forum_item.forum_key == p_forum_key:
			logging.debug("got forum %s from cache",p_forum_key)
			return forum_item
	if p_create_new:
		logging.debug("creating new forum %s", p_forum_key)
		return Forum(key_name = p_forum_key)

def put_forum_cache(p_forum):
	p_forum.put()
	forums = get_forums_cache()
	new_forums = []
	found = False 
	for forum_item in forums:
		if forum_item.forum_key == p_forum.forum_key:
			new_forums.append(p_forum)
			found = True
		else:
			new_forums.append(forum_item)
	if not found:
		new_forums.append(p_forum)
	memcache.set('forums_array', new_forums)
	
def add_to_topics_queue(p_forum_key, p_topic_id, p_topic_name, p_topic_posts):
	topic_queue = memcache.get("topic_queue:"+p_forum_key+","+p_topic_id);
	if topic_queue is None:
		taskqueue.add(queue_name='topic-fetch-queue', url='/refreshtopic', params={'forum_key': p_forum_key, 'topic_id': p_topic_id, 'topic_name' : p_topic_name, 'topic_posts' : p_topic_posts})
		logging.debug("adding to topics queue")
		memcache.set("topic_queue:"+p_forum_key+","+p_topic_id,"1")
	else:
		logging.debug("already in topics queue (cache)")
		
def del_from_topics_queue(p_forum_key,p_topic_id):
	memcache.delete("topic_queue:" + p_forum_key + "," + p_topic_id)