"""Gateway Service Client - Orchestration Layer.

This module provides the orchestration layer for the gateway service.
It centralizes all microservice client management and high-level orchestration logic.
The gateway should only orchestrate, not handle business logic.
"""
from typing import List, Optional, Dict, Any
from libs.events.schemas import User, Submission, PlagiarismResult, AnalyticsWindow

from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient
from services.plagiarism_service.app.client import PlagiarismServiceClient
from services.analytics_service.app.client import AnalyticsServiceClient
from services.notification_service.app.client import NotificationServiceClient


class ServiceClients:
    """Container for all microservice clients with orchestration methods."""
    
    def __init__(
        self,
        user_url: str,
        submission_url: str,
        plagiarism_url: str,
        analytics_url: str,
        notification_url: str
    ):
        """Initialize all microservice clients."""
        self.user = UserServiceClient(user_url)
        self.submission = SubmissionServiceClient(submission_url)
        self.plagiarism = PlagiarismServiceClient(plagiarism_url)
        self.analytics = AnalyticsServiceClient(analytics_url)
        self.notification = NotificationServiceClient(notification_url)
    
    async def close_all(self):
        """Close all client connections."""
        await self.user.client.close()
        await self.submission.close()
        await self.plagiarism.close()
        await self.analytics.close()
        await self.notification.close()
    
    # User orchestration methods
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Orchestrate user authentication.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # For mock: derive user_id from email pattern
        if "student" in email.lower():
            user_id = "student_001"
        elif "faculty" in email.lower():
            user_id = "faculty_001"
        else:
            user_id = "user_001"
        
        # Fetch user from user service
        user = await self.user.get_user(user_id)
        
        # In a real implementation, would validate password here
        # For now, just return the user if found
        return user
    
    async def get_user_with_fallback(self, user_id: str, role: str = "student") -> User:
        """Get user with fallback to mock user.
        
        Args:
            user_id: User ID
            role: User role for fallback
            
        Returns:
            User object
        """
        user = await self.user.get_user(user_id)
        if not user:
            # Fallback to mock user so dev flow works without Users service data
            user = User(
                id=user_id,
                name=f"Demo {role.capitalize()}",
                email=f"{user_id}@example.com",
                role=role,
            )
        return user
    
    # Student dashboard orchestration
    async def get_student_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Orchestrate data fetching for student dashboard.
        
        Args:
            user_id: Student user ID
            
        Returns:
            Dictionary containing all dashboard data
        """
        # Fetch user data
        user = await self.get_user_with_fallback(user_id, "student")
        
        # Fetch student's submissions
        submissions = await self.submission.list_by_user(user_id)
        
        # Fetch latest analytics
        analytics = await self.analytics.get_latest()
        
        # Fetch user notifications
        notifications = await self.notification.get_user_notifications(user_id)
        
        return {
            "user": user,
            "submissions": submissions,
            "submissions_count": len(submissions),
            "analytics": analytics,
            "notifications": notifications[:5],  # Show 5 most recent
            "has_notifications": len(notifications) > 0
        }
    
    # Faculty dashboard orchestration
    async def get_faculty_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Orchestrate data fetching for faculty dashboard.
        
        Args:
            user_id: Faculty user ID
            
        Returns:
            Dictionary containing all dashboard data
        """
        # Fetch user data
        user = await self.get_user_with_fallback(user_id, "faculty")
        
        # Fetch analytics history
        analytics_history = await self.analytics.get_history()
        
        # Get latest analytics
        latest_analytics = analytics_history[0] if analytics_history else None
        
        # Fetch all users to get recent submissions
        all_users = await self.user.get_all()
        
        # Fetch recent submissions from all students
        recent_submissions = []
        for u in all_users[:10]:  # Limit to prevent too many API calls
            if u.role == "student":
                user_submissions = await self.submission.list_by_user(u.id)
                recent_submissions.extend(user_submissions)
        
        # Sort by upload time and limit
        recent_submissions.sort(key=lambda s: s.uploaded_at, reverse=True)
        recent_submissions = recent_submissions[:10]
        
        # Calculate statistics
        total_submissions = len(recent_submissions)
        flagged_count = 0
        if latest_analytics and latest_analytics.avg_plagiarism > 0.5:
            # Estimate flagged based on analytics
            flagged_count = int(total_submissions * latest_analytics.avg_plagiarism)
        
        return {
            "user": user,
            "analytics_history": analytics_history[:10],  # Last 10 windows
            "latest_analytics": latest_analytics,
            "recent_submissions": recent_submissions,
            "total_submissions": total_submissions,
            "flagged_count": flagged_count,
            "spike_detected": latest_analytics.spike_detected if latest_analytics else False
        }
    
    # Submission orchestration
    async def handle_submission_upload(
        self,
        user_id: str,
        assignment_id: str,
        file_content: bytes,
        filename: str
    ) -> Optional[Submission]:
        """Orchestrate submission upload with plagiarism check.
        
        Args:
            user_id: User ID
            assignment_id: Assignment ID
            file_content: File content bytes
            filename: Original filename
            
        Returns:
            Created submission or None if failed
        """
        # Upload file to submission service
        created_submission = await self.submission.upload_file(
            user_id=user_id,
            assignment_id=assignment_id,
            file_content=file_content,
            filename=filename
        )
        
        if not created_submission:
            return None
        
        # Trigger plagiarism check if text content is available
        if created_submission.text:
            try:
                await self.plagiarism.check(created_submission)
            except Exception:
                # Continue even if plagiarism check fails
                pass
        
        return created_submission
    
    async def get_user_submissions(self, user_id: str) -> List[Submission]:
        """Get all submissions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of submissions
        """
        return await self.submission.list_by_user(user_id)
    
    async def get_submission_by_id(self, submission_id: str) -> Optional[Submission]:
        """Get submission by ID.
        
        Args:
            submission_id: Submission ID
            
        Returns:
            Submission or None if not found
        """
        return await self.submission.get(submission_id)
