from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User

GROUP_SLUG = 'test-slug'
USER_USERNAME = 'TestUser'
URL_GROUP_LIST_PAGE = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
URL_INDEX_PAGE = reverse('posts:index')
URL_POST_CREATE_PAGE = reverse('posts:post_create')
URL_LOGIN_PAGE = reverse('users:login')
URL_PROFILE_PAGE = reverse('posts:profile', kwargs={'username': USER_USERNAME})
URL_UNEXISTING_PAGE = '/unexisting_page/'
URL_FOLLOW_INDEX_PAGE = reverse('posts:follow_index')
URL_PROFILE_FOLLOW_PAGE = reverse(
    'posts:profile_follow', kwargs={'username': USER_USERNAME}
)
URL_PROFILE_UNFOLLOW_PAGE = reverse(
    'posts:profile_unfollow', kwargs={'username': USER_USERNAME}
)
URL_REDIRECT_FOLLOW_INDEX_PAGE = (
    f'{URL_LOGIN_PAGE}?next={URL_FOLLOW_INDEX_PAGE}'
)
URL_REDIRECT_PROFILE_FOLLOW_PAGE = (
    f'{URL_LOGIN_PAGE}?next={URL_PROFILE_FOLLOW_PAGE}'
)
URL_REDIRECT_PROFILE_UNFOLLOW_PAGE = (
    f'{URL_LOGIN_PAGE}?next={URL_PROFILE_UNFOLLOW_PAGE}'
)
URL_REDIRECT_POST_CREATE_PAGE = (
    f'{URL_LOGIN_PAGE}?next={URL_POST_CREATE_PAGE}'
)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_USERNAME)
        cls.not_author = User.objects.create_user(username='TestNotAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )
        cls.URL_POST_EDIT_PAGE = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsURLTests.post.pk}
        )
        cls.URL_POST_DETAIL_PAGE = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsURLTests.post.pk}
        )
        cls.URL_REDIRECT_POST_EDIT_PAGE = (
            f'{URL_LOGIN_PAGE}?next={cls.URL_POST_EDIT_PAGE}'
        )
        cls.guest_client = Client()
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.other_client = Client()
        cls.other_client.force_login(cls.not_author)

    def test_all_urls_use_correct_access_auth(self):
        cases = [
            [self.guest_client, URL_INDEX_PAGE, HTTPStatus.OK],
            [self.guest_client, URL_GROUP_LIST_PAGE, HTTPStatus.OK],
            [self.guest_client, URL_PROFILE_PAGE, HTTPStatus.OK],
            [
                self.guest_client,
                PostsURLTests.URL_POST_DETAIL_PAGE,
                HTTPStatus.OK
            ],
            [self.guest_client, URL_UNEXISTING_PAGE, HTTPStatus.NOT_FOUND],
            [self.author, URL_POST_CREATE_PAGE, HTTPStatus.OK],
            [
                self.author,
                PostsURLTests.URL_POST_EDIT_PAGE,
                HTTPStatus.OK
            ],
            [self.guest_client, URL_POST_CREATE_PAGE, HTTPStatus.FOUND],
            [
                self.guest_client,
                PostsURLTests.URL_POST_EDIT_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.other_client,
                PostsURLTests.URL_POST_EDIT_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.guest_client,
                URL_FOLLOW_INDEX_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.guest_client,
                URL_PROFILE_FOLLOW_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.guest_client,
                URL_PROFILE_UNFOLLOW_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.other_client,
                URL_FOLLOW_INDEX_PAGE,
                HTTPStatus.OK
            ],
            [
                self.other_client,
                URL_PROFILE_FOLLOW_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.other_client,
                URL_PROFILE_UNFOLLOW_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.author,
                URL_PROFILE_FOLLOW_PAGE,
                HTTPStatus.FOUND
            ],
            [
                self.author,
                URL_PROFILE_UNFOLLOW_PAGE,
                HTTPStatus.NOT_FOUND
            ]
        ]
        for client, url, status in cases:
            with self.subTest(client=client, url=url, status=status):
                response = client.get(url)
                self.assertEqual(response.status_code, status)

    def test_pages_use_correct_templates(self):
        """Cтраницы сайта используют соответствующие шаблоны."""
        cases = [
            [self.author, URL_INDEX_PAGE, 'posts/index.html'],
            [
                self.author,
                URL_GROUP_LIST_PAGE,
                'posts/group_list.html'
            ],
            [self.author, URL_PROFILE_PAGE, 'posts/profile.html'],
            [
                self.author,
                PostsURLTests.URL_POST_DETAIL_PAGE,
                'posts/post_detail.html'
            ],
            [
                self.author,
                URL_POST_CREATE_PAGE,
                'posts/create_post.html'
            ],
            [
                self.author,
                PostsURLTests.URL_POST_EDIT_PAGE,
                'posts/create_post.html'
            ],
            [
                self.author,
                URL_FOLLOW_INDEX_PAGE,
                'posts/follow.html'
            ]
        ]
        for client, url, template in cases:
            with self.subTest(client=client, url=url, template=template):
                response = client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect(self):
        """Проверка редиректов."""
        url_redirect_to_url = [
            [
                self.guest_client,
                URL_POST_CREATE_PAGE,
                URL_REDIRECT_POST_CREATE_PAGE
            ],
            [
                self.guest_client,
                PostsURLTests.URL_POST_EDIT_PAGE,
                PostsURLTests.URL_REDIRECT_POST_EDIT_PAGE
            ],
            [
                self.guest_client,
                URL_FOLLOW_INDEX_PAGE,
                URL_REDIRECT_FOLLOW_INDEX_PAGE
            ],
            [
                self.guest_client,
                URL_PROFILE_FOLLOW_PAGE,
                URL_REDIRECT_PROFILE_FOLLOW_PAGE
            ],
            [
                self.guest_client,
                URL_PROFILE_UNFOLLOW_PAGE,
                URL_REDIRECT_PROFILE_UNFOLLOW_PAGE
            ],
            [
                self.other_client,
                PostsURLTests.URL_POST_EDIT_PAGE,
                PostsURLTests.URL_POST_DETAIL_PAGE
            ],
            [
                self.other_client,
                URL_PROFILE_FOLLOW_PAGE,
                URL_PROFILE_PAGE
            ],
            [
                self.other_client,
                URL_PROFILE_UNFOLLOW_PAGE,
                URL_PROFILE_PAGE
            ]
        ]
        for client, url, redirect_url in url_redirect_to_url:
            with self.subTest(
                client=client,
                url=url,
                redirect_url=redirect_url
            ):
                response = client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)
