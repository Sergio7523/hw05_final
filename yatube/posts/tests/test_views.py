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

ANOTHER_USER_USERNAME = 'TestUser2'

URL_GROUP_LIST_PAGE = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})

URL_GROUP2_LIST_PAGE = reverse(
    'posts:group_list', kwargs={'slug': GROUP2_SLUG}
)

URL_INDEX_PAGE = reverse('posts:index')

SECOND_INDEX_PAGE_URL = f'{URL_INDEX_PAGE}/?page=2'

SECOND_GROUP_LIST_PAGE_URL = f'{URL_GROUP_LIST_PAGE}?page=2'

URL_POST_CREATE_PAGE = reverse('posts:post_create')

URL_PROFILE_PAGE = reverse('posts:profile', kwargs={'username': USER_USERNAME})

SECOND_PROFILE_PAGE_URL = f'{URL_PROFILE_PAGE}?page=2'

URL_FOLLOW_INDEX_PAGE = reverse('posts:follow_index')

SECOND_FOLLOW_INDEX_PAGE_URL = f'{URL_FOLLOW_INDEX_PAGE}?page=2'

URL_PROFILE_FOLLOW_PAGE = reverse(
    'posts:profile_follow', kwargs={'username': ANOTHER_USER_USERNAME}
)

URL_PROFILE_UNFOLLOW_PAGE = reverse(
    'posts:profile_unfollow', kwargs={'username': ANOTHER_USER_USERNAME}
)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_USERNAME)
        cls.another_user = User.objects.create_user(
            username=ANOTHER_USER_USERNAME
        )
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
        cls.guest_client = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def asserts(self, post):
        self.assertEqual(post.author, PostsPagesTests.post.author)
        self.assertEqual(post.text, PostsPagesTests.post.text)
        self.assertEqual(post.group, PostsPagesTests.post.group)
        self.assertEqual(post.id, PostsPagesTests.post.pk)
        self.assertEqual(post.image, PostsPagesTests.post.image)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author.get(URL_INDEX_PAGE)
        self.assertEqual(len(response.context['page_obj']), 1)
        first_object = response.context['page_obj'][0]
        self.asserts(first_object)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author.get(URL_GROUP_LIST_PAGE)
        self.assertEqual(len(response.context['page_obj']), 1)
        post = response.context['page_obj'][0]
        self.asserts(post)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author.get(URL_PROFILE_PAGE)
        self.assertEqual(len(response.context['page_obj']), 1)
        post = response.context['page_obj'][0]
        self.asserts(post)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author.get(PostsPagesTests.POST_DETAIL_PAGE)
        post = response.context['post']
        self.asserts(post)

    def test_new_post_does_not_appear_on_different_group_page(self):
        """Новый пост не появляется на странице не своей группы
        и в ленте пользователя, не подписанного на автора.
        """
        following_post = Post.objects.create(
            author=PostsPagesTests.another_user,
            text='Отслеживаемый пост',
            group=PostsPagesTests.group
        )
        url_list = [URL_GROUP2_LIST_PAGE, URL_FOLLOW_INDEX_PAGE]
        for url in url_list:
            response = self.author.get(url)
            self.assertNotIn(following_post, response.context['page_obj'])

    def test_post_amount_on_pages_with_paginator(self):
        """Кол-во постов на страницах с паджинатором."""
        AMOUNT_OF_POSTS = settings.POSTS_AMOUNT + 1
        post = Post(
            author=PostsPagesTests.user,
            text='Тестовый пост',
            group=PostsPagesTests.group
        )
        post_list = [post] * AMOUNT_OF_POSTS
        Post.objects.bulk_create(post_list)

        Follow.objects.create(
            user=PostsPagesTests.another_user,
            author=PostsPagesTests.user
        )
        posts_count = Post.objects.all().count()
        posts_amount_on_second_page = posts_count - settings.POSTS_AMOUNT
        pages_list = [
            [URL_INDEX_PAGE, settings.POSTS_AMOUNT],
            [SECOND_INDEX_PAGE_URL, posts_amount_on_second_page],
            [URL_PROFILE_PAGE, settings.POSTS_AMOUNT],
            [SECOND_PROFILE_PAGE_URL, posts_amount_on_second_page],
            [URL_GROUP_LIST_PAGE, settings.POSTS_AMOUNT],
            [SECOND_GROUP_LIST_PAGE_URL, posts_amount_on_second_page],
            [URL_FOLLOW_INDEX_PAGE, settings.POSTS_AMOUNT],
            [SECOND_FOLLOW_INDEX_PAGE_URL, posts_amount_on_second_page]
        ]
        for url, posts_on_page in pages_list:
            with self.subTest(url=url):
                response = self.another.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), posts_on_page
                )

    def test_index_cache(self):
        response = self.author.get(URL_INDEX_PAGE)
        content = response.content
        Post.objects.all().delete()
        response_after_deletion = self.author.get(URL_INDEX_PAGE)
        content_after_deletion = response_after_deletion.content
        self.assertEqual(content, content_after_deletion)
        cache.clear()
        response_after_cache_clear = self.author.get(URL_INDEX_PAGE)
        content_after_cache_clear = response_after_cache_clear.content
        self.assertNotEqual(content, content_after_cache_clear)

    def test_unfollow(self):
        Follow.objects.create(
            user=PostsPagesTests.user,
            author=PostsPagesTests.another_user
        )
        self.author.get(URL_PROFILE_UNFOLLOW_PAGE)
        self.assertFalse(
            Follow.objects.filter(
                author=PostsPagesTests.another_user,
                user=PostsPagesTests.user
            ).exists()
        )

    def test_follow(self):
        self.author.get(URL_PROFILE_FOLLOW_PAGE)
        self.assertTrue(
            Follow.objects.filter(
                author=PostsPagesTests.another_user,
                user=PostsPagesTests.user
            ).exists()
        )

    def test_follow_page(self):
        Follow.objects.create(
            author=PostsPagesTests.user,
            user=PostsPagesTests.another_user
        )
        response = self.another.get(URL_FOLLOW_INDEX_PAGE)
        self.assertEqual(len(response.context['page_obj']), 1)
        post = response.context['page_obj'][0]
        self.asserts(post)
