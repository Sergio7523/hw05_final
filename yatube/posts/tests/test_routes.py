from django.test import TestCase
from django.urls import reverse


GROUP_SLUG = 'test-slug'

USER_USERNAME = 'TestUser'

URL_MAIN_PAGE = '/'

URL_POST_CREATE_PAGE = '/create/'

URL_PROFILE_PAGE = f'/profile/{USER_USERNAME}/'

URL_GROUP_LIST_PAGE = f'/group/{GROUP_SLUG}/'

URL_FOLLOW_INDEX_PAGE = '/follow/'

URL_FOLLOW_PAGE = f'/profile/{USER_USERNAME}/follow/'

URL_UNFOLLOW_PAGE = f'/profile/{USER_USERNAME}/unfollow/'

POST_ID = 1

URL_POST_DETAIL_PAGE = f'/posts/{POST_ID}/'

URL_POST_EDIT_PAGE = f'/posts/{POST_ID}/edit/'

URL_ADD_COMMENT_PAGE = f'/posts/{POST_ID}/comment/'


class PostsURLTests(TestCase):

    def test_1(self):
        links = {
            reverse('posts:index'): URL_MAIN_PAGE,
            reverse(
                'posts:group_list',
                kwargs={'slug': GROUP_SLUG}
            ): URL_GROUP_LIST_PAGE,
            reverse(
                'posts:profile',
                kwargs={'username': USER_USERNAME}
            ): URL_PROFILE_PAGE,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': POST_ID}
            ): URL_POST_DETAIL_PAGE,
            reverse('posts:post_create'): URL_POST_CREATE_PAGE,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': POST_ID}
            ): URL_POST_EDIT_PAGE,
            reverse(
                'posts:add_comment', kwargs={'post_id': POST_ID}
            ): URL_ADD_COMMENT_PAGE,
            reverse('posts:follow_index'): URL_FOLLOW_INDEX_PAGE,
            reverse(
                'posts:profile_follow',
                kwargs={'username': USER_USERNAME}
            ): URL_FOLLOW_PAGE,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': USER_USERNAME}
            ): URL_UNFOLLOW_PAGE
        }
        for url, value in links.items():
            with self.subTest(url=url):
                self.assertEqual(url, value)

    #def test_routes(self):
    #    links = {
    #        reverse('posts:index'): URL_MAIN_PAGE,
    #        reverse(
    #            'posts:group_list',
    #            kwargs={'slug': GROUP_SLUG}
    #        ): URL_GROUP_LIST_PAGE,
    #        reverse(
    #            'posts:profile',
    #            kwargs={'username': USER_USERNAME}
    #        ): URL_PROFILE_PAGE,
    #        reverse(
    #            'posts:post_detail',
    #            kwargs={'post_id': POST_ID}
    #        ): URL_POST_DETAIL_PAGE,
    #        reverse('posts:post_create'): URL_POST_CREATE_PAGE,
    #        reverse(
    #            'posts:post_edit',
    #            kwargs={'post_id': POST_ID}
    #        ): URL_POST_EDIT_PAGE,
    #        reverse(
    #            'posts:add_comment', kwargs={'post_id': POST_ID}
    #        ): URL_ADD_COMMENT_PAGE,
    #        reverse('posts:follow_index'): URL_FOLLOW_INDEX_PAGE,
    #        reverse(
    #            'posts:profile_follow',
    #            kwargs={'username': USER_USERNAME}
    #        ): URL_FOLLOW_PAGE,
    #        reverse(
    #            'posts:profile_unfollow',
    #            kwargs={'username': USER_USERNAME}
    #        ): URL_UNFOLLOW_PAGE
    #    }
    #    for url, value in links.items():
    #        with self.subTest(url=url):
    #            self.assertEqual(url, value)
