import shutil
import tempfile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Comment, Group, Post, User


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
        cls.profile_url = reverse('posts:profile', args=[cls.user.username])
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
        cls.data = {
            'text': 'Тестовый текст',
            'group': cls.group.id,
            'image': cls.uploaded,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=PostCreateFormTests.data,
            follow=True,
        )
        post = response.context['page_obj'][0]
        self.assertRedirects(response, PostCreateFormTests.profile_url)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, PostCreateFormTests.data['text'])
        self.assertEqual(post.group.id, PostCreateFormTests.data['group'])
        self.assertEqual(post.author, PostCreateFormTests.user)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_client_can_not_create_post(self):
        self.guest_client.post(
            reverse('posts:post_create'),
            data=PostCreateFormTests.data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(text='Тестовый текст').exists())

    def test_edit_post(self):
        post = Post.objects.create(
            author=PostCreateFormTests.user,
            text='Тестовый текст',
            group=PostCreateFormTests.group,
        )
        group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        edit_post_data = {
            'text': 'Тестовый текст2',
            'group': group2.id,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=edit_post_data,
            follow=True,
        )
        post = response.context['post']
        self.assertEqual(post.text, 'Тестовый текст2')
        self.assertEqual(Post.objects.count(), posts_count)
        self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostCreateFormTests.group.slug}
            )
        )
        self.assertEqual(Post.objects.filter(group=self.group).count(), 0)


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
        cls.comment_data = {'text': 'Тестовый комментарий'}
        cls.reverse_add_comment = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.pk}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateCommentTests.user)

    def test_guest_client_can_not_add_comment(self):
        self.guest_client.post(
            PostCreateCommentTests.reverse_add_comment,
            data=PostCreateCommentTests.comment_data,
            follow=True,
        )
        self.assertFalse(
            Comment.objects.filter(text='Тестовый комментарий').exists()
        )

    def test_add_comment(self):
        self.authorized_client.post(
            PostCreateCommentTests.reverse_add_comment,
            data=PostCreateCommentTests.comment_data,
            follow=True,
        )
        self.assertTrue(
            Comment.objects.filter(text='Тестовый комментарий').exists()
        )
