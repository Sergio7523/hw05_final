import shutil
import tempfile

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

USER_USERNAME = 'TestUser'
ANOTHER_USER_USERNAME = 'TestUser2'
GROUP1_SLUG = 'test-slug'
GROUP2_SLUG = 'test-slug2'
URL_PROFILE_PAGE = reverse('posts:profile', args=[USER_USERNAME])
URL_LOGIN_PAGE = reverse('users:login')
URL_POST_CREATE_PAGE = reverse('posts:post_create')
URL_REDIRECT_POST_CREATE_PAGE = f'{URL_LOGIN_PAGE}?next={URL_POST_CREATE_PAGE}'
UPLOAD_TO = Post._meta.get_field("image").upload_to


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
        cls.user = User.objects.create_user(username=USER_USERNAME)
        cls.another_user = User.objects.create_user(
            username=ANOTHER_USER_USERNAME
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP1_SLUG,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug=GROUP2_SLUG,
            description='Тестовое описание2',
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
        cls.post_form_data = {
            'text': 'Текст созданного поста',
            'group': cls.group.id,
            'image': cls.uploaded,
        }
        cls.form_data_edit = {
            'text': 'Тестовый текст 1',
            'group': cls.group2.id,
            'image': cls.uploaded_second
        }
        cls.URL_POST_DETAIL_PAGE = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.URL_POST_EDIT_PAGE = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )
        cls.URL_REDIRECT_POST_EDIT_PAGE = (
            f'{URL_LOGIN_PAGE}?next={cls.URL_POST_EDIT_PAGE}'
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another_client = Client()
        cls.another_client.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        Post.objects.all().delete()
        response = self.authorized_client.post(
            URL_POST_CREATE_PAGE,
            data=PostCreateFormTests.post_form_data,
            follow=True
        )
        post_list = Post.objects.all()
        self.assertEqual(len(post_list), 1)
        post = post_list.latest('pk')
        self.assertEqual(
            post.text, PostCreateFormTests.post_form_data['text']
        )
        self.assertEqual(
            post.group.id, PostCreateFormTests.post_form_data['group']
        )
        self.assertEqual(post.author, PostCreateFormTests.user)
        self.assertEqual(post.image, f'{UPLOAD_TO}{IMAGE_NAME}')
        self.assertRedirects(response, URL_PROFILE_PAGE)

    def test_guest_client_can_not_create_post(self):
        Post.objects.all().delete()
        response = self.guest_client.post(
            URL_POST_CREATE_PAGE,
            data=PostCreateFormTests.post_form_data,
            follow=True,
        )
        self.assertRedirects(response, URL_REDIRECT_POST_CREATE_PAGE)
        self.assertEqual(Post.objects.all().count(), 0)

    def test_edit_post(self):
        self.authorized_client.post(
            PostCreateFormTests.URL_POST_EDIT_PAGE,
            data=PostCreateFormTests.form_data_edit,
            follow=True
        )
        post = Post.objects.get(id=PostCreateFormTests.post.id)
        self.assertEqual(post.text, PostCreateFormTests.form_data_edit['text'])
        self.assertEqual(
            post.group.id, PostCreateFormTests.form_data_edit['group']
        )
        self.assertEqual(post.author, PostCreateFormTests.post.author)
        self.assertEqual(
            post.image,
            f'{UPLOAD_TO}{PostCreateFormTests.form_data_edit["image"]}'
        )

    def test_guest_client_and_not_author_can_not_edit_post(self):
        post_before_edit = PostCreateFormTests.post
        cases1 = [
            [self.guest_client, self.URL_REDIRECT_POST_EDIT_PAGE],
            [self.another_client, self.URL_POST_DETAIL_PAGE]
        ]
        for client, redirect_url in cases1:
            with self.subTest(client=client, redirect_url=redirect_url):
                response = client.post(
                    PostCreateFormTests.URL_POST_EDIT_PAGE,
                    data=PostCreateFormTests.form_data_edit,
                    follow=True
                )
                post = Post.objects.get(id=PostCreateFormTests.post.id)
                self.assertEqual(post.text, post_before_edit.text)
                self.assertEqual(post.group.id, post_before_edit.group.id)
                self.assertEqual(post.author, post_before_edit.author)
                self.assertEqual(post.image, post_before_edit.image)
                self.assertRedirects(response, redirect_url)

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
            with self.subTest(url=url):
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
        cls.user = User.objects.create_user(username=USER_USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP1_SLUG,
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

    def test_add_comment(self):
        Comment.objects.all().delete()
        self.authorized_client.post(
            PostCreateCommentTests.URL_ADD_COMMENT_PAGE,
            data=PostCreateCommentTests.comment_data,
            follow=True,
        )
        comments_list = Comment.objects.all()
        self.assertEqual(len(comments_list), 1)
        comment = comments_list.latest('pk')
        self.assertEqual(
            comment.text, PostCreateCommentTests.comment_data['text']
        )
        self.assertEqual(comment.author, PostCreateCommentTests.user)
        self.assertEqual(comment.post, PostCreateCommentTests.post)

    def test_guest_client_can_not_add_comment(self):
        Comment.objects.all().delete()
        response = self.guest_client.post(
            PostCreateCommentTests.URL_ADD_COMMENT_PAGE,
            data=PostCreateCommentTests.comment_data,
        )
        self.assertRedirects(
            response, PostCreateCommentTests.URL_REDIRECT_COMMENT_PAGE
        )
        self.assertEqual(Comment.objects.all().count(), 0)
