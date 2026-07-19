from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import uuid
from .models import (
    ProductCatalog, Customer, Cart, CartItem, Order, OrderItem,
    POSession, POSTransaction, POSTransactionItem
)
from .serializers import (
    ProductCatalogSerializer, CustomerSerializer, CartSerializer,
    CartItemSerializer, OrderSerializer, OrderItemSerializer,
    POSessionSerializer, POSTransactionSerializer, POSTransactionItemSerializer
)

class ProductCatalogViewSet(viewsets.ModelViewSet):
    queryset = ProductCatalog.objects.all()
    serializer_class = ProductCatalogSerializer
    permission_classes = [IsAuthenticated]

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += int(quantity)
            item.save()

        serializer = CartItemSerializer(item)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        cart = self.get_object()
        customer_id = request.data.get('customer_id')

        if not customer_id:
            return Response({"error": "customer_id required"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer_id,
            subtotal=cart.total,
            total=cart.total
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price
            )

        cart.status = 'converted'
        cart.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = Order.objects.filter(status=status_filter)
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            order.status = new_status
            order.save()
        return Response({"status": "updated"})


    @action(detail=True, methods=['post'])
    def online_payment(self, request, pk=None):
        order = self.get_object()
        payment_method = request.data.get('payment_method', 'card')
        # Simulate payment processing
        payment = Payment.objects.create(
            payment_number=f"PAY-{uuid.uuid4().hex[:8].upper()}",
            company=order.customer,
            invoice=None,
            amount=order.total,
            method=payment_method,
            status='completed',
            date=timezone.now().date()
        )
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        return Response({"status": "paid", "payment_id": payment.id})

    @action(detail=True, methods=['get'])
    def shipping_track(self, request, pk=None):
        order = self.get_object()
        # Simulate shipping tracking
        return Response({
            "order": order.order_number,
            "status": order.status,
            "tracking_number": f"TRK-{order.id:06d}",
            "estimated_delivery": "2026-08-01",
            "history": [
                {"status": "Order Placed", "date": order.created_at},
                {"status": "Processing", "date": order.updated_at},
                {"status": "Shipped", "date": None}
            ]
        })

    @action(detail=False, methods=['get'])
    def customer_portal(self, request):
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            orders = Order.objects.filter(customer_id=customer_id)
            total_spent = sum(o.total for o in orders)
            return Response({
                "customer_id": customer_id,
                "total_orders": orders.count(),
                "total_spent": total_spent,
                "recent_orders": OrderSerializer(orders[:5], many=True).data
            })
        return Response({"error": "customer_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def apply_discount(self, request, pk=None):
        order = self.get_object()
        discount_code = request.data.get('code', '')
        # Simulate discount codes
        discounts = {'SAVE10': 0.10, 'SAVE20': 0.20, 'HALF': 0.50}
        discount_rate = discounts.get(discount_code.upper(), 0)

        if discount_rate > 0:
            order.discount = order.subtotal * discount_rate
            order.total = order.subtotal + order.tax_amount - order.discount
            order.save()
            return Response({"status": "applied", "discount": order.discount, "new_total": order.total})
        return Response({"error": "Invalid discount code"}, status=status.HTTP_400_BAD_REQUEST)


class POSessionViewSet(viewsets.ModelViewSet):
    queryset = POSession.objects.all()
    serializer_class = POSessionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def open_sessions(self, request):
        sessions = POSession.objects.filter(status='open')
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        session = self.get_object()
        session.status = 'closed'
        session.closing_cash = request.data.get('closing_cash', 0)
        from django.utils import timezone
        session.closed_at = timezone.now()
        session.save()
        return Response({"status": "closed"})

class POSTransactionViewSet(viewsets.ModelViewSet):
    queryset = POSTransaction.objects.all()
    serializer_class = POSTransactionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_session(self, request):
        session_id = request.query_params.get('session_id')
        if session_id:
            transactions = POSTransaction.objects.filter(session_id=session_id)
            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data)
        return Response({"error": "session_id required"}, status=status.HTTP_400_BAD_REQUEST)
