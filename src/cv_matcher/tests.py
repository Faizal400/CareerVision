from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from cv_matcher.services.cv_matcher_service import infer_job_level_from_text
from core_engine.market_relevance import _classify_from_text


class CVMatcherAuthTests(TestCase):
    """Tool B views require login."""

    def test_ingest_requires_login(self):
        response = Client().get(reverse("cv_matcher_ingest"))
        self.assertRedirects(response, "/accounts/login/?next=/cv-matcher/")

    def test_results_requires_login(self):
        response = Client().get(reverse("cv_matcher_results"))
        self.assertRedirects(response, "/accounts/login/?next=/cv-matcher/results/")


class SeniorityInferenceTests(TestCase):
    """infer_job_level_from_text — keyword heuristic seniority detection."""

    def test_intern_keywords(self):
        self.assertEqual(infer_job_level_from_text("We are hiring an intern for a placement year"), 0)

    def test_graduate_keywords(self):
        self.assertEqual(infer_job_level_from_text("Graduate Software Engineer role, entry level"), 1)

    def test_senior_keyword(self):
        self.assertEqual(infer_job_level_from_text("Senior Backend Engineer with 5+ years experience"), 3)

    def test_lead_keyword(self):
        self.assertEqual(infer_job_level_from_text("Lead engineer to head up the platform team"), 4)

    def test_defaults_to_mid_when_unclear(self):
        # Generic JD with no seniority keywords should default to 2 (Mid)
        self.assertEqual(infer_job_level_from_text("We are looking for an engineer to join the team"), 2)


class RoleFamilyClassificationTests(TestCase):
    """_classify_from_text — role family keyword classification."""

    def test_tech_software_classification(self):
        result = _classify_from_text("junior backend developer python django rest api")
        self.assertEqual(result, "tech_software")

    def test_tech_data_classification(self):
        result = _classify_from_text("data scientist machine learning analytics")
        self.assertEqual(result, "tech_data")

    def test_tech_infra_classification(self):
        result = _classify_from_text("devops engineer kubernetes terraform cloud")
        self.assertEqual(result, "tech_infrastructure")

    def test_non_tech_classification(self):
        result = _classify_from_text("graduate marketing manager social media campaigns")
        self.assertEqual(result, "non_tech")


class CVMatcherViewTests(TestCase):
    """Tool B view flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_ingest_page_loads(self):
        response = self.client.get(reverse("cv_matcher_ingest"))
        self.assertEqual(response.status_code, 200)

    def test_results_redirects_without_session(self):
        response = self.client.get(reverse("cv_matcher_results"))
        self.assertRedirects(response, reverse("cv_matcher_ingest"))