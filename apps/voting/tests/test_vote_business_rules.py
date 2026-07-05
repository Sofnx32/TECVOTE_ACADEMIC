from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from apps.academic.models import AcademicPeriod, Faculty, Program,VoterRegistry
from apps.elections.models import Election, Position, ElectionRule, CandidateList
from apps.ballots.models import Ballot, BallotPosition, BallotOption
from apps.voting.models import Vote, VotingSession

User = get_user_model()


class VoteBusinessRulesTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email="admin@x.com", username="adminx", institutional_id="A-99", password="Pass1234!", role="ADMIN"
        )
        self.student = User.objects.create_user(
            email="student@x.com", username="studentx", institutional_id="S-99", password="Pass1234!", role="STUDENT"
        )
        self.other_student = User.objects.create_user(
            email="student2@x.com", username="student2x", institutional_id="S-100", password="Pass1234!", role="STUDENT"
        )

        self.period = AcademicPeriod.objects.create(
            name="2026-II",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_active=True,
        )
        self.faculty = Faculty.objects.create(name="Engineering2", code="ENG2")
        self.program = Program.objects.create(faculty=self.faculty, name="Systems2", code="SYS2")

        self.election = Election.objects.create(
            title="Business Rules Election",
            description="desc",
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
            label="List A",
        )

        VoterRegistry.objects.create(
            user=self.student, program=self.program, period=self.period, semester=5, is_eligible=True
        )
        VoterRegistry.objects.create(
            user=self.other_student, program=self.program, period=self.period, semester=5, is_eligible=False
        )

    def test_ineligible_student_cannot_vote(self):
        self.client.force_authenticate(self.other_student)
        payload = {"election_id": str(self.election.id), "selections": [{"ballot_option_id": str(self.opt.id)}]}
        r = self.client.post("/api/v1/votes/cast/", payload, format="json")
        self.assertIn(r.status_code, [400, 403])

    def test_double_vote_blocked(self):
        session = VotingSession.objects.create(
            election=self.election,
            voter=self.student,
            is_successful=True,
        )

        Vote.objects.create(
            election=self.election,
            voter=self.student,
            session=session,  # <- obligatorio
            receipt_code="alreadyvoted001",
            encrypted_payload="payload",
            payload_hash="hash",
        )

        self.client.force_authenticate(self.student)
        payload = {
            "election_id": str(self.election.id),
            "selections": [{"ballot_option_id": str(self.opt.id)}],
        }
        r = self.client.post("/api/v1/votes/cast/", payload, format="json")
        self.assertIn(r.status_code, [400, 409])

    def test_vote_not_allowed_when_election_not_open(self):
        self.election.status = "CERTIFIED"
        self.election.save(update_fields=["status"])
        self.client.force_authenticate(self.student)
        payload = {"election_id": str(self.election.id), "selections": [{"ballot_option_id": str(self.opt.id)}]}
        r = self.client.post("/api/v1/votes/cast/", payload, format="json")
        self.assertIn(r.status_code, [400, 403])

    def test_vote_requires_valid_option(self):
        self.client.force_authenticate(self.student)
        payload = {"election_id": str(self.election.id), "selections": [{"ballot_option_id": "00000000-0000-0000-0000-000000000000"}]}
        r = self.client.post("/api/v1/votes/cast/", payload, format="json")
        self.assertIn(r.status_code, [400, 404])