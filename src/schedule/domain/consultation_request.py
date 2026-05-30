"""Schedule domain entity: ConsultationRequest."""

from datetime import datetime, timezone
from typing import Literal


ConsultationRequestStatus = Literal[
    "pending",       # submitted by student, awaiting coordinator action
    "negotiating",   # coordinator launched negotiation session
    "confirmed",     # appointment scheduled
    "cancelled",     # cancelled at any stage
]


class ConsultationRequest:
    """A student's request for a consultation.

    Written in free text. The AI recommender (stub) populates
    ``recommended_curator_ids`` with ordered curator suggestions.
    """

    def __init__(
        self,
        request_id: str,
        student_name: str,
        request_text: str,
    ) -> None:
        student_name = student_name.strip()
        if not student_name:
            raise ValueError("Student name cannot be empty")

        request_text = request_text.strip()
        if not request_text:
            raise ValueError("Request text cannot be empty")

        self.request_id = request_id
        self.student_name = student_name
        self.request_text = request_text
        self.status: ConsultationRequestStatus = "pending"
        self.recommended_curator_ids: list[str] = []
        self.created_at: datetime = datetime.now(timezone.utc)

    def set_recommendations(self, curator_ids: list[str]) -> None:
        """Set AI-recommended curator IDs (ordered by relevance)."""
        if not curator_ids:
            raise ValueError("Recommendations list cannot be empty")
        self.recommended_curator_ids = list(curator_ids)

    def start_negotiation(self) -> None:
        """Coordinator launches a negotiation session."""
        if self.status != "pending":
            raise ValueError(
                f"Cannot start negotiation from status '{self.status}'"
            )
        if not self.recommended_curator_ids:
            raise ValueError(
                "Cannot start negotiation without recommended curators"
            )
        self.status = "negotiating"

    def confirm(self) -> None:
        """Mark request as confirmed after appointment is assigned."""
        if self.status != "negotiating":
            raise ValueError(
                f"Cannot confirm from status '{self.status}'"
            )
        self.status = "confirmed"

    def cancel(self) -> None:
        """Cancel the request from any non-terminal status."""
        if self.status in ("confirmed", "cancelled"):
            raise ValueError(
                f"Cannot cancel a request with status '{self.status}'"
            )
        self.status = "cancelled"

    def reopen_negotiation(self) -> None:
        """Re-open negotiation after a curator declines (was confirmed)."""
        if self.status != "confirmed":
            raise ValueError(
                f"Cannot reopen negotiation from status '{self.status}'"
            )
        self.status = "negotiating"
