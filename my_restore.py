import re
from velo_cache import *

youtube1 = re.compile(r'\[URL=\"http([^y]+)youtube\.com([^v]+)v=([^&\"]+)([^\"]*)\"\]([^\[]+)\[\/URL\]')
youtube2 = re.compile(r'\[YOUTUBE\]([^\[]+)\[\/YOUTUBE\]')
vimeo	 = re.compile(r'\[VIMEO\]([^\[]+)\[\/VIMEO\]')
	
def restore_video(p_src, p_mode):
	rez = p_src;
	rez = youtube1.sub(r'<br />[YOUTUBE]\3[/YOUTUBE]<br />',rez)
	if p_mode == 0:
		rez = youtube2.sub(r'<br/><iframe width="640" height="385" src="http://www.youtube.com/embed/\1" frameborder="0" allowfullscreen></iframe>',rez)
		rez = vimeo.sub(r'<br/><iframe width="640" height="385" src="http://player.vimeo.com/video/\1" frameborder="0" allowfullscreen></iframe>',rez)
	else:
		rez = youtube2.sub(u'<br/>видео',rez)
		rez = vimeo.sub(u'<br/>видео',rez)
	return rez
	

outer_image = re.compile(r'\[IMG\]http([^\[]+)\[\/IMG\]')
inline_image = re.compile(r'\[IMG\]data([^\[]+)\[\/IMG\]')
velonsk_image = re.compile(r'\[IMG\]i/([^\[]+)\[\/IMG\]')
def restore_images(p_src, p_mode):
	rez = p_src
	if p_mode ==0:
		rez = outer_image.sub(r'<br /><img class="eMessage" src="http\1">',rez)
		rez = inline_image.sub(r'<br /><img class="eMessage" src="data\1">',rez)
		rez = velonsk_image.sub(r'<br /><img class="eMessage" src="http://velo.nsk.ru/i/\1">',rez)
	else:
		rez = outer_image.sub(u'<br />картинка',rez)
		rez = inline_image.sub(u'<br />картинка',rez)
		rez = velonsk_image.sub(u'<br />картинка',rez)	
	return rez

	
def isolate_video(p_src):
	rez = p_src
	#youtube, старый вариант
	rez = re.sub(r'<object[^\/]+[^v]+v\/([^?]+)[^>]+>', r'[YOUTUBE]\1[/YOUTUBE]',rez) 
	#youtube, новый вариант
	rez = re.sub(r"<iframe width=[^h]+height=[^s]+ src='http:\/\/www.youtube.com\/embed\/([^']+)'([^>]+)><\/iframe>",r"[YOUTUBE]\1[/YOUTUBE]",rez) 
	#vimeo
	rez = re.sub(r'<iframe width=\'640\' height=\'385\' src=\'http:\/\/player.vimeo.com\/video\/([^\']+)\'([^>]+)><\/iframe>',r'[VIMEO]\1[/VIMEO]',rez)
	return rez

def isolate_images(p_src):
	rez = p_src
	rez = re.sub(r'<img src=\"([^\"]*)\"[^>]*>', r'[IMG]\1[/IMG]',rez)
	return rez
def isolate_refs(p_src):
	rez = p_src
	rez = re.sub(r'<a target=_blank href=\'([^\']*)\'>([^<]*)<\/a>', r'[URL="\1"]\2[/URL]',rez) #вычленяем ссылки вариант с '
	rez = re.sub(r'<a target=_blank href=\"([^\"]*)\">([^<]*)<\/a>', r'[URL="\1"]\2[/URL]',rez) #вычленяем ссылки вариант с "
	rez = re.sub(r'<a target=_blank href=([^>]*)>([^<]*)<\/a>', r'[URL="\1"]\2[/URL]',rez) #вычленяем ссылки
	return rez

def format_cutheader(value):
	rez = restore_video(value, 1)
	rez = restore_images(rez, 1)
	rez = restore_refs(rez, 1)
	if len(rez) > 150:
		return rez[:150] + "..."
	else:
		return rez
		
def decode_topic_message_id(match_object):
	topic =  get_topic_cache(match_object.group(2), False)
	if topic:
		return topic.topic_name
	else:
		return match_object.group(4)
	
def restore_refs(p_src, p_mode = 0):
	rez = p_src
	if p_mode==0:
		# ссылка на велоэнск
		rez = re.sub('\[URL="http://velo.nsk.ru/forum.php\?forum=([^&]+).amp;topic=([^&]+).amp;messid=([^"]*)"\]([^\[]+)\[\/URL\]',decode_topic_message_id,rez)
		rez = re.sub('\[URL="http://velo.nsk.ru/forum.php\?forum=([^&]+)&topic=([^&]+)&messid=([^"]*)"\]([^\[]+)\[\/URL\]',decode_topic_message_id,rez)
		# сцылка с inline картинкой - удаляем
		rez = re.sub(r'\[URL="data([^"]+)"\]([^\[]+)\[\/URL\]',r'\2',rez)
		# сцылка с картинкой с велоэнска - удаляем
		rez = re.sub(r'\[URL="i/([^"]+)"\]([^\[]+)\[\/URL\]',r'\2',rez)
		# сцылка с картинкой
		rez = re.sub(r'\[URL="http([^"]+)"\]<([^\[]+)\[\/URL\]',r'<a target=_blank href="http\1"><\2</a>',rez)
		# внешняя сцылка
		rez = re.sub(r'\[URL="http([^"]+)"\]([^\]]*)\[\/URL\]',r'<a target=_blank href="http\1">\2</a>',rez);
		# просто ссылка
		#post_text = re.sub(r'\[URL="([^"]+)"\]([^\[]+)\[\/URL\]',r'<a target=_blank href="http://velo.nsk.ru/\1">\2</a>',post_text)
	else:
		# ссылка на велоэнск
		rez = re.sub('\[URL="http://velo.nsk.ru/forum.php\?forum=([^&]+).amp;topic=([^&]+).amp;messid=([^"]*)"\]([^\[]+)\[\/URL\]',decode_topic_message_id,rez)
		# просто ссылка
		rez = re.sub(r'\[URL="([^"]+)"\]([^\[]+)\[\/URL\]',r'\2',rez)
		
	return rez