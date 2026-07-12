from django.conf import settings
from django.db import models


class TwoFactor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="two_factor"
    )
    secret = models.CharField(max_length=64, blank=True)
    enabled = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "two_factor"

    def __str__(self):
        return f"2FA<{self.user}> enabled={self.enabled}"
