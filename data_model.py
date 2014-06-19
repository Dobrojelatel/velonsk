from google.appengine.ext import db

class Forum(db.Model):
    forum_name = db.StringProperty()
    forum_desc = db.StringProperty()
    forum_topics = db.IntegerProperty()
    forum_last_post_subject = db.StringProperty()
    forum_last_post_time = db.DateTimeProperty()
    forum_last_poster_name = db.StringProperty()
    forum_last_poster_id = db.StringProperty()
    forum_last_post_id = db.StringProperty()
    forum_order = db.IntegerProperty()
    forum_key = db.StringProperty()
    
class Topic(db.Model):
    forum_key = db.StringProperty()
    topic_id = db.StringProperty()
    topic_name = db.StringProperty()
    topic_posts = db.IntegerProperty()
    topic_true_posts = db.IntegerProperty()
    topic_starter_name = db.StringProperty()
    topic_starter_id = db.StringProperty()    
    topic_start_date = db.DateTimeProperty()
    topic_last_poster_name = db.StringProperty()
    topic_last_poster_id = db.StringProperty()
    topic_last_post_date = db.DateTimeProperty()
    topic_last_post_title = db.StringProperty()
    topic_views = db.IntegerProperty()
    topic_posts_text = db.TextProperty()

class Options(db.Model):
    topics_per_page = db.IntegerProperty()
    posts_per_page = db.IntegerProperty()
