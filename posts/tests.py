from django.test import TestCase, Client
import time
from .models import Post, User, Group, Follow, Comment
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import tempfile
User = get_user_model()


class TestPosts(TestCase):
    def setUp(self):
        self.client = Client()
        # создаём пользователя
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        user = User.objects.get(username="sarah")
        self.client.force_login(user)
        self.test_post = 'Post from user'

    def test_new_post_not_autoriz(self):
        """
        Неавторизованный посетитель не может опубликовать пост
         (его редиректит на страницу входа)
        """
        self.client.logout()
        response = self.client.get("/new/", follow=True)   # попытка зайди на страницу new, редирект
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/auth/login/?next=/new/')    # равен ли ответ редиректу

    def test_appear_post(self):
        """
        После публикации поста новая запись появляется на главной странице сайта (index),
        на персональной странице пользователя (profile), и на отдельной странице поста (post)
        """
        self.client.post("/new/", {"text": self.test_post})

        response = self.client.get('/')
        self.assertContains(response, self.test_post)

        response = self.client.get('/sarah/')
        self.assertContains(response, self.test_post)

        response = self.client.get('/sarah/1/')
        self.assertContains(response, self.test_post)

    @override_settings(CACHES=settings.TEST_CACHES)
    def test_edit_post(self):
        """
        Авторизованный пользователь может отредактировать свой пост
         и его содержимое изменится на всех связанных страницах
        """
        self.client.post("/new/", {"text": self.test_post}, follow=True)

        post = Post.objects.get(author=self.user)
        new_post = 'New post'
        self.client.post(f'/sarah/{post.id}/edit/', {"text": new_post}, follow=True)

        response = self.client.get('/sarah/')
        self.assertContains(response, new_post)

        response = self.client.get('/sarah/1/')
        self.assertContains(response, new_post)
        response = self.client.get('/')
        self.assertContains(response, new_post)

    def test_cache(self):
        """
        Проверка работы кэша.
        """
        test_post = 'Test cache'
        self.client.post("/new/", {"text": test_post}, Follow=True)

        response = self.client.get('/')
        self.assertNotContains(response, test_post)

        cache.clear()
        response = self.client.get('/')
        self.assertContains(response, test_post)

    def tearDown(self):
        print("tearDown")


class SimpleTest(TestCase):
    def setUp(self):
        self.client = Client()
        # создаём пользователя
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        user = User.objects.get(username="sarah")
        self.client.force_login(user)
        self.post = Post.objects.create(
            text="It's driving me crazy!",
            author=self.user)

    def test_profile(self):
        """
        После регистрации пользователя создается его персональная страница (profile)
        """
        response = self.client.get('/sarah/')
        self.assertEqual(response.status_code, 200)
        # Проверка того, что мы используем правильный шаблон
        self.assertTemplateUsed(response, 'profile.html')

    def test_new_post(self):
        """
        Авторизованный пользователь может опубликовать пост (new)
        """
        # формируем GET-запрос к странице сайта

        response = self.client.get("/sarah/1/")
        self.assertTemplateUsed(response, 'post.html')

    def test_wrong_url_return_404(self):
        """
        Возвращает ли сервер код 404, если страница не найдена.
        """
        response = self.client.get('sarah/1000')
        self.assertEqual(response.status_code, 404)


    def test_comment(self):
        """
        Только авторизированный пользователь может комментировать посты.
        """
        comment = Comment.objects.create(post=self.post, text="First comment", author=self.user)
        response = self.client.post(f'/{self.user.username}/{self.post.pk}/')
        self.assertContains(response, comment.text)

    def tearDown(self):
        print("tearDown")


class TestImage(TestCase):

    def setUp(self):
        self.client = Client()
        # создаём пользователя
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345")
        user = User.objects.get(username="sarah")
        self.client.force_login(user)
        self.group = Group.objects.create(title='leo', slug='leoleo')
        settings.MEDIA_ROOT = tempfile.mkdtemp()

    @override_settings(CACHES=settings.TEST_CACHES)
    def test_image(self):
        """
        1. Проверяет страницу конкретной записи с картинкой: на странице есть тег <img>
        2. Проверяет, что на главной странице, на странице профайла и на странице группы
        пост с картинкой отображается корректно, с тегом <img>
        """
        image = SimpleUploadedFile(name='image.png', content=open('test_media/image.png', 'rb').read(),
                                                content_type='image/jpeg')
        self.client.post("/new/", {"text": "post with image", "group": self.group.pk, 'image': image}, follow=True)

        response = self.client.get('/sarah/')
        self.assertContains(response, '<img')
        response = self.client.get('/group/leoleo/')
        self.assertContains(response, '<img')
        response = self.client.get('/')
        self.assertContains(response, '<img')
        response = self.client.get('/sarah/1/')
        self.assertContains(response, '<img')


    def test_graphic_format(self):
        """
        Проверяет, что срабатывает защита от загрузки файлов не-графических форматов
        """
        with open("test_media/notimage.docx", 'rb') as fp:
            self.client.post("/new/",
                             {"text": "post with image", "group": self.group.pk, 'image': fp},
                             follow=True)
        response = self.client.get('/sarah/')
        self.assertNotContains(response, self.client.post)
        # print(response.content.decode('utf-8'))

    def tearDown(self):
        print("tearDown")


class TestFollow(TestCase):

    def setUp(self):
        self.client = Client()
        # создаём пользователя
        User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345"
        )
        User.objects.create_user(
            username="dara", email="sara.s@skynet.com", password="12345"
        )
        User.objects.create_user(
            username="genry", email="sara.s@skynet.com", password="12345"
        )
        user = User.objects.get(username="dara")
        self.client.force_login(user)
        self.test_post = 'Post from user'

    def test_follow_unfollow(self):
        """
        Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.
        """
        self.client.post("/new/", {"text": self.test_post})
        self.client.logout()

        user = User.objects.get(username="sarah")
        self.client.force_login(user)
        self.client.get("/dara/follow")

        response = self.client.get('/follow/')
        self.assertContains(response, self.test_post)

        self.client.get("/dara/unfollow")
        response = self.client.get('/follow/')
        self.assertNotContains(response, self.test_post)

    def test_feed(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан на него.

        """

        self.client.post("/new/", {"text": self.test_post})
        self.client.logout()

        user = User.objects.get(username="sarah")
        self.client.force_login(user)
        self.client.get("/dara/follow")

        response = self.client.get('/follow/')
        self.assertContains(response, self.test_post)
        self.client.logout()

        user = User.objects.get(username="genry")
        self.client.force_login(user)
        response = self.client.get('/follow/')
        self.assertNotContains(response, self.test_post)

    def tearDown(self):
        print("tearDown")

