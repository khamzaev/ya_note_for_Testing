# notes/tests/test_routes.py
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя, который будет владельцем заметки.
        cls.author = User.objects.create_user(username='author', password='password')
        cls.reader = User.objects.create_user(username='reader', password='password')

        # Создаём заметку, которая будет использована в тестах.
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст тестовой заметки',
            author=cls.author
        )

    def test_pages_availability(self):
        # Проверка доступности основных страниц.
        urls = (
            ('notes:home', None),
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:list', None),
            ('notes:success', None),
        )

        for name, args in urls:
            with self.subTest(name=name):
                self.client.force_login(self.author)
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        # Проверяем, что анонимный пользователь перенаправляется на страницу входа при попытке редактирования или удаления.
        login_url = reverse('users:login')

        # Список страниц для тестирования редиректа.
        for name in ('notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_availability_for_author(self):
        # Проверка доступности страниц для пользователя, создавшего заметку.
        self.client.force_login(self.author)

        # Проверяем доступность страниц редактирования и удаления.
        for name in ('notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_reader(self):
        # Проверка, что пользователь, не являющийся автором, не может редактировать или удалять заметки.
        self.client.force_login(self.reader)

        # Проверяем, что эти страницы возвращают ошибку 404.
        for name in ('notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
