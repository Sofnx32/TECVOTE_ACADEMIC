from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academic.models import AcademicPeriod, Faculty, Program, VoterRegistry
from apps.elections.models import Election, Position, ElectionRule, CandidateList
from apps.ballots.models import Ballot, BallotPosition, BallotOption
from apps.voting.models import VotingSession, Vote, VoteSelection
from apps.results.models import ElectionResult, Tally

User = get_user_model()


class ElectionLifecycleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            institutional_id="A-1",
            password="Pass1234!",
            role="ADMIN",
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            username="student",
            institutional_id="S-1",
            password="Pass1234!",
            role="STUDENT",
        )

        self.period = AcademicPeriod.objects.create(
            name="2026-I",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_active=True,
        )
        self.faculty = Faculty.objects.create(name="Engineering", code="ENG")
        self.program = Program.objects.create(faculty=self.faculty, name="Systems", code="SYS")

        self.election = Election.objects.create(
            title="Student Council Election",
            description="Academic election",
            election_type="FACULTY",
            period=self.period,
            faculty=self.faculty,
            start_at=timezone.now() - timezone.timedelta(hours=1),
            end_at=timezone.now() + timezone.timedelta(hours=1),
            status="OPEN",
            created_by=self.admin,
        )

        ElectionRule.objects.create(
            election=self.election,
            allow_blank_vote=True,
            allow_null_vote=True,
            max_positions_per_ballot=3,
            requires_2fa=False,
        )

        self.position = Position.objects.create(election=self.election, name="President", seats=1)
        self.list_a = CandidateList.objects.create(election=self.election, name="List A")
        self.ballot = Ballot.objects.create(election=self.election, version=1, is_active=True)
        self.bp = BallotPosition.objects.create(ballot=self.ballot, position=self.position, order=1)
        self.opt = BallotOption.objects.create(
            ballot_position=self.bp,
            option_type="CANDIDATE_LIST",
            candidate_list=self.list_a,
            label="List A - President"
        )

        VoterRegistry.objects.create(
            user=self.student,
            program=self.program,
            period=self.period,
            semester=5,
            is_eligible=True,
        )

        session = VotingSession.objects.create(election=self.election, voter=self.student, is_successful=True)
        vote = Vote.objects.create(
            election=self.election,
            voter=self.student,
            session=session,
            receipt_code="abc123xyz789",
            encrypted_payload="payload",
            payload_hash="hash",
        )
        VoteSelection.objects.create(vote=vote, ballot_option=self.opt)

    def test_results_hidden_before_published(self):
        self.client.force_authenticate(user=self.student)
        r1 = self.client.get("/api/v1/election-results/")
        r2 = self.client.get("/api/v1/tallies/")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(len(r1.json()), 0)
        self.assertEqual(len(r2.json()), 0)

    def test_lifecycle_close_certify_publish(self):
        self.client.force_authenticate(user=self.admin)

        close_resp = self.client.post("/api/v1/election-lifecycle/close/", {"election_id": self.election.id}, format="json")
        self.assertEqual(close_resp.status_code, 200)

        cert_resp = self.client.post("/api/v1/election-lifecycle/certify/", {"election_id": self.election.id}, format="json")
        self.assertEqual(cert_resp.status_code, 200)

        pub_resp = self.client.post("/api/v1/election-lifecycle/publish/", {"election_id": self.election.id}, format="json")
        self.assertEqual(pub_resp.status_code, 200)

        self.election.refresh_from_db()
        self.assertEqual(self.election.status, "PUBLISHED")

        result = ElectionResult.objects.get(election=self.election)
        self.assertIsNotNone(result.published_at)
        self.assertTrue(bool(result.report_pdf))

        self.assertTrue(Tally.objects.filter(election=self.election).exists())

    def test_results_visible_after_published(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post("/api/v1/election-lifecycle/close/", {"election_id": self.election.id}, format="json")
        self.client.post("/api/v1/election-lifecycle/certify/", {"election_id": self.election.id}, format="json")
        self.client.post("/api/v1/election-lifecycle/publish/", {"election_id": self.election.id}, format="json")

        self.client.force_authenticate(user=self.student)
        r1 = self.client.get("/api/v1/election-results/")
        r2 = self.client.get("/api/v1/tallies/")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(len(r1.json()), 1)
        self.assertGreaterEqual(len(r2.json()), 1)