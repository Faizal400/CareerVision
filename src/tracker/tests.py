from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tracker.models import SkillPlan, TrackedSkill


class TrackerAuthTests(TestCase):
    """Tracker views require login."""

    def test_dashboard_requires_login(self):
        response = Client().get(reverse("tracker_dashboard"))
        self.assertRedirects(response, "/accounts/login/?next=/tracker/dashboard/")

    def test_plan_detail_requires_login(self):
        response = Client().get(reverse("tracker_plan_detail", args=[1]))
        self.assertRedirects(response, "/accounts/login/?next=/tracker/plan/1/")


class TrackerDataIsolationTests(TestCase):
    """Users can only see and edit their own plans."""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.plan = SkillPlan.objects.create(
            user=self.user1,
            plan_name="User1 Plan",
            source=0,
        )

    def test_user2_cannot_access_user1_plan(self):
        self.client.login(username="user2", password="pass123")
        response = self.client.get(reverse("tracker_plan_detail", args=[self.plan.id]))
        # Should return 404 not a 200
        self.assertEqual(response.status_code, 404)

    def test_user1_can_access_own_plan(self):
        self.client.login(username="user1", password="pass123")
        response = self.client.get(reverse("tracker_plan_detail", args=[self.plan.id]))
        self.assertEqual(response.status_code, 200)


class TrackerCRUDTests(TestCase):
    """Saving skills and updating status."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_save_skills_creates_plan_and_skills(self):
        response = self.client.post(reverse("save_tskill_toplan"), {
            "plan_name": "My Test Plan",
            "source": 0,
            "skills": ["Python", "Docker"],
        })
        self.assertRedirects(response, reverse("tracker_dashboard"))
        plan = SkillPlan.objects.get(plan_name="My Test Plan", user=self.user)
        self.assertEqual(TrackedSkill.objects.filter(plan=plan).count(), 2)

    def test_save_skills_without_name_redirects(self):
        # empty plan_name should redirect rather than crash
        response = self.client.post(reverse("save_tskill_toplan"), {
            "plan_name": "",
            "source": 0,
            "skills": ["Python"],
        })
        self.assertEqual(response.status_code, 302)

    def test_update_skill_status(self):
        plan = SkillPlan.objects.create(user=self.user, plan_name="Test", source=0)
        skill = TrackedSkill.objects.create(
            plan=plan,
            skill_name="Python",
            skill_prog_status=0,
            skill_next_action="Build something with Python",
        )
        response = self.client.post(
            reverse("tracker_update_skill_status", args=[skill.id]),
            {"skill_prog_status": 2},
        )
        skill.refresh_from_db()
        self.assertEqual(skill.skill_prog_status, 2)
        self.assertRedirects(response, reverse("tracker_plan_detail", args=[plan.id]))

    def test_dashboard_only_shows_own_plans(self):
        other_user = User.objects.create_user(username="other", password="pass")
        SkillPlan.objects.create(user=other_user, plan_name="Other Plan", source=0)
        SkillPlan.objects.create(user=self.user, plan_name="My Plan", source=0)

        response = self.client.get(reverse("tracker_dashboard"))
        plans = response.context["plans"]
        self.assertEqual(plans.count(), 1)
        self.assertEqual(plans.first().plan_name, "My Plan")