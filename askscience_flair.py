import praw
import json
import sqlalchemy as sql
from sqlalchemy import Column, String, Boolean, Integer 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
import time
import os
import urllib
Base = declarative_base()

########## SETTINGS SECTION############
subreddit_target = 'askScience'
minutes_before_flair_check = 5
hours_to_flair = 1 
hours_before_autoremove = 24
science_flair_dict = {"Physics":"physics","Astronomy":"astro","Earth Sciences":"geo",
"Chemistry":"chem","Biology":"bio","Paleontology":"bio",'Medicine':"med",'Human Body':'med',
'Neuroscience':"neuro",'Psychology':'psych','Social Science':'soc','Political Science':'soc',\
 "Economics":'soc','Archaeology':'soc','Anthropology':'soc','Linguistics':'soc',\
 "Engineering":'eng','Computing':'computing',"Mathematics":'maths',"Planetary Sci.":'geo'}
##########END SETTINGS SECTION############
 
def load_settings(file_name):
    """
    loads sensitive settings from files to ensure privacy.
    arg: file_name: a string that contains the path to a json file with the relevent settings.
                    file must be in same directory as this script.
    """
    file_name = os.path.dirname(os.path.realpath(__file__))+"/"+file_name
    with open(file_name,"r") as settings_file:
        json_dict = json.load(settings_file)
    return json_dict
    
DBinfo = load_settings("DBinfo.json")

def create_session():
    """
    Creates and returns a sqlite session
    """
    engine_string = "mysql://"+DBinfo["username"]+":"+DBinfo["password"]+"@"\
    +DBinfo["IP"]+":{}".format(DBinfo["port"])+"/"+DBinfo["dbname"]
    engine = sql.create_engine(engine_string)
    Session = sessionmaker(bind=engine)
    session =Session()
    return session
    
class Posts(Base):
    post_id = Column(String(6), primary_key = True)
    approved = Column(Boolean, default=False)
    upvotes = Column(Integer)
    downvotes = Column(Integer)
    created_utc = Column(Integer,index=True)
    removed = Column(Boolean, default=False)
    approved_by = Column(String(30))
    removed_by = Column(String(30))
    author = Column(String(30))
    title = Column(String(300))
    body = Column(String(15000))
    permalink = Column(String(300))
    flair_text = Column(String(50))
    flair_css_class = Column(String(50))
    __tablename__ = "posts"
    def __repr__(self):
        string = "http://redd.it/{}".format(self.post_id)
        return string
def create_metadata():
    """
    creates tables in the database
    """
    engine_string = "mysql://"+DBinfo["username"]+":"+DBinfo["password"]+"@"\
    +DBinfo["IP"]+":{}".format(DBinfo["port"])+"/"+DBinfo["dbname"]
    engine = sql.create_engine(engine_string)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.commit()
    session.close()
    Base.metadata.create_all(engine)     
    session = Session()
    session.commit()

def get_new_posts():
    """
    fetches current items in the modqueue.  adjust limit variable to limit number of posts that get fetched.
    """
    return r.get_mod_queue(subreddit_target,{"only":"links","limit":"15"})
def add_new_items_to_db(session):
    """
    fetches the modqueue and then searches the database for items.
    items not already in the database are added and a comment is left on posts without flair.
    """
    new_posts = get_new_posts()
    for post in new_posts:
        search = session.query(Posts).filter(Posts.post_id == post.id).first()
        if search:
            pass
        else:
            now = time.time()
            if now > post.created_utc + 60*minutes_before_flair_check: 
                approved = False
                removed = False
                if post.banned_by !=True and post.banned_by !=None:
                    print(type(post.banned_by))
                    print (post.banned_by)
                    removed = True
                if post.approved_by:
                    approved=True
                print(post.title)
                post.title = post.title.encode('ascii',errors='ignore')
                db_add = Posts(post_id = post.id,created_utc = post.created_utc,\
                approved = approved,removed=removed, flair_text = post.link_flair_text,\
                flair_css_class = post.link_flair_css_class, author=post.author.name,\
                title = post.title)
                intro = "Hi {} thank you for submitting to /r/Askscience.\n\n".format(post.author.name)
                rules_pm = """ Your post is not yet visible on the forum and is awaiting review from the moderator team. Your question may be denied for the following reasons, \n\n 
* **Have you searched for your question on** [**AskScience**](https://www.reddit.com/r/askscience/search?q={title} &sort=relevance&restrict_sr=on&t=all) **or on** \
 [**Google**](https://www.google.com/search?q={title})**?** - Common questions, or questions covered in the [**FAQ**](https://www.reddit.com/r/askscience/wiki/faq), will be rejected.
* **Are you asking for** [**medical advice**](http://redd.it/s4chc) **or does your post contain personal medical information?** - These questions, even innocuous ones should be between you and your doctor.
* **Is your post speculative or hypothetical?** - Questions involving unphysical what ifs or imaginary situations requiring guesses and speculation are best for /r/AskScienceDiscussion. \n
There are more restrictions on what kind of questions are suitable for /r/AskScience, the above are just some of the most common. While you wait, check out the forum 
[**Posting Guidelines**](https://www.reddit.com/r/askscience/wiki/quickstart/askingquestions) on asking questions as well as our [**User Help Page**](https://www.reddit.com/r/askscience/wiki/index#wiki_askscience_user_help_page). \
Please wait several hours before messaging us if there is an issue, moderator mail concerning recent submissions will be ignored.\n\n\
""".format(title = urllib.parse.quote(post.title))
                flair_comment = "If your post is not flaired it will not be reviewed. \
   Please add flair to your post. \n \n \
Your post will be removed permanently  if flair is not added within one hour \n\n\
You can flair this post by replying to this message with  your  flair choice. \
 It must be an exact match to one of the following flair categories and contain no other text:\n\n\
 'Computing', 'Economics', 'Human Body', 'Engineering', 'Planetary Sci.', 'Archaeology', 'Neuroscience',\
 'Biology', 'Chemistry', 'Medicine', 'Linguistics', 'Mathematics', 'Astronomy', 'Psychology',\
 'Paleontology', 'Political Science', 'Social Science', 'Earth Sciences', 'Anthropology', 'Physics'\n\n"
                bot_message = "I am a bot, and this action was performed automatically.\
Please contact the [moderators of this subreddit](http://www.reddit.com/message/compose?\
to=%2Fr%2FAskScience&amp;message=My%20Post:%20http://redd.it/{}) if you have any questions or concerns"\
.format(post.id)
                if not post.link_flair_text:
                    print("added flair comment: {}".format(post.id))
                    comment = post.add_comment(intro+flair_comment+rules_pm+bot_message)
                    comment.distinguish()
                else:
                    r.send_message(post.author.name,"Welcome to /r/askScience!",intro+rules_pm+bot_message)
                session.add(db_add)            
    return session
    
def check_flair(list_of_posts,session):
    for post in list_of_posts:
        submission = r.get_submission(submission_id=post.post_id)
        if submission.banned_by !=True and submission.banned_by != None:
            post.removed = True
        if submission.approved_by:
            post.approved=True
        post.flair_text = submission.link_flair_text
        post.flair_css_class = submission.link_flair_css_class
        me = r.get_me()
        #check new posts for flair and removed self posted comments
        if submission.link_flair_text or submission.link_flair_css_class:
            for comment in submission.comments:
                if comment.author.name == me.name:
                    print("removing self comment {}".format(submission.id))
                    comment.remove()
        #check for text replies and flair posts based on replies
        else:
            for comment in submission.comments:
                if comment.author.name == me.name:
                    for reply in comment.replies:
                        reply_body = reply.body
                        print("reply: {}".format(reply_body))
                        if reply_body:
                            word = reply_body.title().strip()
                            if word.startswith("'"):
                                word = word[1:]
                            if word.endswith("'"):
                                word = word[:-1]
                            print(word)
                            print (word in science_flair_dict.keys())
                            if word in science_flair_dict.keys():
                                print("adding flair")
                                print(submission.id)
                                r.set_flair(subreddit_target,submission,word,science_flair_dict[word])
                                for comment in submission.comments:
                                    if comment.author.name == me.name:
                                        comment.remove()
                                        for reply in comment.replies:
                                            reply.remove()
        print ("{},id:{} flair: {}, approved = {}"\
        .format(post.title,post.post_id,post.flair_text,post.approved))        
        
        session.add(post)
    return session

def remove_posts_without_flair(list_of_posts,session):
    for post in list_of_posts:
        submission = r.get_submission(submission_id=post.post_id)
        if submission.banned_by !="True" and submission.banned_by != None:
            post.removed = True
        if submission.approved_by:
            post.approved=True
        post.flair_text = submission.link_flair_text
        post.flair_css_class = submission.link_flair_css_class
        if not post.approved and not post.flair_text:
            submission.remove()
            print ("removing post: {},id:{} flair: {}, approved = {}"\
            .format(post.title,post.post_id,post.flair_text,post.approved))
            post.removed=True
        session.add(post)
    return session
    
        
def remove_posts(list_of_posts,session):
    for post in list_of_posts:
        submission = r.get_submission(submission_id=post.post_id)
        if submission.banned_by !="True" and submission.banned_by != None:
            post.removed = True
        if submission.approved_by:
            post.approved=True
        post.flair_text = submission.link_flair_text
        post.flair_css_class = submission.link_flair_css_class
        if not post.approved:
            submission.remove()
            print ("removing post: {},id:{}, approved = {}"\
            .format(post.title,post.post_id,post.approved))
            post.removed=True
        session.add(post)
    return session
                
    
if __name__ == "__main__":
    
    client_info = load_settings("clientinfo.json")
    r = praw.Reddit('AskScience Flair Assistant V1.0 by /u/Doomhammer458')   
    r.set_oauth_app_info(client_id=client_info["client_id"],\
    client_secret=client_info["client_secret"],redirect_uri=client_info["redirect_uri"])
    mod_access = load_settings("mod_access.json")
    new_mod_access= r.refresh_access_information(mod_access['refresh_token'])
    r.set_access_credentials(**new_mod_access)
    print("New posts for DB \n")
    session = create_session()
    session = add_new_items_to_db(session)
    now = time.time()
    unflaired_posts = session.query(Posts)\
    .filter(and_(Posts.flair_text==None, now - Posts.created_utc < 60*60*hours_to_flair,\
    Posts.approved==False,Posts.removed==False)).all()
    
    print("\nChecking old posts for flair\n")   
    session = check_flair(unflaired_posts,session)
    old_unflaired_posts = session.query(Posts)\
    .filter(and_(Posts.flair_text==None, now - Posts.created_utc > 60*60*hours_to_flair,\
    Posts.approved==False,Posts.removed==False)).all()
    
    print("\nRemoving unflaired posts \n")
    session = remove_posts_without_flair(old_unflaired_posts,session)
    session.commit()
    session = create_session()
    print("\nRemoving not approved posts older than 24 hours\n")
    unapproved_posts = session.query(Posts)\
    .filter(and_(now - Posts.created_utc > 60*60*hours_before_autoremove,\
    Posts.approved==False,Posts.removed==False)).all()
    remove_posts(unapproved_posts,session)
    print("commiting to DB") 
    session.commit()
