from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from apps.security.services import create_audit_log
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework.exceptions import ValidationError
import hashlib
from apps.academic.models import VoterRegistry
from apps.elections.models import Election
from apps.security.models import AuditLog
from apps.voting.models import VoteSelection
from apps.ballots.models import BallotOption
from .models import Tally, ElectionResult
from apps.security.crypto_utils import sign_payload

def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _build_pdf_report(*, election: Election, result: ElectionResult) -> bytes:
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Official Election Report")
    y -= 30

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Election: {election.title}")
    y -= 20
    p.drawString(50, y, f"Status: {election.status}")
    y -= 20
    p.drawString(50, y, f"Certified at: {result.certified_at}")
    y -= 20
    p.drawString(50, y, f"Published at: {result.published_at}")
    y -= 30

    p.drawString(50, y, f"Total voters: {result.total_voters}")
    y -= 20
    p.drawString(50, y, f"Total votes cast: {result.total_votes_cast}")
    y -= 20
    p.drawString(50, y, f"Turnout %: {result.turnout_percentage}")
    y -= 20
    p.drawString(50, y, f"Blank votes: {result.blank_votes}")
    y -= 20
    p.drawString(50, y, f"Null votes: {result.null_votes}")
    y -= 30

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Tallies by Option")
    y -= 20
    p.setFont("Helvetica", 10)

    tallies = (
        Tally.objects.select_related("position", "option")
        .filter(election=election)
        .order_by("position__name", "-votes_count")
    )
    for t in tallies:
        line = f"{t.position.name} | {t.option.label} ({t.option.option_type}) -> {t.votes_count}"
        p.drawString(50, y, line[:110])
        y -= 15
        if y < 60:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


@transaction.atomic
def close_election(*, election: Election, actor, ip_address=None):
    if election.status != "OPEN":
        raise ValidationError("Election must be OPEN to close it.")

    election.status = "CLOSED"
    election.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=actor,
        election=election,
        action="PUBLISH_RESULT",
        ip_address=ip_address,
        metadata={"message": "Election closed successfully."},
    )


@transaction.atomic
def certify_election_results(*, election: Election, actor, ip_address=None):
    if election.status not in {"CLOSED", "CERTIFIED", "PUBLISHED"}:
        raise ValidationError("Election must be CLOSED before certification.")

    Tally.objects.filter(election=election).delete()

    grouped = (
        VoteSelection.objects
        .filter(vote__election=election)
        .values("ballot_option")
        .annotate(votes_count=Count("id"))
    )

    option_map = {
        opt.id: opt
        for opt in BallotOption.objects.select_related("ballot_position__position").filter(
            ballot_position__ballot__election=election
        )
    }

    blank_votes = 0
    null_votes = 0
    total_votes_cast = 0
    tallies_to_create = []

    for row in grouped:
        option_id = row["ballot_option"]
        count = row["votes_count"]
        total_votes_cast += count

        option = option_map.get(option_id)
        if not option:
            continue

        if option.option_type == "BLANK":
            blank_votes += count
        elif option.option_type == "NULL":
            null_votes += count

        tallies_to_create.append(
            Tally(
                election=election,
                position=option.ballot_position.position,
                option=option,
                votes_count=count,
            )
        )

    Tally.objects.bulk_create(tallies_to_create)

    total_voters = VoterRegistry.objects.filter(
        period=election.period,
        is_eligible=True
    ).count()

    turnout_percentage = Decimal("0.00")
    if total_voters > 0:
        turnout_percentage = (Decimal(total_votes_cast) / Decimal(total_voters)) * Decimal("100")

    result, _ = ElectionResult.objects.update_or_create(
        election=election,
        defaults={
            "total_voters": total_voters,
            "total_votes_cast": total_votes_cast,
            "turnout_percentage": turnout_percentage.quantize(Decimal("0.01")),
            "blank_votes": blank_votes,
            "null_votes": null_votes,
            "certified_at": timezone.now(),
        },
    )

    election.status = "CERTIFIED"
    election.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=actor,
        election=election,
        action="CERTIFY_RESULT",
        ip_address=ip_address,
        metadata={
            "total_voters": total_voters,
            "total_votes_cast": total_votes_cast,
            "turnout_percentage": str(result.turnout_percentage),
            "blank_votes": blank_votes,
            "null_votes": null_votes,
        },
    )

    return result


@transaction.atomic
def publish_election_results(*, election, actor, ip_address=None):
    if election.status not in {"CERTIFIED", "PUBLISHED"}:
        raise ValidationError("Election must be CERTIFIED before publishing.")

    result = ElectionResult.objects.filter(election=election).first()
    if not result:
        raise ValidationError("Election result not found. Certify results first.")

    # 1) timestamp
    result.published_at = timezone.now()

    # 2) generate PDF
    pdf_bytes = _build_pdf_report(election=election, result=result)
    filename = f"election_{election.id}_report.pdf"
    result.report_pdf.save(filename, ContentFile(pdf_bytes), save=False)

    # 3) hash + signature
    pdf_hash = _hash_bytes(pdf_bytes)
    acta_signature = sign_payload(pdf_hash)

    # 4) save integrity fields
    result.report_hash = pdf_hash
    result.report_signature = acta_signature

    # 5) save all together
    result.save(update_fields=["published_at", "report_pdf", "report_hash", "report_signature"])

    # 6) election status
    election.status = "PUBLISHED"
    election.save(update_fields=["status"])

    # 7) audit log
    create_audit_log(
        actor=actor,
        election=election,
        action="PUBLISH_RESULT",
        ip_address=ip_address,
        metadata={
            "report_pdf": result.report_pdf.name,
            "report_hash": result.report_hash,
            "signature_present": bool(result.report_signature),
        },
    )

    return result