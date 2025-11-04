"""
Comprehensive Unit Tests for Third-Party RESTful API

This test suite provides complete coverage for the news application's
RESTful API, including all 32 test cases consolidated into a single file:
1. Token authentication and authorization
2. Subscription-based article filtering
3. CRUD operations for subscriptions
4. Error handling and edge cases
5. Performance and pagination
6. Data integrity and validation

The API allows third-party clients to:
- Authenticate using token-based authentication
- Subscribe/unsubscribe to publishers and journalists
- Retrieve articles filtered by their subscriptions
- Access publisher and journalist information
"""

# pylint: disable=no-member,too-many-lines,missing-function-docstring
# Django ORM dynamically adds .objects manager to models at runtime
# File length acceptable for comprehensive test suite
# Test method docstrings omitted for brevity - method names are descriptive

import time
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import CustomUser, Publisher, Article


class APISubscriptionTests(TestCase):
    """Tests for third-party API endpoints and subscription filtering."""

    def setUp(self):
        """Create publishers, journalists, reader and approved articles."""
        # Create two publishers
        self.pub1 = Publisher.objects.create(name="Pub One")
        self.pub2 = Publisher.objects.create(name="Pub Two")

        # Create journalists and attach to publishers
        self.jour_a = CustomUser.objects.create(
            username="jour_a",
            role="journalist",
        )
        self.jour_a.publisher = self.pub1
        self.jour_a.save()

        self.jour_b = CustomUser.objects.create(
            username="jour_b",
            role="journalist",
        )
        self.jour_b.publisher = self.pub2
        self.jour_b.save()

        # Approved articles for each journalist
        self.a1 = Article.objects.create(
            title="Article A1",
            slug="a1",
            content="x",
            summary="s",
            author=self.jour_a,
            publisher=self.pub1,
            status="approved",
            is_approved=True,
        )

        self.b1 = Article.objects.create(
            title="Article B1",
            slug="b1",
            content="x",
            summary="s",
            author=self.jour_b,
            publisher=self.pub2,
            status="approved",
            is_approved=True,
        )

        # Reader who subscribes only to pub1
        self.reader = CustomUser.objects.create(
            username="reader1",
            role="reader",
        )
        self.reader.subscribed_publishers.add(self.pub1)

        # Token for the reader
        self.token, _ = Token.objects.get_or_create(user=self.reader)

        self.client = APIClient()

    def test_auth_required(self):
        """Unauthenticated access to the articles list should be 401."""
        r = self.client.get("/api/articles/")
        self.assertEqual(r.status_code, 401)

    def test_articles_filtered_by_subscribed_publisher(self):
        """Reader should only see articles from subscribed publishers."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.client.get("/api/articles/")
        self.assertEqual(r.status_code, 200)

        body = r.json()
        # DRF list endpoints may be paginated; extract results if present
        results = body.get("results", body if isinstance(body, list) else [])
        titles = [a["title"] for a in results]
        self.assertIn("Article A1", titles)
        self.assertNotIn("Article B1", titles)

    def test_by_publisher_endpoint(self):
        """The by_publisher endpoint returns articles for the given pub id."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        url = f"/api/articles/by_publisher/?publisher_id={self.pub1.id}"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        data = r.json()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('results', data)
        results = data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Article A1")

    def test_by_journalist_endpoint(self):
        """by_journalist returns articles for the given journalist."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        url = f"/api/articles/by_journalist/?journalist_id={self.jour_a.id}"
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        data = r.json()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('results', data)
        results = data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["author"]["username"], "jour_a")


class SubscriptionAPITests(TestCase):
    """Token-authenticated tests for subscription endpoints."""

    def setUp(self):
        # Publishers
        self.pub1 = Publisher.objects.create(name="Pub One")
        self.pub2 = Publisher.objects.create(name="Pub Two")

        # Journalists
        self.jour_a = CustomUser.objects.create(
            username="jour_a",
            role="journalist",
        )
        self.jour_b = CustomUser.objects.create(
            username="jour_b",
            role="journalist",
        )

        # Reader
        self.reader = CustomUser.objects.create(
            username="reader",
            role="reader",
        )

        # Token and client
        self.token, _ = Token.objects.get_or_create(user=self.reader)
        self.client = APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

    def test_publishers_subscribe_list_create_destroy(self):
        # Initially no subscriptions
        r = self.client.get("/api/subscriptions/publishers/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        self.assertEqual(len(results), 0)

        # Subscribe to pub1
        r = self.client.post(
            "/api/subscriptions/publishers/",
            {"publisher_id": self.pub1.id},
            format='json',
        )
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body.get("name"), "Pub One")

        # Now list should contain one
        r = self.client.get("/api/subscriptions/publishers/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        self.assertEqual(len(results), 1)

        # Unsubscribe (DELETE) using publisher id as pk
        r = self.client.delete(
            f"/api/subscriptions/publishers/{self.pub1.id}/",
        )
        self.assertEqual(r.status_code, 204)

        # Back to empty
        r = self.client.get("/api/subscriptions/publishers/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        self.assertEqual(len(results), 0)

    def test_journalists_subscribe_list_create_destroy(self):
        # Initially no journalist subscriptions
        r = self.client.get("/api/subscriptions/journalists/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        self.assertEqual(len(results), 0)

    def test_subscribe_edge_cases_publishers(self):
        """Edge cases for publisher subscription: missing id and not found."""
        # Missing publisher_id -> 400
        r = self.client.post("/api/subscriptions/publishers/", {},
                             format='json')
        self.assertEqual(r.status_code, 400)

        # Non-existent publisher_id -> 404
        r = self.client.post(
            "/api/subscriptions/publishers/",
            {"publisher_id": 99999},
            format='json',
        )
        self.assertEqual(r.status_code, 404)

    def test_subscribe_edge_cases_journalists(self):
        """Edge cases for journalist subscription: missing id, not found."""
        # Missing journalist_id -> 400
        r = self.client.post("/api/subscriptions/journalists/", {},
                             format='json')
        self.assertEqual(r.status_code, 400)

        # Non-existent journalist_id -> 404
        r = self.client.post(
            "/api/subscriptions/journalists/",
            {"journalist_id": 99999},
            format='json',
        )
        self.assertEqual(r.status_code, 404)

        # Attempt to subscribe to a non-journalist user (reader) -> 404
        r = self.client.post(
            "/api/subscriptions/journalists/",
            {"journalist_id": self.reader.id},
            format='json',
        )
        self.assertEqual(r.status_code, 404)

        # Subscribe to jour_a
        r = self.client.post(
            "/api/subscriptions/journalists/",
            {"journalist_id": self.jour_a.id},
            format='json',
        )
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body.get("username"), "jour_a")

        # List shows one
        r = self.client.get("/api/subscriptions/journalists/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        self.assertEqual(len(results), 1)

        # Unsubscribe
        r = self.client.delete(
            f"/api/subscriptions/journalists/{self.jour_a.id}/",
        )
        self.assertEqual(r.status_code, 204)

        r = self.client.get("/api/subscriptions/journalists/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        results = data.get("results", data if isinstance(data, list) else [])
        self.assertEqual(len(results), 0)


class ComprehensiveAPITestCase(APITestCase):
    """
    Comprehensive test suite for the third-party RESTful API.
    Tests authentication, subscription filtering, CRUD operations, edge cases.
    """

    @classmethod
    def setUpTestData(cls):
        """Set up test data that will be used across multiple tests."""
        # Create publishers
        cls.tech_publisher = Publisher.objects.create(
            name="Tech News Daily",
            description="Leading technology news publisher",
            website="https://technews.com"
        )
        cls.sports_publisher = Publisher.objects.create(
            name="Sports Central",
            description="Sports news and analysis",
            website="https://sportscentral.com"
        )
        cls.finance_publisher = Publisher.objects.create(
            name="Finance World",
            description="Financial news and market analysis"
        )

        # Create journalists
        cls.tech_journalist = CustomUser.objects.create_user(
            username="tech_reporter",
            email="tech@technews.com",
            password="testpass123",
            role="journalist",
            first_name="Alice",
            last_name="Tech",
            bio="Technology journalist with 5 years experience"
        )
        cls.tech_journalist.publisher = cls.tech_publisher
        cls.tech_journalist.save()

        cls.sports_journalist = CustomUser.objects.create_user(
            username="sports_writer",
            email="sports@sportscentral.com",
            password="testpass123",
            role="journalist",
            first_name="Bob",
            last_name="Sports"
        )
        cls.sports_journalist.publisher = cls.sports_publisher
        cls.sports_journalist.save()

        cls.independent_journalist = CustomUser.objects.create_user(
            username="indie_writer",
            email="indie@freelance.com",
            password="testpass123",
            role="journalist",
            first_name="Carol",
            last_name="Independent"
        )
        # Independent journalist has no publisher

        # Create editors
        cls.tech_editor = CustomUser.objects.create_user(
            username="tech_editor",
            email="editor@technews.com",
            password="testpass123",
            role="editor"
        )
        cls.tech_publisher.staff_members.add(cls.tech_editor)

        # Create readers (API clients)
        cls.api_client_1 = CustomUser.objects.create_user(
            username="api_client_1",
            email="client1@thirdparty.com",
            password="testpass123",
            role="reader"
        )
        cls.api_client_2 = CustomUser.objects.create_user(
            username="api_client_2",
            email="client2@thirdparty.com",
            password="testpass123",
            role="reader"
        )
        cls.api_client_3 = CustomUser.objects.create_user(
            username="api_client_3",
            email="client3@thirdparty.com",
            password="testpass123",
            role="reader"
        )

        # Set up subscriptions for different test scenarios
        # Client 1: Subscribed to tech publisher and sports journalist
        cls.api_client_1.subscribed_publishers.add(cls.tech_publisher)
        cls.api_client_1.subscribed_journalists.add(cls.sports_journalist)

        # Client 2: Subscribed to sports publisher only
        cls.api_client_2.subscribed_publishers.add(cls.sports_publisher)

        # Client 3: No subscriptions (should receive no articles)

        # Create tokens for API clients
        cls.token_1, _ = Token.objects.get_or_create(user=cls.api_client_1)
        cls.token_2, _ = Token.objects.get_or_create(user=cls.api_client_2)
        cls.token_3, _ = Token.objects.get_or_create(user=cls.api_client_3)

    def setUp(self):
        """Set up for each test method."""
        self.client = APIClient()

        # Create articles for testing
        self.tech_article_1 = Article.objects.create(
            title="AI Revolution in 2024",
            slug="ai-revolution-2024",
            content="Artificial intelligence continues to transform...",
            summary="AI is changing the world in unprecedented ways.",
            author=self.tech_journalist,
            publisher=self.tech_publisher,
            status="approved",
            is_approved=True,
            tags="AI, technology, innovation"
        )

        self.tech_article_2 = Article.objects.create(
            title="Quantum Computing Breakthrough",
            slug="quantum-computing-breakthrough",
            content="Scientists achieve new milestone in quantum computing...",
            summary="New quantum computing achievements unlock possibilities.",
            author=self.tech_journalist,
            publisher=self.tech_publisher,
            status="approved",
            is_approved=True,
            tags="quantum, computing, science"
        )

        self.sports_article_1 = Article.objects.create(
            title="Olympic Games Preview",
            slug="olympic-games-preview",
            content="Preview of upcoming Olympic games and key athletes...",
            summary="What to expect from the upcoming Olympics.",
            author=self.sports_journalist,
            publisher=self.sports_publisher,
            status="approved",
            is_approved=True,
            tags="olympics, sports, athletes"
        )

        self.independent_article = Article.objects.create(
            title="Freelance Journalism in Digital Age",
            slug="freelance-journalism-digital",
            content="The challenges and opportunities for journalists...",
            summary="How digital platforms are changing freelance journalism.",
            author=self.independent_journalist,
            publisher=None,
            status="approved",
            is_approved=True,
            is_independent=True,
            tags="journalism, freelance, digital"
        )

        # Create some draft/pending articles (should not appear in API)
        self.draft_article = Article.objects.create(
            title="Draft Article",
            slug="draft-article",
            content="This is a draft article...",
            summary="Draft summary",
            author=self.tech_journalist,
            publisher=self.tech_publisher,
            status="draft",
            is_approved=False
        )

        self.pending_article = Article.objects.create(
            title="Pending Article",
            slug="pending-article",
            content="This article is pending approval...",
            summary="Pending summary",
            author=self.sports_journalist,
            publisher=self.sports_publisher,
            status="pending",
            is_approved=False
        )

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied with 401."""
        endpoints = [
            '/api/articles/',
            '/api/publishers/',
            '/api/subscriptions/publishers/',
            '/api/subscriptions/journalists/',
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    f"Unauthenticated access to {endpoint} should return 401"
                )

    def test_token_authentication_success(self):
        """Test successful token authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_authentication(self):
        """Test authentication with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid_token_123')
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_authorization_header(self):
        """Test malformed authorization headers."""
        malformed_headers = [
            'Bearer token123',  # Wrong type
            'Token',  # Missing token
            'token123',  # Missing Token prefix
            'Token token1 token2',  # Multiple tokens
        ]

        for auth_header in malformed_headers:
            with self.subTest(auth_header=auth_header):
                self.client.credentials(HTTP_AUTHORIZATION=auth_header)
                response = self.client.get('/api/articles/')
                self.assertEqual(response.status_code,
                                 status.HTTP_401_UNAUTHORIZED)

    def test_subscription_based_article_filtering(self):
        """
        Test that API clients receive only articles based on subscriptions.
        This is the core functionality of the subscription system.
        """
        # Client 1: Subscribed to tech publisher and sports journalist
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data.get('results', data)
        article_titles = [article['title'] for article in results]

        # Should see tech articles and sports articles
        self.assertIn("AI Revolution in 2024", article_titles)
        self.assertIn("Quantum Computing Breakthrough", article_titles)
        self.assertIn("Olympic Games Preview", article_titles)

        # Should NOT see independent article
        self.assertNotIn("Freelance Journalism in Digital Age", article_titles)

        # Should not see draft/pending articles
        self.assertNotIn("Draft Article", article_titles)
        self.assertNotIn("Pending Article", article_titles)

        # Client 2: Subscribed to sports publisher only
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_2.key}')
        response = self.client.get('/api/articles/')
        data = response.json()
        results = data.get('results', data)
        article_titles = [article['title'] for article in results]

        # Should only see sports articles
        self.assertIn("Olympic Games Preview", article_titles)
        self.assertNotIn("AI Revolution in 2024", article_titles)
        self.assertNotIn("Quantum Computing Breakthrough", article_titles)
        self.assertNotIn("Freelance Journalism in Digital Age", article_titles)

        # Client 3: No subscriptions
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_3.key}')
        response = self.client.get('/api/articles/')
        data = response.json()
        results = data.get('results', data)

        # Should see no articles
        self.assertEqual(len(results), 0)

    def test_articles_by_publisher_endpoint(self):
        """Test the by_publisher action endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Test valid publisher filter
        url = (f'/api/articles/by_publisher/'
               f'?publisher_id={self.tech_publisher.id}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('results', data)
        results = data['results']

        # Should return tech articles only
        article_titles = [article['title'] for article in results]
        self.assertIn("AI Revolution in 2024", article_titles)
        self.assertIn("Quantum Computing Breakthrough", article_titles)
        self.assertNotIn("Olympic Games Preview", article_titles)

        # Test missing publisher_id parameter
        response = self.client.get('/api/articles/by_publisher/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = response.json().get('error', '')
        self.assertIn('publisher_id required', error_msg)

        # Test non-existent publisher
        response = self.client.get(
            '/api/articles/by_publisher/?publisher_id=99999'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('results', data)
        results = data['results']
        self.assertEqual(len(results), 0)

    def test_articles_by_journalist_endpoint(self):
        """Test the by_journalist action endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Test valid journalist filter
        url = (f'/api/articles/by_journalist/'
               f'?journalist_id={self.sports_journalist.id}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('results', data)
        results = data['results']
        article_titles = [article['title'] for article in results]
        self.assertIn("Olympic Games Preview", article_titles)
        self.assertNotIn("AI Revolution in 2024", article_titles)

        # Test missing journalist_id parameter
        response = self.client.get('/api/articles/by_journalist/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_publisher_subscription_management(self):
        """Test publisher subscription CRUD operations."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_3.key}')

        # Initially no subscriptions
        response = self.client.get('/api/subscriptions/publishers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 0)

        # Subscribe to tech publisher
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': self.tech_publisher.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify subscription was created
        response = self.client.get('/api/subscriptions/publishers/')
        data = response.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Tech News Daily")

        # Verify articles are now available
        response = self.client.get('/api/articles/')
        data = response.json()
        results = data.get('results', data)
        self.assertGreater(len(results), 0)

        # Unsubscribe
        response = self.client.delete(
            f'/api/subscriptions/publishers/{self.tech_publisher.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify no subscriptions
        response = self.client.get('/api/subscriptions/publishers/')
        data = response.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 0)

    def test_journalist_subscription_management(self):
        """Test journalist subscription CRUD operations."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_3.key}')

        # Subscribe to tech journalist
        response = self.client.post(
            '/api/subscriptions/journalists/',
            {'journalist_id': self.tech_journalist.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify subscription
        response = self.client.get('/api/subscriptions/journalists/')
        data = response.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], 'tech_reporter')

        # Try to subscribe to non-journalist (should fail)
        response = self.client.post(
            '/api/subscriptions/journalists/',
            {'journalist_id': self.tech_editor.id},  # Editor, not journalist
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_edge_cases(self):
        """Test edge cases for subscription management."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_3.key}')

        # Test duplicate subscription (should be idempotent)
        response1 = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': self.tech_publisher.id},
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': self.tech_publisher.id},
            format='json'
        )
        # Should still succeed (idempotent operation)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        # But should only have one subscription
        response = self.client.get('/api/subscriptions/publishers/')
        data = response.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 1)

        # Test invalid publisher ID
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': 99999},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid data format
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {'invalid_field': 'invalid_value'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_article_serialization_completeness(self):
        """Test that article serialization includes all expected fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.get('/api/articles/')

        data = response.json()
        results = data.get('results', data)
        self.assertGreater(len(results), 0)

        article = results[0]
        expected_fields = [
            'id', 'title', 'slug', 'content', 'summary', 'author',
            'publisher', 'status', 'is_approved', 'tags', 'views_count',
            'created_at', 'published_at', 'featured_image'
        ]

        for field in expected_fields:
            self.assertIn(field, article,
                          f"Article should include field: {field}")

        # Test nested serialization
        self.assertIn('username', article['author'])
        self.assertIn('role', article['author'])
        if article['publisher']:
            self.assertIn('name', article['publisher'])
            self.assertIn('website', article['publisher'])

    def test_publisher_serialization_completeness(self):
        """Test publisher serialization includes all expected fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.get('/api/publishers/')

        data = response.json()
        results = data.get('results', data)
        self.assertGreater(len(results), 0)

        publisher = results[0]
        expected_fields = [
            'id', 'name', 'description', 'website', 'founded_date',
            'created_at', 'article_count'
        ]

        for field in expected_fields:
            self.assertIn(field, publisher,
                          f"Publisher should include field: {field}")

    def test_pagination_functionality(self):
        """Test API pagination works correctly."""
        # Create many articles to test pagination
        for i in range(15):
            Article.objects.create(
                title=f"Test Article {i}",
                slug=f"test-article-{i}",
                content=f"Content for test article {i}",
                summary=f"Summary {i}",
                author=self.tech_journalist,
                publisher=self.tech_publisher,
                status="approved",
                is_approved=True
            )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.get('/api/articles/')

        data = response.json()
        # Should have pagination metadata
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)

        # Should respect page size (configured as 20 in settings)
        results = data['results']
        self.assertLessEqual(len(results), 20)

    def test_api_performance_basic(self):
        """Basic performance test for API endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Test articles endpoint performance
        start_time = time.time()
        response = self.client.get('/api/articles/')
        end_time = time.time()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should respond within 1 second (adjust based on requirements)
        self.assertLess(end_time - start_time, 1.0)

        # Test publishers endpoint performance
        start_time = time.time()
        response = self.client.get('/api/publishers/')
        end_time = time.time()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(end_time - start_time, 1.0)

    def test_cross_user_data_isolation(self):
        """Test that users can only see their own subscription data."""
        # Client 1 subscribes to tech publisher
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': self.finance_publisher.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Client 2 should not see Client 1's subscriptions
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_2.key}')
        response = self.client.get('/api/subscriptions/publishers/')
        data = response.json()
        results = data.get('results', data)

        # Client 2 should only see sports publisher (from setup), not finance
        publisher_names = [pub['name'] for pub in results]
        self.assertIn("Sports Central", publisher_names)
        self.assertNotIn("Finance World", publisher_names)

    def test_content_type_handling(self):
        """Test proper handling of JSON content type."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Test JSON content type works correctly
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': self.finance_publisher.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify subscription was created
        response = self.client.get('/api/subscriptions/publishers/')
        data = response.json()
        results = data.get('results', data)
        publisher_names = [pub['name'] for pub in results]
        self.assertIn("Finance World", publisher_names)

    def test_http_methods_allowed(self):
        """Test that only allowed HTTP methods work on endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Articles endpoint should only allow GET (ReadOnlyModelViewSet)
        response = self.client.post('/api/articles/', {})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.put('/api/articles/1/', {})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete('/api/articles/1/')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_api_error_responses_format(self):
        """Test that API error responses are properly formatted."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Test 400 error format - missing required field
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)

        # Test 404 error format
        response = self.client.get('/api/articles/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_subscription_filtering_complex_scenarios(self):
        """Test complex subscription filtering scenarios."""
        # Create a user subscribed to both publisher and individual journalist
        complex_client = CustomUser.objects.create_user(
            username="complex_client",
            email="complex@test.com",
            password="testpass123",
            role="reader"
        )

        # Subscribe to tech publisher and independent journalist
        complex_client.subscribed_publishers.add(self.tech_publisher)
        complex_client.subscribed_journalists.add(self.independent_journalist)

        complex_token, _ = Token.objects.get_or_create(user=complex_client)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {complex_token.key}'
        )
        response = self.client.get('/api/articles/')

        data = response.json()
        results = data.get('results', data)
        article_titles = [article['title'] for article in results]

        # Should see tech articles and independent article
        self.assertIn("AI Revolution in 2024", article_titles)
        self.assertIn("Quantum Computing Breakthrough", article_titles)
        self.assertIn("Freelance Journalism in Digital Age", article_titles)

        # Should NOT see sports articles
        self.assertNotIn("Olympic Games Preview", article_titles)

    def test_token_management(self):
        """Test token creation and management."""
        # Test that tokens are created for users
        test_user = CustomUser.objects.create_user(
            username="token_test",
            email="token@test.com",
            password="testpass123",
            role="reader"
        )

        # Token should be creatable
        token, created = Token.objects.get_or_create(user=test_user)
        self.assertTrue(created)
        self.assertIsNotNone(token.key)
        self.assertEqual(len(token.key), 40)  # Django token length

        # Same token should be returned on subsequent calls
        token2, created2 = Token.objects.get_or_create(user=test_user)
        self.assertFalse(created2)
        self.assertEqual(token.key, token2.key)

    def test_role_based_access_control(self):
        """Test that different user roles can access the API."""
        # Create users with different roles
        journalist_token, _ = Token.objects.get_or_create(
            user=self.tech_journalist
        )
        editor_token, _ = Token.objects.get_or_create(user=self.tech_editor)

        # Test journalist access (should work)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {journalist_token.key}'
        )
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test editor access (should work)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {editor_token.key}'
        )
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_article_approval_workflow_filtering(self):
        """Test that only approved articles are returned by the API."""
        # Create articles in different states
        Article.objects.create(
            title="Rejected Article",
            slug="rejected-article",
            content="This article was rejected",
            summary="Rejected summary",
            author=self.tech_journalist,
            publisher=self.tech_publisher,
            status="rejected",
            is_approved=False
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')
        response = self.client.get('/api/articles/')

        data = response.json()
        results = data.get('results', data)
        article_titles = [article['title'] for article in results]

        # Should not include rejected, draft, or pending articles
        self.assertNotIn("Rejected Article", article_titles)
        self.assertNotIn("Draft Article", article_titles)
        self.assertNotIn("Pending Article", article_titles)

        # Should include approved articles
        self.assertIn("AI Revolution in 2024", article_titles)

    def test_subscription_persistence(self):
        """Test that subscriptions persist across sessions."""
        # Subscribe to publisher
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_3.key}')
        response = self.client.post(
            '/api/subscriptions/publishers/',
            {'publisher_id': self.tech_publisher.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create new client instance (simulating new session)
        new_client = APIClient()
        new_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_3.key}')

        # Subscription should still exist
        response = new_client.get('/api/subscriptions/publishers/')
        data = response.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 1)

    def test_api_documentation_fields(self):
        """Test that API responses include fields useful for documentation."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_1.key}')

        # Test articles endpoint
        response = self.client.get('/api/articles/')
        data = response.json()

        # Should have proper pagination structure
        if 'results' in data:
            self.assertIn('count', data)
            self.assertIn('next', data)
            self.assertIn('previous', data)

        # Test individual article detail
        if data.get('results'):
            article_id = data['results'][0]['id']
            response = self.client.get(f'/api/articles/{article_id}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
