import logging
import re
import json
from google.appengine.api import urlfetch
from datetime import datetime, timedelta
from velo_cache import *
from my_restore import isolate_video, isolate_images, isolate_refs, format_cutheader

def get_post_dict(p_post_num, p_post_date, p_author_name, p_author_key, p_post_title, p_post_text, p_parent_post):
	return dict(post_num = p_post_num, post_date = p_post_date, author_name = p_author_name, author_key = p_author_key, post_title = p_post_title, post_text = p_post_text, parent_post = p_parent_post)

def fetch_forums():
	logging.debug("Starting fetch_forums")
	nMatches = 1
	url = "http://velo.nsk.ru/spall/"
	result = urlfetch.fetch(url)
	logging.debug("  urlfetch done %s", url)
	if result.status_code == 200:
		logging.debug("fetch ok")
		grab = result.content.decode('windows-1251')
	else:
		logging.error("error retrieving url %s",url)
	matches = re.findall("index.php\?action=view_forum&param\[forum\]=([^']+)'>([^<]+)",grab)
	nMatches = len(matches)
	order = 1
	for match in matches:
		nsk_forum_id = match[0]
		nsk_forum_name = match[1]
		forum = get_forum_cache(nsk_forum_id, True)
		if forum.forum_topics is None:
			logging.info("filling attributes of new forum %s",nsk_forum_id)
			forum.forum_name=  nsk_forum_name
			forum.forum_order = order
			forum.forum_key = nsk_forum_id
			forum.forum_topics = 0
			put_forum_cache(forum)
		order+=1
		
def fetch_forum_topics(forum_code):
	logging.debug("Starting fetch_topics %s",forum_code)
	#nMatches = 1
	nPostStart = 0
	url = "http://velo.nsk.ru/spall/index.php?action=view_forum&param[forum]="+forum_code+"&skip="
	#while nMatches>0:
	
	result = urlfetch.fetch(url+str(nPostStart))
	logging.debug("  urlfetch done %s", url)
	if result.status_code == 200:
		logging.debug("  fetch ok")
		grab = result.content.decode('windows-1251')
		matches = re.findall("<div class='theme'>[^>]+>([^<]+)[^0-9]+([^&]+)[^=]+=([^']+)[^0-9]+([^\]]+)+\]([^(]+)\(([^\)]+)", grab)
		nMatches = len(matches)
		for match in matches:
			#0 - имя темы, 1 - id темы, 2 - id форума, 3 - количество сообщений, 4-  автор,  5 - дата и время
			nsk_topic_name = match[0]
			nsk_topic_id = match[1]
			nsk_forum_id = match[2]
			nsk_topic_posts_num = int(match[3])
			nsk_topic_author = match[4]
			nsk_topic_created = match[5]
			
			topic = get_topic_cache(nsk_topic_id, False)
			if topic is None:
				add_to_topics_queue(nsk_forum_id, nsk_topic_id, nsk_topic_name, nsk_topic_posts_num)
				logging.debug("topic %s added to queue", nsk_topic_id)				
			elif topic.topic_posts<>nsk_topic_posts_num: 
				logging.debug("%s posts number mismatch %d -> %d",nsk_topic_id, topic.topic_posts, nsk_topic_posts_num)
				add_to_topics_queue(nsk_forum_id, nsk_topic_id, nsk_topic_name, nsk_topic_posts_num)
			else:
				logging.debug("same posts number")
				#nMatches = 0;
				#break;
			
		nPostStart+= nMatches
		#else:
		#	nMatches = 0
		#if nPostStart > 10:
		#	break
		
def get_posts(self, forum_code, topic_id, forum , topic):
	logging.debug("starting get_posts")
	url = 'http://velo.nsk.ru/forumsheet.php?forum='+forum_code+'&topic='+topic_id+'&messid=1'
	result = urlfetch.fetch(url)
	logging.debug("urlfetch done %s", url)
	if result.status_code == 200:
		logging.debug("fetch ok")
		grab = result.content.replace('\n','').replace('<br />','[br]').replace('<center>',' ').replace('</center>',' ').decode('windows-1251')

		grab = isolate_video(grab)
		grab = isolate_images(grab)
		grab = isolate_refs(grab)
			 
		matches = re.findall('(<\/?div[^m]*mss>)<div class=hdr>[^<]+<([^>]+)>([^<]+)(?:[^;]+;){3}([^&]+)[^<]+[^&]+&topic=(\d+)&messid=(\d+)[^j]+j>([^<]+)[^x]+xt>([^<]*)', grab)
		logging.debug("found %d posts in topic awaiting %d",len(matches), topic.topic_posts)
		last_post_num = 0
		topic.topic_true_posts = 0
		cur_level = 0
		parent_posts = []
		prev_match = None
		posts_list = []
		
		for match in matches:
			# 0 - подсчет вложенности, 1 - ссылка на автора, 2 -  имя автора, 3 - дата и время, 4 - тема, 5 - номер сообщения, 6 - Заголовок сообщения, 7 - текст сообщения
			nsk_post_level = match[0]
			nsk_post_author_key = match[1]
			key_idx = nsk_post_author_key.find(r'key=')
			if key_idx>=0:
				nsk_post_author_key = nsk_post_author_key[key_idx+4:]
			else:
				nsk_post_author_key = ""
			nsk_post_author_name = match[2]
			nsk_post_date = datetime.strptime(match[3], '%d.%m.%y %H:%M')
			nsk_topic_id = match[4]
			nsk_post_num = int(match[5])
			nsk_post_title = match[6]
			nsk_post_text = match[7]
			nsk_parent_post = 0
			topic.topic_true_posts += 1
			#определим родительскую запись
			#если есть тэг nst, то погружаемся на один уровень
			if nsk_post_level.find(r'<div class=nst>')>=0 or prev_match is None:
				if not prev_match is None:
					nsk_parent_post = int(prev_match[5])
					parent_posts.insert(cur_level, nsk_parent_post)
					cur_level += 1
					
			else: #нет тэга nst, значит поднимаемся по дереву вверх
				steps_cnt = nsk_post_level.count(r'</div>') - 2
				cur_level -= steps_cnt
				nsk_parent_post = parent_posts[cur_level-1]
			
			post = get_post_dict(nsk_post_num, match[3], nsk_post_author_name, nsk_post_author_key, clear_post_title(nsk_post_title), nsk_post_text, nsk_parent_post)
			posts_list.append(post)
	   
			if nsk_post_num > last_post_num:
				last_post_num = nsk_post_num
				topic.topic_last_poster_name = nsk_post_author_name
				topic.topic_last_poster_id = nsk_post_author_key
				topic.topic_last_post_date = nsk_post_date
				topic.topic_last_post_title = format_cutheader(clear_post_title(nsk_post_title) + " " + nsk_post_text)
			if nsk_post_num==1:
				topic.topic_start_date = nsk_post_date;
				topic.topic_starter_name = nsk_post_author_name
				topic.topic_starter_id = nsk_post_author_key
				if topic.topic_name == u'ни о чем':
					topic.topic_name = format_cutheader(nsk_post_text)
			prev_match = match
		posts_sorted_list = sorted(posts_list, key=lambda lpost: lpost['post_num'])
		topic.topic_posts_text = json.dumps(posts_sorted_list, ensure_ascii = False, encoding = 'windows-1251')
		logging.debug("posts parsing done")
	else:
		logging.error("error retrieving url %s",url)	