import hashlib
import secrets
from collections import Counter
from apps.security.services import create_audit_log
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.academic.models import VoterRegistry
from apps.elections.models import Election
from apps.security.models import AuditLog
from apps.ballots.models import BallotOption
from .models import VotingSession, Vote, VoteSelection


def _generate_receipt_code() -> str:
    return secrets.token_hex(16)


def _hash_payload(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@transaction.atomic
def cast_vote(*, user, election_id: int, selections: list[int], ip_address=None, user_agent=None):
    election = Election.objects.select_for_update().filter(id=election_id).first()
    if not election:
        raise ValidationError("Election not found.")

    now = timezone.now()
    if election.status != "OPEN":
        raise ValidationError("Election is not open.")
    if not (election.start_at <= now <= election.end_at):
        raise ValidationError("Election is outside allowed voting time window.")

    eligible = VoterRegistry.objects.filter(
        user=user,
        period=election.period,
        is_eligible=True,
    ).exists()
    if not eligible:
        raise ValidationError("User is not eligible to vote in this election period.")

    if Vote.objects.filter(election=election, voter=user).exists():
        raise ValidationError("User has already voted in this election.")

    rules = getattr(election, "rules", None)

    # Load selected options and validate ownership by election
    selected_options = list(
        BallotOption.objects.select_related("ballot_position__ballot__election")
        .filter(id__in=selections)
    )
    if len(selected_options) != len(selections):
        raise ValidationError("One or more selected options do not exist.")

    # Must belong to active ballot of the same election
    for option in selected_options:
        ballot = option.ballot_position.ballot
        if ballot.election_id != election.id:
            raise ValidationError("Selected option does not belong to this election.")
        if not ballot.is_active:
            raise ValidationError("Selected option belongs to an inactive ballot.")

    # No duplicate option ids in request
    if len(set(selections)) != len(selections):
        raise ValidationError("Duplicate options are not allowed.")

    # Per-position constraints
    position_ids = [opt.ballot_position.position_id for opt in selected_options]
    counts = Counter(position_ids)
    if any(c > 1 for c in counts.values()):
        raise ValidationError("Only one option per position is allowed.")

    # Election rule constraints
    if rules:
        blank_count = sum(1 for opt in selected_options if opt.option_type == "BLANK")
        null_count = sum(1 for opt in selected_options if opt.option_type == "NULL")

        if not rules.allow_blank_vote and blank_count > 0:
            raise ValidationError("Blank vote is not allowed in this election.")
        if not rules.allow_null_vote and null_count > 0:
            raise ValidationError("Null vote is not allowed in this election.")

        if rules.max_positions_per_ballot and len(selected_options) > rules.max_positions_per_ballot:
            raise ValidationError("Selected options exceed maximum allowed positions.")

    session = VotingSession.objects.create(
        election=election,
        voter=user,
        ip_address=ip_address,
        user_agent=user_agent,
        is_successful=False,
    )

    payload_raw = f"user={user.id};election={election.id};selections={selections};ts={now.isoformat()}"
    encrypted_payload = payload_raw  # TODO: replace with real encryption
    payload_hash = _hash_payload(payload_raw)

    vote = Vote.objects.create(
        election=election,
        voter=user,
        session=session,
        receipt_code=_generate_receipt_code(),
        encrypted_payload=encrypted_payload,
        payload_hash=payload_hash,
    )

    VoteSelection.objects.bulk_create(
        [VoteSelection(vote=vote, ballot_option_id=option.id) for option in selected_options]
    )

    session.completed_at = timezone.now()
    session.is_successful = True
    session.save(update_fields=["completed_at", "is_successful"])

    AuditLog.objects.create(
        actor=user,
        election=election,
        action="PUBLISH_RESULT",
        ip_address=ip_address,
        metadata={
            "vote_id": str(vote.id),
            "receipt_code": vote.receipt_code,
            "selection_count": len(selected_options),
            "user_agent": user_agent or "",
        },
    )

    return vote

