from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='группа',
            slug='group_slug',
            description='описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        Post.objects.bulk_create(
            [Post(
                text=f'Пост номер {i}',
                author=self.user,
                group=self.group,
            )for i in range(13)]
        )

    def test_paginator(self):
        url_names = {
            'posts:index': {},
            'posts:group_list': {'slug': self.group.slug},
            'posts:profile': {'username': self.user},
        }
        page_counts = [10, 3]

        for url_name, url_kwargs in url_names.items():
            with self.subTest(url_name=url_name):
                for page_num, page_count in enumerate(page_counts, start=1):
                    with self.subTest(page_num=page_num,
                                      page_count=page_count):
                        response = self.client.get(
                            reverse(url_name,
                                    kwargs=url_kwargs) + f'?page={page_num}')
                        self.assertEqual(len(
                            response.context['page_obj']), page_count)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='cats',
            slug='group_slug',
            description='описание'
        )
        cls.post = Post.objects.create(
            text='чонитьтам',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='New_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context['page_obj'][0]
        self.assertEqual(page_obj, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        ))
        _object = response.context['page_obj'][0]
        text = _object.text
        author = _object.author.username
        self.assertEqual(text, self.post.text)
        self.assertEqual(author, self.author.username)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author}))
        _object = response.context['page_obj'][0]
        post_title = _object.text
        post_pub_date = _object.pub_date
        post_author = _object.author
        post_group = _object.group
        self.assertEqual(post_title, self.post.text)
        self.assertEqual(post_pub_date, self.post.pub_date)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_group, self.post.group)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post'), self.post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        fields_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in fields_form.items():
            with self.subTest(value=value):
                field_form = response.context.get('form').fields.get(value)
                self.assertIsInstance(field_form, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        fields_form = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in fields_form.items():
            with self.subTest(value=value):
                field_form = response.context.get('form').fields.get(value)
                self.assertIsInstance(field_form, expected)


class PostDisplayTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(username='New_user')
        cls.group = Group.objects.create(
            title='группа',
            slug='slug',
            description='описание группы'
        )
        cls.post = Post.objects.create(
            text='текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.client = Client()

    def test_post_on_index(self):
        """Пост повявляется на главной странице"""
        response = self.client.get(reverse('posts:index'))
        self.assertContains(response, self.post.text)

    def test_post_on_group_page(self):
        """Пост появляется на странице группы"""
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': self.group.slug}))
        self.assertContains(response, self.post.text)

    def test_post_on_author_profile(self):
        """Пост появляется на странице автора"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertContains(response, self.post.text)

    def test_post_not_in_wrong_group(self):
        """Пост не появляется на странице другой группы"""
        wrong_group = Group.objects.create(
            title='не та группа',
            slug='slug2',
            description='описание не той группы'
        )
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': wrong_group.slug}))
        self.assertNotContains(response, self.post.text)
