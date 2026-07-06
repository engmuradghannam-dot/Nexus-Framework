import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_leave_decision_email(self, leave_request_id, decision):
    """Notify an employee by email once their leave request is Approved or
    Rejected. Fire-and-forget from the API request (see hr/signals.py) so
    a slow/broken mail server never blocks the HTTP response."""
    from apps.hr.models import LeaveRequest

    try:
        leave = LeaveRequest.objects.select_related('employee').get(pk=leave_request_id)
    except LeaveRequest.DoesNotExist:
        logger.warning('send_leave_decision_email: LeaveRequest %s no longer exists', leave_request_id)
        return

    if not leave.employee.email:
        logger.info('send_leave_decision_email: employee %s has no email on file, skipping', leave.employee_id)
        return

    subject = f"Leave request {decision.lower()}: {leave.start_date} to {leave.end_date}"
    message = (
        f"Hi {leave.employee.first_name},\n\n"
        f"Your {leave.leave_type} leave request ({leave.start_date} to {leave.end_date}, "
        f"{leave.duration_days} day(s)) has been {decision.lower()}.\n\n"
        f"— Nexus HR"
    )
    try:
        send_mail(
            subject, message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nexus.local'),
            [leave.employee.email], fail_silently=False,
        )
    except Exception as exc:
        logger.exception('send_leave_decision_email failed for leave %s', leave_request_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payroll_paid_email(self, payroll_id):
    """Notify an employee once their payroll record is marked Paid."""
    from apps.hr.models import Payroll

    try:
        payroll = Payroll.objects.select_related('employee').get(pk=payroll_id)
    except Payroll.DoesNotExist:
        logger.warning('send_payroll_paid_email: Payroll %s no longer exists', payroll_id)
        return

    if not payroll.employee.email:
        logger.info('send_payroll_paid_email: employee %s has no email on file, skipping', payroll.employee_id)
        return

    subject = f"Payslip processed: {payroll.pay_period_start} to {payroll.pay_period_end}"
    message = (
        f"Hi {payroll.employee.first_name},\n\n"
        f"Your salary for {payroll.pay_period_start} to {payroll.pay_period_end} "
        f"has been processed. Net pay: {payroll.net_salary} {payroll.currency}.\n\n"
        f"— Nexus HR"
    )
    try:
        send_mail(
            subject, message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nexus.local'),
            [payroll.employee.email], fail_silently=False,
        )
    except Exception as exc:
        logger.exception('send_payroll_paid_email failed for payroll %s', payroll_id)
        raise self.retry(exc=exc)
