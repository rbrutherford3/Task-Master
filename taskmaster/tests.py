import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import signing
from django.test import TestCase
from django.urls import reverse

from .models import Task
from .views import SETTINGS_CONFIRM_SALT

# Assumes that today is not at the very beginning or end of the year
class DateFormatTest(TestCase):

    def test_one_year_ago(self):
        test_date = datetime.date.today() - datetime.timedelta(days=365)
        task = Task(due_date=test_date)
        self.assertEqual(test_date.strftime('%x'), task.formatted_due_date)

    def test_two_weeks_ago(self):
        test_date = datetime.date.today() - datetime.timedelta(days=14)
        task = Task(due_date=test_date)
        self.assertEqual(test_date.strftime('%b %-d'), task.formatted_due_date)

    def test_one_week_ago(self):
        test_date = datetime.date.today() - datetime.timedelta(days=7)
        task = Task(due_date=test_date)
        self.assertEqual(test_date.strftime('%b %-d'), task.formatted_due_date)

    def test_two_days_ago(self):
        test_date = datetime.date.today() - datetime.timedelta(days=2)
        task = Task(due_date=test_date)
        self.assertEqual(test_date.strftime('%b %-d'), task.formatted_due_date)

    def test_yesterday(self):
        test_date = datetime.date.today() - datetime.timedelta(days=1)
        task = Task(due_date=test_date)
        self.assertEqual('Yesterday', task.formatted_due_date)

    def test_today(self):
        test_date = datetime.date.today()
        task = Task(due_date=test_date)
        self.assertEqual('Today', task.formatted_due_date)

    def test_six_days_out(self):
        test_date = datetime.date.today() + datetime.timedelta(days=6)
        task = Task(due_date=test_date)
        self.assertEqual(test_date.strftime('%a'), task.formatted_due_date)

    def test_one_week_out(self):
        test_date = datetime.date.today() + datetime.timedelta(days=7)
        task = Task(due_date = test_date)
        self.assertEqual(test_date.strftime('%b %-d'), task.formatted_due_date)

    def test_two_weeks_out(self):
        test_date = datetime.date.today() + datetime.timedelta(days=14)
        task = Task(due_date = test_date)
        self.assertEqual(test_date.strftime('%b %-d'), task.formatted_due_date)

    def test_one_year_out(self):
        test_date = datetime.date.today() + datetime.timedelta(days=365)
        task = Task(due_date = test_date)
        self.assertEqual(test_date.strftime('%x'), task.formatted_due_date)


class TaskDetailTest(TestCase):

    def test_task_detail_exists(self):
        task = Task()
        task.save()
        url = reverse('taskmaster:form', args=(task.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_task_detail_not_exists(self):
        task = Task()
        task.save()
        url = reverse('taskmaster:form', args=(task.id,))
        task.delete()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TaskToggleTest(TestCase):

    def test_task_toggle(self):
        task = Task()
        task.save()
        inverted = not task.completed
        url = reverse('taskmaster:toggle', args=(task.id,))
        self.client.get(url)
        task.refresh_from_db()
        self.assertEqual(task.completed, inverted)


class SettingsFlowTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='oldname',
            email='old@example.com',
            password='test-password-123'
        )
        self.client.force_login(self.user)

    def test_username_change_updates_task_user_field(self):
        task = Task.objects.create(
            user='oldname',
            short_desc='Task linked to username',
            importance=1,
            urgency=1,
            completed=False,
        )

        response = self.client.post(
            reverse('taskmaster:settings'),
            {
                'action': 'username',
                'username': 'newname',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(self.user.username, 'newname')
        self.assertEqual(task.user, 'newname')

    @patch('taskmaster.views.send_settings_confirmation_email')
    def test_email_change_is_not_applied_until_confirmation(self, mock_send_settings_confirmation_email):
        response = self.client.post(
            reverse('taskmaster:settings'),
            {
                'action': 'email',
                'email': 'new@example.com',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_send_settings_confirmation_email.call_count, 1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'old@example.com')

        signed_payload = signing.dumps(
            {
                'action': 'email_change',
                'uid': self.user.pk,
                'new_email': 'new@example.com',
            },
            salt=SETTINGS_CONFIRM_SALT,
        )

        confirm_response = self.client.get(
            reverse('taskmaster:settings_confirm', args=(signed_payload,))
        )
        self.assertEqual(confirm_response.status_code, 302)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')

    @patch('taskmaster.views.send_settings_confirmation_email')
    def test_account_delete_happens_only_after_confirmation(self, mock_send_settings_confirmation_email):
        Task.objects.create(
            user='oldname',
            short_desc='Task to be deleted with account',
            importance=1,
            urgency=1,
            completed=False,
        )

        response = self.client.post(
            reverse('taskmaster:settings'),
            {
                'action': 'delete',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_send_settings_confirmation_email.call_count, 1)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(Task.objects.filter(user='oldname').count(), 1)

        signed_payload = signing.dumps(
            {
                'action': 'delete_account',
                'uid': self.user.pk,
            },
            salt=SETTINGS_CONFIRM_SALT,
        )

        confirm_response = self.client.get(
            reverse('taskmaster:settings_confirm', args=(signed_payload,))
        )
        self.assertEqual(confirm_response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(Task.objects.filter(user='oldname').count(), 0)


class RegistrationFlowTest(TestCase):

    @patch('taskmaster.views.verify_recaptcha')
    def test_register_step_one_username_error_has_priority(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(username='takenuser', email='first@example.com', password='x-12345-Abc')
        User.objects.create_user(username='differentuser', email='taken@example.com', password='x-12345-Abc')

        response = self.client.post(
            reverse('taskmaster:register'),
            {
                'username': 'takenuser',
                'email': 'taken@example.com',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That username is already taken.')
        self.assertNotContains(response, 'That email address is already in use.')

    @patch('taskmaster.views.verify_recaptcha')
    def test_register_step_one_email_taken_message(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(username='anotheruser', email='taken@example.com', password='x-12345-Abc')

        response = self.client.post(
            reverse('taskmaster:register'),
            {
                'username': 'newuser',
                'email': 'taken@example.com',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'That email address is already in use.')

    def test_register_step_two_requires_step_one_first(self):
        response = self.client.get(reverse('taskmaster:register_password'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('taskmaster:register'))

    @patch('taskmaster.views.activateEmail')
    @patch('taskmaster.views.verify_recaptcha')
    def test_register_two_step_creates_inactive_user(self, mock_verify_recaptcha, mock_activate_email):
        mock_verify_recaptcha.return_value = {'success': True}

        step_one = self.client.post(
            reverse('taskmaster:register'),
            {
                'username': 'newuser',
                'email': 'new@example.com',
                'g-recaptcha-response': 'token',
            }
        )
        self.assertEqual(step_one.status_code, 302)
        self.assertEqual(step_one.url, reverse('taskmaster:register_password'))

        step_two = self.client.post(
            reverse('taskmaster:register_password'),
            {
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            }
        )
        self.assertEqual(step_two.status_code, 302)
        self.assertEqual(step_two.url, reverse('taskmaster:index'))

        created_user = User.objects.get(username='newuser')
        self.assertEqual(created_user.email, 'new@example.com')
        self.assertFalse(created_user.is_active)
        self.assertEqual(mock_activate_email.call_count, 1)
