import shutil

import tempfile

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.apps import PostsConfig
from posts.models import Comment, Group, Post, User

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
SECOND_IMAGE_NAME = 'small2.gif'

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.another_user = User.objects.create_user(username='TestUser2')
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
            name=SECOND_IMAGE_NAME,
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.URL_POST_EDIT_PAGE = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostCreateFormTests.user)
        cls.another_client = Client()
        cls.another_client.force_login(PostCreateFormTests.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст созданного поста',
            'group': PostCreateFormTests.group.id,
            'image': PostCreateFormTests.uploaded,
        }
        id_list = Post.objects.values_list('id', flat=True).order_by('id')
        self.assertEqual(len(id_list), 1)
        first_post_id = id_list[0]
        response = self.authorized_client.post(
            URL_POST_CREATE_PAGE,
            data=form_data,
            follow=True
        )
        post_list = Post.objects.exclude(id=first_post_id)
        post_list_ids = post_list.values_list('id', flat=True).order_by('id')
        self.assertEqual(len(post_list_ids), 1)
        created_post_id = post_list_ids[0]
        created_post = Post.objects.get(id=created_post_id)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.group.id, form_data['group'])
        self.assertEqual(created_post.author, PostCreateFormTests.user)
        self.assertEqual(
            created_post.image, f'{PostsConfig.name}/{IMAGE_NAME}'
        )
        self.assertRedirects(response, URL_PROFILE_PAGE)

    def test_guest_client_can_not_create_post(self):
        posts_amount_before_creation_attempt = Post.objects.all().count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id,
            'image': PostCreateFormTests.uploaded,
        }
        response = self.guest_client.post(
            URL_POST_CREATE_PAGE,
            data=form_data,
            follow=True,
        )
        posts_amount_after_creation_attempt = Post.objects.all().count()
        self.assertRedirects(response, URL_REDIRECT_POST_CREATE_PAGE)
        self.assertEqual(
            posts_amount_before_creation_attempt,
            posts_amount_after_creation_attempt
        )

    def test_edit_post(self):
        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        form_data_edit = {
            'text': 'Тестовый текст 1',
            'group': group2.id,
            'image': PostCreateFormTests.uploaded_second
        }
        self.authorized_client.post(
            PostCreateFormTests.URL_POST_EDIT_PAGE,
            data=form_data_edit,
            follow=True
        )
        post = Post.objects.get(id=PostCreateFormTests.post.id)
        self.assertEqual(post.text, form_data_edit['text'])
        self.assertEqual(post.group.id, form_data_edit['group'])
        self.assertEqual(post.author, PostCreateFormTests.user)
        self.assertEqual(
            post.image, f'{PostsConfig.name}/{form_data_edit["image"]}'
        )

    def test_guest_client_and_not_author_can_not_edit_post(self):
        clients_list = [self.guest_client, self.another_client]

        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        form_data_edit = {
            'text': 'Тестовый текст 1',
            'group': group2.id,
            'image': PostCreateFormTests.uploaded_second
        }
        for client in clients_list:
            client.post(
                PostCreateFormTests.URL_POST_EDIT_PAGE,
                data=form_data_edit,
                follow=True
            )
            post = Post.objects.get(id=PostCreateFormTests.post.id)
            self.assertNotEqual(post.text, form_data_edit['text'])
            self.assertNotEqual(post.group.id, form_data_edit['group'])
            self.assertEqual(post.author, PostCreateFormTests.user)
            self.assertNotEqual(
                post.image, f'{PostsConfig.name}/{form_data_edit["image"]}'
            )

    def test_create_edit_posts_show_correct_form(self):
        """Шаблоны post_create и post_edit сформированы
         с правильным контекстом.
        """

        url_list = [
            URL_POST_CREATE_PAGE, PostCreateFormTests.URL_POST_EDIT_PAGE
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for url in url_list:
            for value, expected in form_fields.items():
                response = self.authorized_client.get(url)
                form_field = (
                    response.context.get('form').fields.get(value)
                )
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
        }
        cls.URL_ADD_COMMENT_PAGE = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.pk}
        )
        cls.URL_REDIRECT_COMMENT_PAGE = (
            f'{URL_LOGIN_PAGE}?next={cls.URL_ADD_COMMENT_PAGE}'
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PostCreateCommentTests.user)

    def test_guest_client_can_not_add_comment(self):
        response = self.guest_client.post(
            PostCreateCommentTests.URL_ADD_COMMENT_PAGE,
            data=PostCreateCommentTests.comment_data,
        )
        self.assertRedirects(
            response, PostCreateCommentTests.URL_REDIRECT_COMMENT_PAGE
        )
        self.assertEqual(Comment.objects.all().count(), 0)

    def test_add_comment(self):
        self.authorized_client.post(
            PostCreateCommentTests.URL_ADD_COMMENT_PAGE,
            data=PostCreateCommentTests.comment_data,
            follow=True,
        )
        comment_list = Comment.objects.all()
        comments_list_ids = comment_list.values_list(
            'id', flat=True
        ).order_by('id')
        self.assertEqual(len(comments_list_ids), 1)
        comment_id = comments_list_ids[0]
        comment = Comment.objects.get(id=comment_id)
        self.assertEqual(
            comment.text, PostCreateCommentTests.comment_data['text']
        )
        self.assertEqual(comment.author, PostCreateCommentTests.user)
        self.assertEqual(comment.post, PostCreateCommentTests.post)
