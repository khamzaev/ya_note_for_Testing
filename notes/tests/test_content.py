from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from notes.models import Note
from django.conf import settings

User = get_user_model()


class TestHomePage(TestCase):
    HOME_URL = reverse('notes:home')

    def test_home_page(self):
        response = self.client.get(self.HOME_URL)
        # Проверяем, что главная страница загружается с кодом 200
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/home.html')


class TestNotesList(TestCase):
    NOTES_LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')
        for i in range(5):
            Note.objects.create(
                title=f'Заметка {i}',
                text=f'Текст заметки {i}',
                author=cls.user
            )

    def test_notes_list(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.NOTES_LIST_URL)
        self.assertEqual(len(response.context['object_list']), 5)


class TestNoteCreate(TestCase):
    CREATE_NOTE_URL = reverse('notes:add')

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')

    def test_create_note_anonymous_user(self):
        response = self.client.get(self.CREATE_NOTE_URL)
        expected_url = f"{settings.LOGIN_URL}?next={self.CREATE_NOTE_URL}"
        self.assertRedirects(response, expected_url)

    def test_create_note_authenticated_user(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.CREATE_NOTE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/form.html')

    def test_create_note_valid_form(self):
        self.client.login(username='testuser', password='password')
        data = {'title': 'Тестовая заметка', 'text': 'Текст заметки', 'slug': 'test-slug'}
        response = self.client.post(self.CREATE_NOTE_URL, data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.first().title, 'Тестовая заметка')


class TestNoteUpdate(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.note = Note.objects.create(
            title='Тестовая заметка', text='Текст заметки', author=cls.user, slug='test-slug'
        )
        cls.update_url = reverse('notes:edit', args=[cls.note.slug])

    def test_update_note_authenticated_user(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/form.html')

    def test_update_note_anonymous_user(self):
        response = self.client.get(self.update_url)
        self.assertRedirects(response, f'/auth/login/?next={self.update_url}')

    def test_update_note_valid_form(self):
        self.client.login(username='testuser', password='password')
        data = {'title': 'Обновлённая заметка', 'text': 'Обновлённый текст', 'slug': 'updated-slug'}
        response = self.client.post(self.update_url, data)
        self.assertRedirects(response, reverse('notes:success'))
        updated_note = Note.objects.get(id=self.note.id)
        self.assertEqual(updated_note.title, 'Обновлённая заметка')
        self.assertEqual(updated_note.text, 'Обновлённый текст')


class TestNoteDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.note = Note.objects.create(
            title='Заметка для удаления', text='Текст заметки для удаления', author=cls.user, slug='delete-slug'
        )
        cls.delete_url = reverse('notes:delete', args=[cls.note.slug])

    def test_delete_note_authenticated_user(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/delete.html')

    def test_delete_note_anonymous_user(self):
        response = self.client.get(self.delete_url)
        self.assertRedirects(response, f'/auth/login/?next={self.delete_url}')

    def test_delete_note_valid_post(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)


class TestNoteDetail(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.note = Note.objects.create(
            title='Тестовая заметка', text='Текст заметки', author=cls.user, slug='test-slug'
        )
        cls.detail_url = reverse('notes:detail', args=[cls.note.slug])

    def test_note_detail(self):
        self.client.login(username='testuser', password='password')

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notes/detail.html')
        self.assertIn('note', response.context)
        self.assertEqual(response.context['note'], self.note)
