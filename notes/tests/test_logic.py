from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from pytils.translit import slugify
from notes.models import Note
from notes.forms import WARNING

User = get_user_model()

class TestNoteCreation(TestCase):
    ADD_NOTE_URL = reverse('notes:add')

    def setUp(self):
        """Настройка данных для тестов"""
        self.form_data = {'title': 'Form title',
                          'text': 'Form text',
                          'slug': 'form-slug'}

        self.user = User.objects.create(username='Test User')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_user_can_create_note(self):
        response = self.auth_client.post(self.ADD_NOTE_URL, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        new_note = Note.objects.filter(slug=self.form_data['slug']).first()
        self.assertIsNotNone(new_note)
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.user)

    def test_not_auth_user_cant_create_note(self):
        response = self.client.post(self.ADD_NOTE_URL, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.ADD_NOTE_URL}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_slug_unique(self):
        # Создание первой заметки с тем же slug
        self.auth_client.post(self.ADD_NOTE_URL, data=self.form_data)
        response = self.auth_client.post(self.ADD_NOTE_URL, data=self.form_data)
        form = response.context['form']
        warning = self.form_data['slug'] + WARNING
        self.assertIn(warning, form.errors['slug'])

    def test_fill_slug(self):
        del self.form_data['slug']
        response = self.auth_client.post(self.ADD_NOTE_URL, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))

        # Проверка, что заметка создана с автогенерированным slug
        expected_slug = slugify(self.form_data['title'])
        new_note = Note.objects.filter(slug=expected_slug).first()
        self.assertIsNotNone(new_note)
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    NOTE_TITLE = 'title'
    NEW_NOTE_TITLE = 'new note title'
    NOTE_TEXT = 'note text'
    NEW_NOTE_TEXT = 'new note text'

    def setUp(self):
        """Настройка данных для тестов редактирования и удаления заметки"""
        self.author = User.objects.create(username='Test')
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader = User.objects.create(username='Simple')
        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

        self.note = Note.objects.create(
            title=self.NOTE_TITLE,
            text=self.NOTE_TEXT,
            slug='noteslug',
            author=self.author,
        )
        self.edit_note_url = reverse('notes:edit', args=[self.note.slug])
        self.delete_note_url = reverse('notes:delete', args=[self.note.slug])
        self.form_data = {'title': self.NEW_NOTE_TITLE, 'text': self.NEW_NOTE_TEXT}

    def test_author_can_edit_note(self):
        # Автор может отредактировать заметку
        self.author_client.post(self.edit_note_url, self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_other_user_cant_edit_note(self):
        # Другой пользователь не может редактировать заметку
        response = self.reader_client.post(self.edit_note_url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # Убедимся, что заметка не изменилась
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)

    def test_author_can_delete_note(self):
        # Автор может удалить заметку
        response = self.author_client.post(self.delete_note_url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        # Другой пользователь не может удалить заметку
        response = self.reader_client.post(self.delete_note_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
