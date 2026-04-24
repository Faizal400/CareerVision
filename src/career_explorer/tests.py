from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from career_explorer.models import Job
from core_engine.scoring import score_seniority, aggregate
from core_engine.skill_extraction import skill_gap_summary, extract_skills
from core_engine.preprocess import normalise_text


class SeniorityScoreTests(TestCase):
    """CareerFit seniority feature - distance-based scoring."""

    def test_perfect_match_returns_one(self):
        # same level should always be 1.0
        self.assertEqual(score_seniority(1, 1), 1.0)

    def test_max_distance_returns_zero(self):
        # intern vs lead = distance 4 = 0.0
        self.assertEqual(score_seniority(0, 4), 0.0)

    def test_one_level_apart(self):
        # graduate applying for mid = distance 1 = 0.75
        self.assertAlmostEqual(score_seniority(1, 2), 0.75)

    def test_clamps_out_of_range(self):
        # levels outside 0-4 should not crash
        result = score_seniority(-1, 5)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)


class SkillGapSummaryTests(TestCase):
    """Weighted skill gap summary - essential vs optional."""

    def test_all_essential_matched(self):
        U = {"Python", "Django", "Git"}
        T_ess = {"Python", "Django", "Git"}
        T_opt = set()
        result = skill_gap_summary(U, T_ess, T_opt)
        self.assertEqual(result["overlap_score"], 1.0)
        self.assertEqual(result["missing"], [])

    def test_missing_essential_hurts_more_than_optional(self):
        U = set()
        T_ess = {"Python"}   # weight 2
        T_opt = {"Docker"}   # weight 1
        result = skill_gap_summary(U, T_ess, T_opt)
        # overlap should be 0, gap should be 0 (everything missing)
        self.assertEqual(result["overlap_score"], 0.0)
        self.assertIn("Python", result["missing_ess"])
        self.assertIn("Docker", result["missing_opt"])

    def test_no_occupation_degrades_gracefully(self):
        # T_opt=set() should work the same as flat scoring
        U = {"Python"}
        T_ess = {"Python", "Docker"}
        T_opt = set()
        result = skill_gap_summary(U, T_ess, T_opt)
        self.assertIn("Python", result["matched"])
        self.assertIn("Docker", result["missing"])

    def test_empty_T_returns_zero_overlap(self):
        result = skill_gap_summary({"Python"}, set(), set())
        self.assertEqual(result["overlap_score"], 0.0)


class SkillExtractionTests(TestCase):
    """extract_skills - alias layer matching."""

    def test_finds_python_alias(self):
        skills = extract_skills("I write Python code daily")
        self.assertIn("Python", skills)

    def test_empty_text_returns_empty_set(self):
        self.assertEqual(extract_skills(""), set())

    def test_does_not_false_positive_on_partial_word(self):
        # "r" skill should not match inside "career" or "our"
        skills = extract_skills("our career goals are clear")
        self.assertNotIn("R", skills)

    def test_finds_multiple_skills(self):
        skills = extract_skills("Python Django REST API Git Docker")
        self.assertIn("Python", skills)
        self.assertIn("Git", skills)
        self.assertIn("Docker", skills)


class PreprocessTests(TestCase):
    """normalise_text - consistent lowercasing and cleaning."""

    def test_lowercases(self):
        self.assertEqual(normalise_text("Python DJANGO"), "python django")

    def test_empty_string(self):
        self.assertEqual(normalise_text(""), "")


class CareerExplorerViewTests(TestCase):
    """Tool A views - auth and basic flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        Job.objects.create(
            job_id="J001",
            title="Junior Backend Developer",
            description="Python Django REST API Git Docker SQL",
            seniority_level=1,
            role_family="tech_software",
        )

    def test_ingest_requires_login(self):
        response = self.client.get(reverse("career_explorer_ingest"))
        self.assertRedirects(response, "/accounts/login/?next=/career-explorer/")

    def test_ingest_page_loads_when_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("career_explorer_ingest"))
        self.assertEqual(response.status_code, 200)

    def test_results_redirects_without_session_data(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("career_explorer_results"))
        self.assertRedirects(response, reverse("career_explorer_ingest"))