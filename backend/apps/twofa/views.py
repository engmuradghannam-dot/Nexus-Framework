from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from . import totp
from .models import TwoFactor


class TwoFactorViewSet(ViewSet):
    """TOTP two-factor: setup -> verify -> (enabled). Disable to turn off."""

    def _tf(self, request):
        tf, _ = TwoFactor.objects.get_or_create(user=request.user)
        return tf

    @action(detail=False, methods=["get"])
    def status(self, request):
        tf = self._tf(request)
        return Response({"enabled": tf.enabled})

    @action(detail=False, methods=["post"])
    def setup(self, request):
        tf = self._tf(request)
        if not tf.secret or not tf.enabled:
            tf.secret = totp.random_base32()
            tf.enabled = False
            tf.save()
        uri = totp.provisioning_uri(tf.secret, request.user.email or str(request.user))
        return Response({"secret": tf.secret, "otpauth_uri": uri})

    @action(detail=False, methods=["post"])
    def verify(self, request):
        tf = self._tf(request)
        code = request.data.get("code", "")
        if not tf.secret:
            return Response({"success": False, "message": "ابدأ الإعداد أولاً"}, status=400)
        if totp.verify(tf.secret, code):
            tf.enabled = True
            tf.confirmed_at = timezone.now()
            tf.save()
            return Response({"success": True, "message": "تم تفعيل المصادقة الثنائية"})
        return Response({"success": False, "message": "رمز غير صحيح"}, status=400)

    @action(detail=False, methods=["post"])
    def disable(self, request):
        tf = self._tf(request)
        tf.enabled = False
        tf.secret = ""
        tf.save()
        return Response({"success": True, "message": "تم إيقاف المصادقة الثنائية"})
