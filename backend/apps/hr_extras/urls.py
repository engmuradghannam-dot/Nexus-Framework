from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AppraisalViewSet, EmployeeLoanViewSet, EndOfServiceView,
                    ExpenseClaimViewSet, JobApplicantViewSet, JobOpeningViewSet)

router = DefaultRouter()
router.register(r"expense-claims", ExpenseClaimViewSet, basename="expense-claim")
router.register(r"loans", EmployeeLoanViewSet, basename="employee-loan")
router.register(r"job-openings", JobOpeningViewSet, basename="job-opening")
router.register(r"applicants", JobApplicantViewSet, basename="job-applicant")
router.register(r"appraisals", AppraisalViewSet, basename="appraisal")

urlpatterns = [
    path("end-of-service/", EndOfServiceView.as_view(), name="end-of-service"),
    path("", include(router.urls)),
]
