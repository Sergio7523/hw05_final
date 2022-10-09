from django.test import TestCase
from django.urls import reverse

from urllib.parse import urljoin


GROUP_SLUG = 'test-slug'

USER_USERNAME = 'TestUser'

URL_MAIN_PAGE = '/'

URL_POST_CREATE_PAGE = '/create/'

URL_PROFILE_PAGE = f'/profile/{USER_USERNAME}/'

URL_GROUP_LIST_PAGE = f'/group/{GROUP_SLUG}/'

URL_FOLLOW_INDEX_PAGE = '/follow/'

URL_FOLLOW_PAGE = urljoin(URL_PROFILE_PAGE, 'follow/')

URL_UNFOLLOW_PAGE = urljoin(URL_PROFILE_PAGE, 'unfollow/')

POST_ID = 1

URL_POST_DETAIL_PAGE = f'/posts/{POST_ID}/'

URL_POST_EDIT_PAGE = urljoin(URL_POST_DETAIL_PAGE, 'edit/')

URL_ADD_COMMENT_PAGE = urljoin(URL_POST_DETAIL_PAGE, 'comment/')


class PostsURLTests(TestCase):

    def test_1(self):
        links = {
            'posts:index': (URL_MAIN_PAGE, None),
            'posts:group_list': (URL_GROUP_LIST_PAGE, {'slug': GROUP_SLUG}),
            'posts:profile': (URL_PROFILE_PAGE, {'username': USER_USERNAME}),
            'posts:post_detail': (URL_POST_DETAIL_PAGE, {'post_id': POST_ID}),
            'posts:post_create': (URL_POST_CREATE_PAGE, None),
            'posts:post_edit': (URL_POST_EDIT_PAGE, {'post_id': POST_ID}),
            'posts:add_comment': (URL_ADD_COMMENT_PAGE, {'post_id': POST_ID}),
            'posts:follow_index': (URL_FOLLOW_INDEX_PAGE, None),
            'posts:profile_follow':
            (URL_FOLLOW_PAGE, {'username': USER_USERNAME}),
            'posts:profile_unfollow':
            (URL_UNFOLLOW_PAGE, {'username': USER_USERNAME}),
        }
        for key_rev, value_tuple in links.items():
            expected_link = value_tuple[0]
            kwargs_dct = value_tuple[1]
            with self.subTest(key_rev=key_rev):
                self.assertEqual(
                    reverse(key_rev, kwargs=kwargs_dct), expected_link
                )
