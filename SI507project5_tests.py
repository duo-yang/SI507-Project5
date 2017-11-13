import unittest
import copy
from SI507project5_code import *


CACHE_TEST_FNAME = "cache_contents_example.json"

try:
    with open(CACHE_TEST_FNAME, 'r', encoding='UTF-8') as cache_test:
        test_json = cache_test.read()
        CACHE_TEST_DICTION = json.loads(test_json)
except FileNotFoundError:
    CACHE_TEST_DICTION = {}

TEXT_IDENT =\
    "HTTPS://API.TUMBLR.COM/V2/BLOG/NBCNEWS.TUMBLR.COM/POSTS"\
    + "/?FILTER_TEXT_LIMIT_20_TYPE_TEXT"
PHOTO_IDENT = \
    "HTTPS://API.TUMBLR.COM/V2/BLOG/NBCNEWS.TUMBLR.COM/POSTS"\
    +"/?FILTER_TEXT_LIMIT_20_TYPE_PHOTO"


class PostTest(unittest.TestCase):
    def setUp(self):
        self.text_data = get_from_cache(
            TEXT_IDENT, CACHE_TEST_DICTION)['response']['posts']
        self.photo_data = get_from_cache(
            PHOTO_IDENT, CACHE_TEST_DICTION)['response']['posts']
        self.test_post1 = Post(self.text_data[0])
        self.test_text = TextPost(self.text_data[0])
        self.test_post2 = Post(self.photo_data[0])
        self.test_photo = PhotoPost(self.photo_data[0])

    def test_init(self):
        self.assertIsInstance(self.test_post1, Post,
                              "Post not init properly")
        self.assertIsInstance(self.test_text, TextPost,
                              "TextPost not init properly")
        self.assertIsInstance(self.test_photo, PhotoPost,
                              "PhotoPost not init properly")

    def test_var(self):
        self.assertIsInstance(self.test_post1.blog_name, str,
                              "Post not init properly")
        self.assertIsInstance(self.test_post1.post_id, int,
                              "Post not init properly")
        self.assertIsInstance(self.test_post1.post_url, str,
                              "Post not init properly")
        self.assertIsInstance(self.test_post1.post_type, str,
                              "Post not init properly")
        self.assertIsInstance(self.test_post1.post_date, str,
                              "Post not init properly")
        self.assertIsInstance(self.test_text.title, str,
                              "TextPost not init properly")
        self.assertIsInstance(self.test_text.body, str,
                              "TextPost not init properly")
        self.assertIsInstance(self.test_photo.photos, list,
                              "PhotoPost not init properly")
        self.assertIsInstance(self.test_photo.caption, str,
                              "PhotoPost not init properly")

    def test_str(self):
        self.assertNotEqual(str(self.test_post2), str(self.test_photo),
                            "PhotoPost string method not correct")
        self.assertNotEqual(str(self.test_post1), str(self.test_text),
                            "TextPost string method not correct")

    def tearDown(self):
        self.text_data = None
        self.photo_data = None
        self.test_post1 = None
        self.test_text = None
        self.test_photo = None

class ListTest(unittest.TestCase):

    def test_length(self):
        self.assertTrue(len(posts) <= 20,
                        "posts length not correct")
        self.assertTrue(len(photo_posts) <= 20,
                        "photo_posts length not correct")
        self.assertTrue(len(text_posts) <= 20,
                        "text_posts length not correct")

    def test_type(self):
        self.assertIsInstance(posts[0], Post,
                              "posts instance not correct")
        self.assertIsInstance(photo_posts[0], PhotoPost,
                              "photo_posts instance not correct")
        self.assertIsInstance(text_posts[0], TextPost,
                              "text_posts instance not correct")

if __name__ == "__main__":
    unittest.main(verbosity=2)
