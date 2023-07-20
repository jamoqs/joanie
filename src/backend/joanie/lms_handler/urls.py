"""
API routes exposed by our LMS handler app.
"""
from django.urls import re_path

from rest_framework import routers

from .api import course_runs_sync, complementary_configurations

ROUTER = routers.SimpleRouter()

urlpatterns = ROUTER.urls + [
    re_path("course-runs-sync/?$", course_runs_sync, name="course-runs-sync"),
    re_path("complementary-configurations/", complementary_configurations, name="complementary-configurations"),
]
