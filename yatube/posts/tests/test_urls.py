from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(username='Author')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            text='чонитьтам',
            author=cls.author
        )
        cls.group = Group.objects.create(
            title='Группа',
            slug='test_slug',
            description='описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.auth_client = Client()
        self.authorized_client.force_login(self.user)
        self.auth_client.force_login(self.author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/about/tech/': 'about/tech.html',
            '/about/author/': 'about/author.html'
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth_client.get(address)
                self.assertTemplateUsed(response, template)
