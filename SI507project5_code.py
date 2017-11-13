## import statements

import requests_oauthlib
import webbrowser
import json
import csv
from datetime import datetime
from pprint import pprint

import secret_data


# CACHING SETUP #
# --------------------------------------------------
# Caching constants
# --------------------------------------------------

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = True
CACHE_FNAME = "cache_contents.json"
CREDS_CACHE_FILE = "creds.json"


# --------------------------------------------------
# Load cache files: data and credentials
# --------------------------------------------------

# Load data cache
try:
    with open(CACHE_FNAME, 'r', encoding='UTF-8') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except FileNotFoundError:
    CACHE_DICTION = {}

# Load creds cache
try:
    with open(CREDS_CACHE_FILE, 'r', encoding='UTF-8')\
            as creds_file:
        cache_creds = creds_file.read()
        CREDS_DICTION = json.loads(cache_creds)
except FileNotFoundError:
    CREDS_DICTION = {}


# ---------------------------------------------
# Cache functions
# ---------------------------------------------
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days

    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days > expire_in_days:
        # It's been longer than expiry time
        return True
    else:
        return False


def get_from_cache(identifier, dictionary):
    """If unique identifier exists in specified cache dictionary and has not
    expired, return the data associated with it from the request, else return
    None
    """
    # Assuming none will differ with case sensitivity here
    identifier = identifier.upper()
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'], data_assoc_dict[
                "expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data


def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data
    cache dictionary, and save the whole dictionary to a file as json
    """
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w', encoding='UTF-8') as cached_file:
        cached_json = json.dumps(CACHE_DICTION)
        cached_file.write(cached_json)


def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the
    credentials cache dictionary, and save the whole dictionary to a file as
    json
    """
    identifier = identifier.upper()  # make unique
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CREDS_CACHE_FILE, 'w', encoding='UTF-8') as cached_file:
        cached_json = json.dumps(CREDS_DICTION)
        cached_file.write(cached_json)


# ADDITIONAL CODE for program should go here...
# Perhaps authentication setup, functions to get and process data,
# a class definition... etc.

# OAuth1 API Constants - vary by API
# Private data in a hidden secret_data.py file

# what Tumblr calls Consumer Key
CONSUMER_KEY = secret_data.consumer_key
# What Tumblr calls Consumer Secret
CONSUMER_SECRET = secret_data.consumer_secret

# Specific to API URLs, not private
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"


def get_tokens(client_key=CONSUMER_KEY, client_secret=CONSUMER_SECRET,
               request_token_url=REQUEST_TOKEN_URL,
               base_authorization_url=BASE_AUTH_URL,
               access_token_url=ACCESS_TOKEN_URL,
               verifier_auto=True):
    oauth_inst = requests_oauthlib.OAuth1Session(
        client_key, client_secret=client_secret)

    fetch_response = oauth_inst.fetch_request_token(request_token_url)

    # Using the dictionary .get method in these lines
    resource_owner_key = fetch_response.get('oauth_token')
    resource_owner_secret = fetch_response.get('oauth_token_secret')

    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # Open the auth url in browser:

    # For user to interact with & approve access of this app -- this script
    webbrowser.open(auth_url)

    # Deal with required input, which will vary by API
    if verifier_auto:
        # if the input is default (True), like Twitter
        verifier = input("Please input the verifier:  ").strip()
    else:
        redirect_result = input("Paste the full redirect URL here:  ").strip()
        # returns a dictionary
        # -- you may want to inspect that this works and edit accordingly
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result)
        verifier = oauth_resp.get('oauth_verifier')

    # Regenerate instance of oauth1session class with more data
    oauth_inst = requests_oauthlib.OAuth1Session(
        client_key, client_secret=client_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier)

    # returns a dictionary
    oauth_tokens = oauth_inst.fetch_access_token(access_token_url)

    # Use that dictionary to get these things
    # Tuple assignment syntax
    resource_owner_key, resource_owner_secret = oauth_tokens.get(
        'oauth_token'), oauth_tokens.get('oauth_token_secret')

    return client_key, client_secret, resource_owner_key, \
        resource_owner_secret, verifier


# Default: 1 days for creds expiration
def get_tokens_from_service(service_name_ident, expire_in_days=1):
    creds_data = get_from_cache(service_name_ident, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading creds from cache...")
            print()
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.")
            print()
        creds_data = get_tokens(verifier_auto=False)
        set_in_creds_cache(service_name_ident, creds_data,
                           expire_in_days=expire_in_days)
    return creds_data


def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(), key=lambda x: x[0])
    # Make the list of tuples into a flat list using a complex list
    # comprehension
    params_str = "_".join([str(e) for l in sorted_params for e in l])
    total_ident = url + "?" + params_str
    return total_ident.upper()  # Creating the identifier


def get_data_from_api(request_url, service_ident, params_diction,
                      expire_in_days=1):
    """Check in cache, if not found, load data, save in cache and then return
    that data
    """
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident, CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        # Get credentials
        client_key, client_secret, resource_owner_key, resource_owner_secret,\
            verifier = get_tokens_from_service(service_ident)

        # Create a new instance of oauth to make a request with
        oauth_inst = requests_oauthlib.OAuth1Session(
            client_key, client_secret=client_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the scenes,
        # thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url, params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data


# Define classes for post data
class Post(object):
    def __init__(self, dict_post):
        self.blog_name = dict_post['blog_name']
        self.post_id = dict_post['id']
        self.post_url = dict_post['post_url']
        self.post_type = dict_post['type']
        self.post_date = dict_post['date']

    def __str__(self):
        return "Post #{0} ({1}) by {2} at {3}\nRetrieved from {4}".format(
            self.post_id, self.post_type, self.blog_name, self.post_date,
            self.post_url)


class PhotoPost(Post):
    def __init__(self, dict_photo_post):
        super().__init__(dict_photo_post)

        self.caption = dict_photo_post['caption']
        list_photo = dict_photo_post['photos']
        self.photos = [photo['original_size']['url'] for photo in list_photo]

    def __str__(self):
        return ("Post #{0} ({1}) by {2} at {3}\nRetrieved from {4}".format(
                self.post_id, self.post_type, self.blog_name, self.post_date,
                self.post_url))\
               + ("\nCaption: {0}\n".format(self.caption.replace('\n', ' ')))\
               + "Photos:\n" + "\n".join(self.photos)


class TextPost(Post):
    def __init__(self, dict_text_post):
        super().__init__(dict_text_post)

        self.title = dict_text_post['title']
        self.body = dict_text_post['body']

    def __str__(self):
        return ("Post #{0} ({1}) by {2} at {3}\nRetrieved from {4}".format(
                self.post_id, self.post_type, self.blog_name, self.post_date,
                self.post_url))\
               + "\nTitle: {0}\nBody: {1}".format(
                self.title, self.body.replace('\n', ' '))


# Make sure to run your code and write CSV files by the end of the program.
# Method for printing CSV files.
def print_posts_csv(list_post, file_name='posts.csv'):
    with open(file_name, "w", encoding='utf-8', newline='')\
            as csv_file:
        # Write column names
        writer = csv.writer(csv_file)
        writer.writerow(
            ["Blog Name", "Post ID", "Post Type", "Post Date", "Post URL"])
        for post in list_post:
            # Write national site entry lines
            writer.writerow(
                [post.blog_name,
                 post.post_id,
                 post.post_type,
                 post.post_date,
                 post.post_url.strip()])


def print_photo_posts_csv(list_post, file_name='photo_posts.csv'):
    with open(file_name, "w", encoding='utf-8', newline='')\
            as csv_file:
        # Write column names
        writer = csv.writer(csv_file)
        writer.writerow(
            ["Blog Name", "Post ID", "Post Type", "Caption", "Photo URL",
             "Post Date", "Post URL"])
        for post in list_post:
            # Write national site entry lines
            for photo in post.photos:
                writer.writerow(
                    [post.blog_name,
                     post.post_id,
                     post.post_type,
                     post.caption.replace('\n', ' '),
                     photo,
                     post.post_date,
                     post.post_url.strip()])


def print_text_posts_csv(list_post, file_name='text_posts.csv'):
    with open(file_name, "w", encoding='utf-8', newline='')\
            as csv_file:
        # Write column names
        writer = csv.writer(csv_file)
        writer.writerow(
            ["Blog Name", "Post ID", "Post Type", "Title", "Body",
             "Post Date", "Post URL"])
        for post in list_post:
            # Write national site entry lines
            writer.writerow(
                [post.blog_name,
                 post.post_id,
                 post.post_type,
                 post.title,
                 post.body.replace('\n', ' '),
                 post.post_date,
                 post.post_url.strip()])

if not CONSUMER_KEY or not CONSUMER_SECRET:
    print("You need to fill in sonsumer_key and consumer_secret in the "
          "secret_data.py file.")
    exit()
if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
    print("You need to fill in this API's specific OAuth2 URLs in this "
          "file.")
    exit()

# Invoke functions
TUMBLR_SEARCH_BASEURL = "https://api.tumblr.com/v2/blog/"
tumblr_search_nbc_posts_baseurl = \
    TUMBLR_SEARCH_BASEURL + "nbcnews.tumblr.com/posts/"

# Search for photos
tumblr_search_params = {'type': "photo",
                        'limit': 20,
                        'filter': "text"}
tumblr_result = get_data_from_api(
    tumblr_search_nbc_posts_baseurl, "Tumblr",
    tumblr_search_params)
# print(type(tumblr_result))
# pprint(tumblr_result)

result_posts = tumblr_result['response']['posts']
posts = [Post(post) for post in result_posts]
photo_posts = [PhotoPost(post) for post in result_posts]
# i = 0
# for post in posts:
#     i += 1
#     print(i)
#     print(post)
# print()
# for post in photo_posts:
#     print(post)
# print()

# Search for text
tumblr_search_params = {'type': "text",
                        'limit': 20,
                        'filter': "text"}

tumblr_result = get_data_from_api(
    tumblr_search_nbc_posts_baseurl, "Tumblr",
    tumblr_search_params)
# print(type(tumblr_result))
# pprint(tumblr_result)

result_posts = tumblr_result['response']['posts']
text_posts = [TextPost(post) for post in result_posts]
# for post in text_posts:
#     print(post)
# print()

print_posts_csv(posts)
print_photo_posts_csv(photo_posts)
print_text_posts_csv(text_posts)