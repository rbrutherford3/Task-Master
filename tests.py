import datetime
from django.test import TestCase
from django.urls import reverse
from .models import Task

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
