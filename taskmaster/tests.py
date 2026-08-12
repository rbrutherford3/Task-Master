import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import signing
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import LoginLockout, Task
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


class FaviconAssetsTest(TestCase):

    def test_page_includes_favicon_links(self):
        response = self.client.get(reverse('taskmaster:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/static/favicon/favicon.ico')
        self.assertContains(response, '/static/favicon/site.webmanifest')


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
            username='old@example.com',
            email='old@example.com',
            password='test-password-123'
        )
        self.client.force_login(self.user)

    @patch('taskmaster.views.send_settings_confirmation_email')
    def test_email_change_updates_user_identity_and_task_owner_on_confirmation(self, mock_send_settings_confirmation_email):
        task = Task.objects.create(
            user='old@example.com',
            short_desc='Task linked to email identity',
            importance=1,
            urgency=1,
            completed=False,
        )

        request_response = self.client.post(
            reverse('taskmaster:settings'),
            {
                'action': 'email',
                'email': 'new@example.com',
            }
        )
        self.assertEqual(request_response.status_code, 302)
        self.assertEqual(mock_send_settings_confirmation_email.call_count, 1)

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
        task.refresh_from_db()
        self.assertEqual(self.user.username, 'new@example.com')
        self.assertEqual(self.user.email, 'new@example.com')
        self.assertEqual(task.user, 'new@example.com')

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
    @patch('taskmaster.views.send_existing_account_notice_email')
    def test_email_change_duplicate_sends_notice_email_and_generic_message(self, mock_send_notice_email, mock_send_settings_confirmation_email):
        User.objects.create_user(
            username='taken@example.com',
            email='taken@example.com',
            password='test-password-123',
        )

        response = self.client.post(
            reverse('taskmaster:settings'),
            {
                'action': 'email',
                'email': 'taken@example.com',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please go to your email inbox and click on the received activation link to confirm and complete the registration. Note: Check your spam folder.')
        mock_send_settings_confirmation_email.assert_not_called()
        mock_send_notice_email.assert_called_once()

    @patch('taskmaster.views.send_settings_confirmation_email')
    def test_account_delete_happens_only_after_confirmation(self, mock_send_settings_confirmation_email):
        Task.objects.create(
            user='old@example.com',
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
        self.assertEqual(Task.objects.filter(user='old@example.com').count(), 1)

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
        self.assertEqual(Task.objects.filter(user='old@example.com').count(), 0)


class RegistrationFlowTest(TestCase):

    @patch('taskmaster.views.verify_recaptcha')
    def test_register_step_one_accepts_existing_email(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(username='taken@example.com', email='taken@example.com', password='x-12345-Abc')

        response = self.client.post(
            reverse('taskmaster:register'),
            {
                'email': 'taken@example.com',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('taskmaster:register_password'))

    @patch('taskmaster.views.verify_recaptcha')
    def test_register_step_one_accepts_new_email(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        response = self.client.post(
            reverse('taskmaster:register'),
            {
                'email': 'new@example.com',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('taskmaster:register_password'))

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

        created_user = User.objects.get(email='new@example.com')
        self.assertEqual(created_user.username, 'new@example.com')
        self.assertEqual(created_user.email, 'new@example.com')
        self.assertFalse(created_user.is_active)
        self.assertEqual(mock_activate_email.call_count, 1)

    @patch('taskmaster.views.send_existing_account_notice_email')
    @patch('taskmaster.views.verify_recaptcha')
    def test_register_two_step_notifies_existing_email_without_creating_user(self, mock_verify_recaptcha, mock_send_notice_email):
        mock_verify_recaptcha.return_value = {'success': True}
        existing_user = User.objects.create_user(
            username='taken@example.com',
            email='taken@example.com',
            password='x-12345-Abc',
        )

        session = self.client.session
        session['register_identity'] = {'email': existing_user.email}
        session.save()

        response = self.client.post(
            reverse('taskmaster:register_password'),
            {
                'password1': 'StrongPassword123!',
                'password2': 'StrongPassword123!',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('taskmaster:index'))
        self.assertEqual(User.objects.filter(email='taken@example.com').count(), 1)
        mock_send_notice_email.assert_called_once()


class LoginFlowTest(TestCase):

    def test_login_get_hides_resend_prompt_without_current_attempt(self):
        session = self.client.session
        session['login_pending_activation_uid'] = 999
        session.save()

        response = self.client.get(reverse('taskmaster:login'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Would you like to be resent the confirmation email?')

    @patch('taskmaster.views.verify_recaptcha')
    def test_inactive_user_login_returns_generic_error(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(
            username='pending@example.com',
            email='pending@example.com',
            password='StrongPassword123!',
            is_active=False,
        )

        response = self.client.post(
            reverse('taskmaster:login'),
            {
                'username': 'pending@example.com',
                'password': 'StrongPassword123!',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')
        self.assertNotContains(response, 'Would you like to be resent the confirmation email?')

    @patch('taskmaster.views.verify_recaptcha')
    def test_invalid_login_increments_failed_attempts(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='StrongPassword123!',
            is_active=True,
        )

        response = self.client.post(
            reverse('taskmaster:login'),
            {
                'username': 'user@example.com',
                'password': 'wrong-password',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')
        state = LoginLockout.objects.get(email='user@example.com')
        self.assertEqual(state.failed_attempts, 1)
        self.assertIsNone(state.lockout_until)

    @patch('taskmaster.views.verify_recaptcha')
    def test_fifth_invalid_login_sets_fifteen_minute_lockout(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(
            username='lockme@example.com',
            email='lockme@example.com',
            password='StrongPassword123!',
            is_active=True,
        )

        for _ in range(5):
            response = self.client.post(
                reverse('taskmaster:login'),
                {
                    'username': 'lockme@example.com',
                    'password': 'wrong-password',
                    'g-recaptcha-response': 'token',
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')
        state = LoginLockout.objects.get(email='lockme@example.com')
        self.assertEqual(state.failed_attempts, 5)
        self.assertIsNotNone(state.lockout_until)
        self.assertGreater(state.lockout_until, timezone.now())
        self.assertLessEqual(state.lockout_until, timezone.now() + datetime.timedelta(minutes=15, seconds=5))

    @patch('taskmaster.views.verify_recaptcha')
    def test_locked_out_user_is_rejected_with_generic_error(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        User.objects.create_user(
            username='locked@example.com',
            email='locked@example.com',
            password='StrongPassword123!',
            is_active=True,
        )
        LoginLockout.objects.create(
            email='locked@example.com',
            failed_attempts=5,
            lockout_until=timezone.now() + datetime.timedelta(minutes=15),
        )

        response = self.client.post(
            reverse('taskmaster:login'),
            {
                'username': 'locked@example.com',
                'password': 'StrongPassword123!',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password.')

    @patch('taskmaster.views.verify_recaptcha')
    def test_successful_login_clears_lockout_state(self, mock_verify_recaptcha):
        mock_verify_recaptcha.return_value = {'success': True}
        user = User.objects.create_user(
            username='clear@example.com',
            email='clear@example.com',
            password='StrongPassword123!',
            is_active=True,
        )
        LoginLockout.objects.create(
            email='clear@example.com',
            failed_attempts=4,
            lockout_until=timezone.now() - datetime.timedelta(minutes=1),
        )

        response = self.client.post(
            reverse('taskmaster:login'),
            {
                'username': 'clear@example.com',
                'password': 'StrongPassword123!',
                'g-recaptcha-response': 'token',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('taskmaster:index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        state = LoginLockout.objects.get(email='clear@example.com')
        self.assertEqual(state.failed_attempts, 0)
        self.assertIsNone(state.lockout_until)


class PasswordResetFlowTest(TestCase):

    @patch('taskmaster.views.send_password_reset_email')
    def test_password_reset_request_clears_lockout_state(self, mock_send_password_reset_email):
        mock_send_password_reset_email.return_value = None
        User.objects.create_user(
            username='recover@example.com',
            email='recover@example.com',
            password='StrongPassword123!',
            is_active=True,
        )
        LoginLockout.objects.create(
            email='recover@example.com',
            failed_attempts=5,
            lockout_until=timezone.now() + datetime.timedelta(minutes=15),
        )

        response = self.client.post(
            reverse('taskmaster:password_reset'),
            {
                'email': 'recover@example.com',
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('taskmaster:index'))
        state = LoginLockout.objects.get(email='recover@example.com')
        self.assertEqual(state.failed_attempts, 0)
        self.assertIsNone(state.lockout_until)
