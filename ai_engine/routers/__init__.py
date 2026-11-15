from . import resume_route, session_route

# Backward-compatible alias for older imports that expect interview_route.router.
interview_route = session_route

__all__ = ["interview_route", "resume_route", "session_route"]
