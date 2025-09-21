"""
Tests for the Task app.

This module includes unit tests for the Task model and view logic.
"""

from django.test import TestCase
from django.urls import reverse
from .models import Task


class TaskModelTests(TestCase):
    """
    Tests for the :class:`~tasks.models.Task` model.
    """

    def test_str(self):
        """
        Verify that ``str(Task)`` returns the task title.

        Creates a task with the title "Hello" and checks that its string
        representation matches the title.
        """
        t = Task.objects.create(title="Hello")
        self.assertEqual(str(t), "Hello")


class TaskViewTests(TestCase):
    """
    Tests for the Task views.
    """

    def test_list_view(self):
        """
        Verify that the task list view renders correctly when no tasks exist.

        - GET ``tasks:list``.
        - Expect HTTP 200 OK.
        - Expect the response to contain "No tasks yet".
        """
        resp = self.client.get(reverse("tasks:list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No tasks yet")
