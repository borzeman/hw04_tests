import shutil
import tempfile

from django.test import Client, override_settings, TestCase
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание тестовой группы')

        cls.post_text_form = {'text': 'Измененный тект',
                              'group': cls.group.pk,
                              }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает новую запись в базе данных."""
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.post_text_form,
            follow=True)

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        post = Post.objects.first()
        self.assertEqual(post.text, self.post_text_form['text'])
        self.assertEqual(post.group.pk, self.post_text_form['group'])
        self.assertEqual(post.author.username, self.user.username)

    def test_post_edit(self):
        """При изменении валидной формы изменяется запись в базе данных."""
        self.post_without_group = Post.objects.create(
            text='текст поста без группы',
            author=self.user
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])

    def test_edit_other_users_post(self):
        """При попытке изменить пост другого пользователя, пост не меняется."""
        user2 = User.objects.create_user(username='user2')
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        client2 = Client()
        client2.force_login(user2)
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group.id
        }
        response = client2.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 403)
        post.refresh_from_db()
        self.assertNotEqual(post.text, form_data['text'])

    def test_create_post_unauthorized(self):
        """При создании поста неавторизованным юзером пост не создается"""
        unauthorized_client = Client()
        response = unauthorized_client.post(
            reverse('posts:post_create'),
            data=self.post_text_form,
            follow=True)
        self.assertEqual(Post.objects.count(), 0)
        self.assertRedirects(response, reverse(
            'login') + '?next=' + reverse('posts:post_create'))
