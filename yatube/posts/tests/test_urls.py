from http import HTTPStatus
from django.test import TestCase, Client
from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.not_author = User.objects.create_user(username='TestNotAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )
        cls.post_create_page = '/create/'
        cls.post_edit_page = f'/posts/{cls.post.pk}/edit/'
        cls.main_page = '/'
        cls.group_list_page = f'/group/{cls.group.slug}/'
        cls.profile_page = '/profile/TestUser/'
        cls.post_detail_page = f'/posts/{cls.post.pk}/'
        cls.redirect_post_create_page = '/auth/login/?next=/create/'
        cls.redirect_post_edit_page = (
            f'/auth/login/?next=/posts/{cls.post.pk}/edit/'
        )
        cls.public_pages_list = [
            (cls.main_page, 'posts/index.html'),
            (cls.group_list_page, 'posts/group_list.html'),
            (cls.profile_page, 'posts/profile.html'),
            (cls.post_detail_page, 'posts/post_detail.html'),
        ]
        cls.private_pages_list = [
            (cls.post_create_page, 'posts/create_post.html'),
            (cls.post_edit_page, 'posts/create_post.html'),
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(PostsURLTests.not_author)

    def test_public_url_exists_and_accessible_for_all_users(self):
        """Общедоступные cnраницы доступны любому пользователю и используют
        соответствующий шаблон.
        """

        self.clients = [self.guest_client, self.authorized_client]
        for client in self.clients:
            for address, template in PostsURLTests.public_pages_list:
                with self.subTest(client=client, address=address):
                    response = self.client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTemplateUsed(response, template)

    def test_private_url_exists_and_accessible_for_authorized_users(self):
        """Приватные страницы доступны авторизованному пользователю
        и используют соответствующий шаблон.
        """

        self.client = self.authorized_client
        for address, template in PostsURLTests.private_pages_list:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page_is_available_for_all_ausers(self):
        """Несуществующая страница доступна всем пользователям."""

        self.clients = [self.guest_client, self.authorized_client]
        for client in self.clients:
            response = client.get('/unexisting_page/')
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_ubevailable_for_not_author(self):
        """Страница /posts/<post_id>/edit/ не доступна не автору публикации."""

        response = self.not_author_client.get(
            PostsURLTests.post_edit_page
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_redirect_anonymous_on_login(self):
        """Страница перенаправит анонимного пользователя на страницу логина."""

        url_redirect_to_url = {
            PostsURLTests.post_create_page:
            PostsURLTests.redirect_post_create_page,
            PostsURLTests.post_edit_page:
            PostsURLTests.redirect_post_edit_page
        }
        for url, redirect in url_redirect_to_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)
