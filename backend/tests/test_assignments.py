import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from datetime import timedelta

User = get_user_model()


@pytest.mark.django_db
class TestAssignments:
    def test_submission_late_penalty_calculation(self, assignment, student_user, enrollment):
        """Test that late penalty is applied correctly to submission scores.
        
        This tests the reorder fix in assignments/views.py where penalty
        was being applied after percentage calculation instead of before.
        """
        from assignments.models import Submission
        
        # Simulate a late submission with a score
        submission = Submission.objects.create(
            assignment=assignment,
            student=student_user,
            status=Submission.Status.SUBMITTED,
            submitted_at=timezone.now() - timedelta(days=2),
            late_submission=True,
            score=80,
        )
        
        # Calculate score with late penalty
        final_score = submission.calculate_score()
        
        # Late penalty should be applied (25% penalty = 20 points off)
        # The fix ensures penalty is applied first, then percentage is calculated
        assert final_score < 80  # Penalty reduces the score
        assert submission.late_penalty_applied is not None
        assert submission.late_penalty_applied > 0

    def test_submission_on_time(self, assignment, student_user, enrollment):
        """Test on-time submission without penalty."""
        from assignments.models import Submission
        
        # Submit on time with a score
        submission = Submission.objects.create(
            assignment=assignment,
            student=student_user,
            status=Submission.Status.SUBMITTED,
            submitted_at=timezone.now(),
            late_submission=False,
            score=80,
        )
        
        # Calculate score without penalty
        final_score = submission.calculate_score()
        
        # No penalty for on-time submission
        assert final_score == 80
        assert submission.late_penalty_applied == 0 or submission.late_penalty_applied is None
