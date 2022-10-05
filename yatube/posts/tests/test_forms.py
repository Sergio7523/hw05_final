import shutil

import tempfile

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

USER_USERNAME = 'TestUser'

URL_PROFILE_PAGE = reverse('posts:profile', args=[USER_USERNAME])

URL_LOGIN_PAGE = reverse('users:login')

URL_POST_CREATE_PAGE = reverse('posts:post_create')

URL_REDIRECT_POST_CREATE_PAGE = f'{URL_LOGIN_PAGE}?next={URL_POST_CREATE_PAGE}'


SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

IMAGE_NAME = 'small.gif'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.uploaded_second = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.URL_POST_EDIT_PAGE = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id,
            'image': PostCreateFormTests.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        created_post = Post.objects.latest('pk')
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(created_post.group.id, form_data['group'])
        self.assertEqual(created_post.author, PostCreateFormTests.user)
        self.assertEqual(created_post.image, f'posts/{IMAGE_NAME}')
        self.assertRedirects(response, URL_PROFILE_PAGE)

    def test_guest_client_can_not_create_post(self):
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, URL_REDIRECT_POST_CREATE_PAGE)

    def test_edit_post(self):
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый текст',
            group=PostCreateFormTests.group,
        )
        form_data_edit = {
            'text': 'Тестовый текст 1',
            'group': '',
            'image': PostCreateFormTests.uploaded_second
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=form_data_edit,
            follow=True
        )
        self.assertEqual(
            Post.objects.get(id=post.id).text, form_data_edit['text']
        )
        self.assertEqual(Post.objects.get(id=post.id).group, None)
        self.assertEqual(
            Post.objects.get(id=post.id).image, 'posts/small2.gif'
        )

    def test_create_edit_posts_show_correct_form(self):
        """Шаблоны post_create и post_edit сформированы
         с правильным контекстом.
        """

        responses_pages_list = [
            self.authorized_client.get(URL_POST_CREATE_PAGE),
            self.authorized_client.get(PostCreateFormTests.URL_POST_EDIT_PAGE)
        ]

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for response in responses_pages_list:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = (response.context.get('form').
                                  fields.get(value))
                    self.assertIsInstance(form_field, expected)


class PostCreateCommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Тестовый пост'
        )
        cls.comment_data = {
            'text': 'Тестовый комментарий',
            'author': PostCreateCommentTests.user
        }
        cls.URL_ADD_COMMENT_PAGE = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.pk}
        )
        cls.URL_COMMENT_PAGE = reverse(
            'posts:add_comment',
            kwargs={'post_id': PostCreateCommentTests.post.pk}
        )
        cls.URL_REDIRECT_COMMENT_PAGE = (
            f'{URL_LOGIN_PAGE}?next={cls.URL_COMMENT_PAGE}'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateCommentTests.user)

    def test_guest_client_can_not_add_comment(self):
        response = self.guest_client.post(
            PostCreateCommentTests.URL_ADD_COMMENT_PAGE,
            data=PostCreateCommentTests.comment_data,
        )
        self.assertRedirects(
            response, PostCreateCommentTests.URL_REDIRECT_COMMENT_PAGE
        )

    def test_add_comment(self):
        self.authorized_client.post(
            PostCreateCommentTests.URL_ADD_COMMENT_PAGE,
            data=PostCreateCommentTests.comment_data,
            follow=True,
        )
        comment = Comment.objects.get(id=1)
        self.assertEqual(
            comment.text, PostCreateCommentTests.comment_data['text']
        )
        self.assertEqual(
            comment.author, PostCreateCommentTests.comment_data['author']
        )
