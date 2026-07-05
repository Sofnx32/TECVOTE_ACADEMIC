from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Vote


class ReceiptVerificationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, receipt_code: str):
        vote = Vote.objects.select_related("election").filter(receipt_code=receipt_code).first()
        if not vote:
            return Response(
                {"valid": False, "message": "Receipt code not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        election = vote.election
        is_published = election.status == "PUBLISHED"

        return Response(
            {
                "valid": True,
                "receipt_code": receipt_code,
                "election_id": election.id,
                "election_title": election.title,
                "election_status": election.status,
                "published": is_published,
                "cast_at": vote.cast_at,
                "payload_hash": vote.payload_hash,  # optional disclosure policy
            },
            status=status.HTTP_200_OK
        )