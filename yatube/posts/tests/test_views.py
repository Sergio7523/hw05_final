import shutil
import tempfile
from http import HTTPStatus
from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from ..models import Comment, Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.user_to_follow = User.objects.create_user(username='TestUser2')
        cls.not_follower = User.objects.create_user(username='TestUser3')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )

        cls.paginator_reverses_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username})
        ]
        cls.post_detail_page = reverse(
            'posts:post_detail', kwargs={'post_id': '1'}
        )
        cls.create_post_page = reverse('posts:post_create')
        cls.edit_post_page = reverse(
            'posts:post_edit', kwargs={'post_id': '1'}
        )
        cls.follow_page = reverse('posts:follow_index')
        cls.unfollow_page = reverse(
            'posts:profile_unfollow', kwargs={'username': cls.user_to_follow}
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

    def asserts(self, first_object):
        self.assertEqual(first_object.author, PostsPagesTests.user)
        self.assertEqual(first_object.text, 'Тестовый пост')
        self.assertEqual(first_object.group, PostsPagesTests.group)
        self.assertEqual(first_object.id, 1)
        self.assertEqual(first_object.image, PostsPagesTests.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            'posts/index.html': PostsPagesTests.paginator_reverses_names[0],
            'posts/group_list.html':
            PostsPagesTests.paginator_reverses_names[1],
            'posts/profile.html': PostsPagesTests.paginator_reverses_names[2],
            'posts/post_detail.html': PostsPagesTests.post_detail_page,
            'posts/create_post.html': PostsPagesTests.create_post_page
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[0]
        )
        first_object = response.context['page_obj'][0]
        self.asserts(first_object)

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[0]
        )
        first_object = response.context['page_obj'][0]
        self.asserts(first_object)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[2]
        )
        first_object = response.context['page_obj'][0]
        posts_count = len(response.context['page_obj'])
        self.asserts(first_object)
        self.assertEqual(
            Post.objects.filter(author=self.user).count(), posts_count
        )

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        comment = Comment.objects.create(
            author=PostsPagesTests.user,
            text='Тестовый комментарий',
            post=PostsPagesTests.post
        )
        response = self.authorized_client.get(PostsPagesTests.post_detail_page)
        first_object = response.context['post']
        self.asserts(first_object)
        self.assertIn(comment, response.context['comments'])

    def test_post_create_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.authorized_client.get(PostsPagesTests.create_post_page)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.authorized_client.get(PostsPagesTests.edit_post_page)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_appears_on_index_page(self):
        """Новый пост появляется на главной странице."""

        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост2',
            group=group2
        )
        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[0]
        )
        self.assertIn(post2, response.context['page_obj'])

    def test_new_post_appears_on_group_list_page(self):
        """Новый пост появляется на странице группы."""

        post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост2',
            group=self.group
        )
        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[1]
        )
        self.assertIn(post2, response.context['page_obj'])

    def test_new_post_appears_on_profile_page(self):
        """Новый пост появляется на странице пользователя."""

        post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост2',
            group=self.group
        )
        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[2]
        )
        self.assertIn(post2, response.context['page_obj'])

    def test_new_post_does_not_appear_on_different_group_page(self):
        """Новый пост не появляется на странице не своей группы."""

        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        post2 = Post.objects.create(
            author=self.user,
            text='Тестовый пост2',
            group=group2
        )
        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[1]
        )
        self.assertNotIn(post2, response.context['page_obj'])

    def test_amount_of_posts_on_pages(self):
        """Кол-во постов на страницах."""

        amount_of_posts = 12
        post = Post(
            author=PostsPagesTests.user,
            text='Тестовый пост',
            group=PostsPagesTests.group
        )
        post_list = [post for _ in range(amount_of_posts)]
        Post.objects.bulk_create(post_list)
        page_posts_amount = [(1, 10), (2, 3)]
        for page_pag, posts in page_posts_amount:
            for page in PostsPagesTests.paginator_reverses_names:
                with self.subTest(page=page):
                    response = self.guest_client.get(page, {'page': page_pag})
                    self.assertEqual(len(response.context['page_obj']), posts)

    def test_index_cache(self):
        response = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[0]
        )
        content = response.content
        Post.objects.all().delete()
        response_after_deletion = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[0]
        )
        content_after_deletion = response_after_deletion.content
        self.assertEqual(content, content_after_deletion)
        cache.clear()
        response_after_cache_clear = self.authorized_client.get(
            PostsPagesTests.paginator_reverses_names[0]
        )
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
        response = self.authorized_client.get(PostsPagesTests.follow_page)
        self.assertIn(following_post, response.context['page_obj'])
        response = self.not_follower_client.get(PostsPagesTests.follow_page)
        self.assertNotIn(following_post, response.context['page_obj'])
        self.assertTrue(
            Follow.objects.filter(
                author=PostsPagesTests.user_to_follow,
                user=PostsPagesTests.user
            ).exists()
        )
        response = self.guest_client.get(PostsPagesTests.follow_page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unfollow(self):
        Follow.objects.create(
            user=PostsPagesTests.user,
            author=PostsPagesTests.user_to_follow
        )
        self.authorized_client.get(PostsPagesTests.unfollow_page)
        self.assertFalse(
            Follow.objects.filter(
                author=PostsPagesTests.user_to_follow,
                user=PostsPagesTests.user
            ).exists()
        )
