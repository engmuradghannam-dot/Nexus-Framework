"""HR notification helpers.

Named `tasks.py` to match the serializer call sites, but these run
synchronously — nothing in this project actually starts a Celery worker
(no `celery.py` app, no `@shared_task` anywhere), so a real `.delay()`
call here would just enqueue a message nobody ever consumes. Delivery
itself is best-effort via `apps.notifications.models.deliver`, which never
raises (falls back to a queued NotificationLog row if SMTP isn't
configured), so these are safe to call inline from a serializer.
"""


def send_leave_decision_email(leave_request_id, decision):
    from apps.notifications.models import deliver

    from .models import LeaveRequest

    leave = LeaveRequest.objects.select_related("employee").filter(id=leave_request_id).first()
    if not leave or not leave.employee.email:
        return
    decision_ar = {"Approved": "تمت الموافقة على", "Rejected": "تم رفض"}.get(decision, decision)
    deliver(
        "email",
        leave.employee.email,
        f"{decision_ar} طلب الإجازة",
        f"{decision_ar} طلب إجازتك ({leave.leave_type}) من {leave.start_date} إلى {leave.end_date}.",
    )


def send_payroll_paid_email(payroll_id):
    from apps.notifications.models import deliver

    from .models import Payroll

    payroll = Payroll.objects.select_related("employee").filter(id=payroll_id).first()
    if not payroll or not payroll.employee.email:
        return
    deliver(
        "email",
        payroll.employee.email,
        "تم صرف الراتب",
        f"تم صرف راتبك لفترة {payroll.pay_period_start} إلى {payroll.pay_period_end} "
        f"بصافي {payroll.net_salary} {payroll.currency}.",
    )
