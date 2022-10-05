from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User

GROUP_SLUG = 'test-slug'

USER_USERNAME = 'TestUser'

URL_MAIN_PAGE = '/'

URL_POST_CREATE_PAGE = '/create/'

URL_PROFILE_PAGE = f'/profile/{USER_USERNAME}/'

URL_GROUP_LIST_PAGE = f'/group/{GROUP_SLUG}/'

URL_FOLLOW_INDEX_PAGE = '/follow/'

URL_FOLLOW_PAGE = f'/profile/{USER_USERNAME}/follow/'

URL_UNFOLLOW_PAGE = f'/profile/{USER_USERNAME}/unfollow/'


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )
        cls.URL_POST_DETAIL_PAGE = f'/posts/{cls.post.pk}/'
        cls.URL_POST_EDIT_PAGE = f'/posts/{cls.post.pk}/edit/'
        cls.URL_ADD_COMMENT_PAGE = f'/posts/{cls.post.pk}/comment/'

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_routes(self):
        links = {
            reverse('posts:index'): URL_MAIN_PAGE,
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsURLTests.group.slug}
            ): URL_GROUP_LIST_PAGE,
            reverse(
                'posts:profile',
                kwargs={'username': PostsURLTests.user.username}
            ): URL_PROFILE_PAGE,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsURLTests.post.pk}
            ): PostsURLTests.URL_POST_DETAIL_PAGE,
            reverse('posts:post_create'): URL_POST_CREATE_PAGE,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsURLTests.post.pk}
            ): PostsURLTests.URL_POST_EDIT_PAGE,
            reverse(
                'posts:add_comment', kwargs={'post_id': PostsURLTests.post.pk}
            ): PostsURLTests.URL_ADD_COMMENT_PAGE,
            reverse('posts:follow_index'): URL_FOLLOW_INDEX_PAGE,
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsURLTests.user.username}
            ): URL_FOLLOW_PAGE,
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsURLTests.user.username}
            ): URL_UNFOLLOW_PAGE
        }
        for url, value in links.items():
            with self.subTest(url=url):
                self.assertEqual(url, value)
