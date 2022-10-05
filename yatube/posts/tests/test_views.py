import shutil

import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User


GROUP_SLUG = 'test-slug'

GROUP2_SLUG = 'test-slug2'

USER_USERNAME = 'TestUser'

USER_TO_FOLLOW_USERNAME = 'TestUserToFollow'

URL_GROUP_LIST_PAGE = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})

URL_GROUP2_LIST_PAGE = reverse(
    'posts:group_list', kwargs={'slug': GROUP2_SLUG}
)

URL_INDEX_PAGE = reverse('posts:index')

URL_POST_CREATE_PAGE = reverse('posts:post_create')

URL_PROFILE_PAGE = reverse('posts:profile', kwargs={'username': USER_USERNAME})

URL_FOLLOW_INDEX_PAGE = reverse('posts:follow_index')

URL_PROFILE_FOLLOW_PAGE = reverse(
    'posts:profile_follow', kwargs={'username': USER_TO_FOLLOW_USERNAME}
)

URL_PROFILE_UNFOLLOW_PAGE = reverse(
    'posts:profile_unfollow', kwargs={'username': USER_TO_FOLLOW_USERNAME}
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_USERNAME)
        cls.user_to_follow = User.objects.create_user(
            username=USER_TO_FOLLOW_USERNAME
        )
        cls.not_follower = User.objects.create_user(username='TestUser3')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug=GROUP2_SLUG,
            description='Тестовое описание2',
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_DETAIL_PAGE = reverse(
            'posts:post_detail', kwargs={'post_id': PostsPagesTests.post.pk}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.user)
        self.user_to_follow_client = Client()
        self.user_to_follow_client.force_login(PostsPagesTests.user_to_follow)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(PostsPagesTests.not_follower)

    def asserts(self, post):
        self.assertEqual(post.author, PostsPagesTests.post.author)
        self.assertEqual(post.text, PostsPagesTests.post.text)
        self.assertEqual(post.group, PostsPagesTests.post.group)
        self.assertEqual(post.id, PostsPagesTests.post.pk)
        self.assertEqual(post.image, PostsPagesTests.post.image)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.authorized_client.get(URL_INDEX_PAGE)
        posts_count = Post.objects.all().count()
        first_object = response.context['page_obj'][0]
        self.asserts(first_object)
        self.assertEqual(len(response.context['page_obj']), posts_count)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(URL_GROUP_LIST_PAGE)
        posts_count = Post.objects.all().count()
        post = response.context['page_obj'][0]
        self.asserts(post)
        self.assertEqual(len(response.context['page_obj']), posts_count)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        posts_count = Post.objects.all().count()
        response = self.authorized_client.get(URL_PROFILE_PAGE)
        post = response.context['page_obj'][0]
        self.asserts(post)
        self.assertEqual(len(response.context['page_obj']), posts_count)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = self.authorized_client.get(PostsPagesTests.POST_DETAIL_PAGE)
        post = response.context['post']
        self.asserts(post)

    def test_new_post_does_not_appear_on_different_group_page(self):
        """Новый пост не появляется на странице не своей группы
        и в ленте пользователя, не подписанного на автора.
        """

        following_post = Post.objects.create(
            author=PostsPagesTests.user_to_follow,
            text='Отслеживаемый пост',
            group=PostsPagesTests.group
        )
        url_list = [URL_GROUP2_LIST_PAGE, URL_FOLLOW_INDEX_PAGE]
        for url in url_list:
            response = self.authorized_client.get(url)
            self.assertNotIn(following_post, response.context['page_obj'])

    def test_1(self):
        """Кол-во постов на страницах."""

        AMOUNT_OF_POSTS = settings.POSTS_AMOUNT + 2

        post = Post(
            author=PostsPagesTests.user,
            text='Тестовый пост',
            group=PostsPagesTests.group
        )
        post_list = [post] * AMOUNT_OF_POSTS
        Post.objects.bulk_create(post_list)

        post_following = Post(
            author=PostsPagesTests.user_to_follow,
            text='Тестовый пост',
        )
        post_list_following = [post_following] * AMOUNT_OF_POSTS
        Post.objects.bulk_create(post_list_following)
        Follow.objects.create(
            user=PostsPagesTests.user,
            author=PostsPagesTests.user_to_follow
        )
        pages_list = [
            [URL_INDEX_PAGE, 1, 10],
            [URL_INDEX_PAGE, 2, 10],
            [URL_INDEX_PAGE, 3, 5],
            [URL_PROFILE_PAGE, 1, 10],
            [URL_PROFILE_PAGE, 2, 3],
            [URL_GROUP_LIST_PAGE, 1, 10],
            [URL_GROUP_LIST_PAGE, 2, 3],
            [URL_FOLLOW_INDEX_PAGE, 1, 10],
            [URL_FOLLOW_INDEX_PAGE, 2, 2]
        ]
        for url, page, posts_on_page in pages_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url, {'page': page})
                self.assertEqual(
                    len(response.context['page_obj']), posts_on_page
                )

    def test_index_cache(self):
        response = self.authorized_client.get(URL_INDEX_PAGE)
        content = response.content
        Post.objects.all().delete()
        response_after_deletion = self.authorized_client.get(URL_INDEX_PAGE)
        content_after_deletion = response_after_deletion.content
        self.assertEqual(content, content_after_deletion)
        cache.clear()
        response_after_cache_clear = self.authorized_client.get(URL_INDEX_PAGE)
        content_after_cache_clear = response_after_cache_clear.content
        self.assertNotEqual(content, content_after_cache_clear)

    def test_follow(self):
        following_post = Post.objects.create(
            author=PostsPagesTests.user_to_follow,
            text='Отслеживаемый пост',
            group=PostsPagesTests.group
        )
        Follow.objects.create(
            user=PostsPagesTests.user,
            author=PostsPagesTests.user_to_follow
        )
        response = self.authorized_client.get(URL_FOLLOW_INDEX_PAGE)
        post = response.context['page_obj'][0]
        self.assertIn(following_post, response.context['page_obj'])
        self.assertEqual(post.author, following_post.author)
        self.assertEqual(post.text, following_post.text)
        self.assertEqual(post.group, following_post.group)
        self.assertEqual(post.id, following_post.pk)
        response = self.not_follower_client.get(URL_FOLLOW_INDEX_PAGE)

    def test_unfollow(self):
        Follow.objects.create(
            user=PostsPagesTests.user,
            author=PostsPagesTests.user_to_follow
        )
        self.authorized_client.get(URL_PROFILE_UNFOLLOW_PAGE)
        self.assertFalse(
            Follow.objects.filter(
                author=PostsPagesTests.user_to_follow,
                user=PostsPagesTests.user
            ).exists()
        )
