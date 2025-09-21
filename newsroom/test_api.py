from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from newsroom.models import User, Publisher, Article


class APITests(APITestCase):
def setUp(self):


self.reader = User.objects.create_user(
    username='r', password='pass', role=User.Roles.READER)
self.editor = User.objects.create_user(
    username='e', password='pass', role=User.Roles.EDITOR)
self.journalist = User.objects.create_user(
    username='j', password='pass', role=User.Roles.JOURNALIST)
self.publisher = Publisher.objects.create(name='Daily Planet')
self.publisher.editors.add(self.editor)
self.publisher.journalists.add(self.journalist)


def test_journalist_can_create_article(self):


self.client.login(username='j', password='pass')
url = '/api/articles/'
data = {"title": "Hello", "body": "World", "publisher_id": self.publisher.id}
res = self.client.post(url, data, format='json')
self.assertEqual(res.status_code, status.HTTP_201_CREATED)


def test_reader_sees_only_approved_subscriptions(self):

    # Make subscriptions
self.reader.reader_profile = getattr(
    # ensure exists
    self.reader, 'reader_profile', None) or self.reader.readerprofile_set.create()
self.reader.reader_profile.subscribed_publishers.add(self.publisher)


# Create two articles
art1 = Article.objects.create(title='A1', body='B1', publisher=self.publisher,
                              author=self.journalist, status=Article.Status.APPROVED)
art2 = Article.objects.create(title='A2', body='B2', publisher=self.publisher,
                              author=self.journalist, status=Article.Status.DRAFT)


self.client.login(username='r', password='pass')
res = self.client.get('/api/articles/')
self.assertEqual(res.status_code, status.HTTP_200_OK)
ids = {a['id'] for a in res.json()}
self.assertIn(art1.id, ids)
self.assertNotIn(art2.id, ids)


def test_editor_can_approve(self):


art = Article.objects.create(title='P', body='B', publisher=self.publisher,
                             author=self.journalist, status=Article.Status.PENDING)
self.client.login(username='e', password='pass')
res = self.client.post(f'/api/articles/{art.id}/approve/')
self.assertEqual(res.status_code, status.HTTP_200_OK)
art.refresh_from_db()
self.assertEqual(art.status, Article.Status.APPROVED)
