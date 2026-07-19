import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class NotificationConsumer(AsyncWebsocketConsumer):
    """Real-time notifications via WebSocket"""

    async def connect(self):
        self.user = self.scope["user"]
        if self.user == AnonymousUser():
            await self.close()
            return

        self.group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Connected as {self.user.username}"
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'ping':
            await self.send(text_data=json.dumps({"type": "pong"}))
        elif action == 'mark_read':
            notification_id = data.get('notification_id')
            await self.mark_notification_read(notification_id)
            await self.send(text_data=json.dumps({
                "type": "notification_marked_read",
                "notification_id": notification_id
            }))

    async def send_notification(self, event):
        """Receive notification from channel layer"""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "title": event.get("title"),
            "message": event.get("message"),
            "data": event.get("data"),
            "timestamp": event.get("timestamp")
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import WebhookDelivery
        # Mark notification as read logic here
        pass

class DashboardConsumer(AsyncWebsocketConsumer):
    """Real-time dashboard updates"""

    async def connect(self):
        self.group_name = "dashboard_updates"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial dashboard data
        data = await self.get_dashboard_data()
        await self.send(text_data=json.dumps({
            "type": "dashboard_data",
            "data": data
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'refresh':
            dashboard_data = await self.get_dashboard_data()
            await self.send(text_data=json.dumps({
                "type": "dashboard_data",
                "data": dashboard_data
            }))

    async def dashboard_update(self, event):
        """Receive dashboard update from channel layer"""
        await self.send(text_data=json.dumps({
            "type": "dashboard_update",
            "metric": event.get("metric"),
            "value": event.get("value"),
            "timestamp": event.get("timestamp")
        }))

    @database_sync_to_async
    def get_dashboard_data(self):
        from nexus.apps.core.models import Company
        from nexus.apps.hr.models import Employee
        from nexus.apps.pmo.models import Project, Task
        from nexus.apps.industry.models import Product
        from nexus.apps.accounting.models import Invoice
        from django.db.models import Count, Sum

        return {
            "total_companies": Company.objects.count(),
            "total_employees": Employee.objects.filter(status='active').count(),
            "total_projects": Project.objects.count(),
            "pending_tasks": Task.objects.filter(completed=False).count(),
            "low_stock": Product.objects.filter(quantity__lte=10).count(),
            "total_revenue": float(Invoice.objects.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0),
        }

class LiveChatConsumer(AsyncWebsocketConsumer):
    """Real-time chat support"""

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'general')
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": f"User joined the room",
                "username": "system",
                "timestamp": ""
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        username = data.get('username', 'anonymous')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
                "timestamp": ""
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "username": event["username"],
            "timestamp": event.get("timestamp", "")
        }))
