from http import HTTPStatus

from django.test import TestCase, Client


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_page_not_found_uses_correct_template(self):
        """Ошибка 404 возвращает кастомный шаблон core/404.html."""
        response = self.client.get('/nonexists-page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
