from django.test import TestCase
from django.urls import reverse
from .models import Task

class TaskModelTests(TestCase):
    def test_str(self):
        t = Task.objects.create(title="Hello")
        self.assertEqual(str(t), "Hello")

class TaskViewTests(TestCase):
    def test_list_view(self):
        resp = self.client.get(reverse('tasks:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No tasks yet")
