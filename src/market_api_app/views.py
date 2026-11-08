import json
import math
import os
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import (authenticate, get_user_model, login, logout,
                                 update_session_auth_hash)
from django.core.files.storage import default_storage
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (BasketItem, Category, Image, Order, OrderProduct, Payment,
                     Product, Review, Sale, Tag)
from .parsers import TextPlainJSONParser
from .serializers import (CategorySerializer, ImageSerializer,
                          OrderProductSerializer, OrderSerializer,
                          ProductFullSerializer, ProductShortSerializer,
                          ProfileSerializer, ReviewSerializer,
                          SaleItemSerializer, TagSerializer)

User = get_user_model()

###########################################################
###########################################################
###########################################################
"""
API-система авторизации, которая необходима для frontend'а, который обращается по /api/sign-in /api/sign-out и /api/sign-up

MarketLoginView - для авторизации пользователя
MarketLogoutView - для выхода пользователя
MarketRegisterView - для регистрации пользователя
"""


class MarketLoginView(APIView):
    authentication_classes = []
    permission_classes = []
    parser_classes = [JSONParser, TextPlainJSONParser, FormParser, MultiPartParser]

    def post(self, request):
        data = request.data

        if len(data) == 1:
            key = list(data.keys())[0]
            try:
                data = json.loads(key)
            except json.JSONDecodeError:
                pass

        if not data or (isinstance(data, dict) and len(data) == 0):
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, ValueError):
                pass

        login_field = data.get("login") or data.get("username")
        password = data.get("password")

        if not login_field or not password:
            """Не мог не удержаться от отсылки на Надоедливого Апельсина, в виду Свагера.
            Я не ожидал что доживу до пасхалок к нему в серьёзной среде"""
            return Response(
                {
                    "error": "Login and password is required. Example: login: Annoying Orange, password: Knife"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request=request, username=login_field, password=password)

        if not user:
            return Response(
                {"error": "Wrong login or password. Pls, try again"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": getattr(user, "full_name", ""),
                },
            }
        )


class MarketRegisterView(APIView):
    authentication_classes = []
    permission_classes = []
    parser_classes = [JSONParser, TextPlainJSONParser, FormParser, MultiPartParser]

    def post(self, request):
        data = request.data

        if len(data) == 1:
            key = list(data.keys())[0]
            try:
                data = json.loads(key)
            except json.JSONDecodeError:
                pass

        if not data or (isinstance(data, dict) and len(data) == 0):
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, ValueError):
                pass

        username = data.get("username") or data.get("login")
        email = data.get("email", "")
        password = data.get("password")
        password2 = data.get("password2")

        if not username or not password:
            return Response(
                {
                    "error": "Login and password is required. Example: login: Annoying Orange, password: Knife"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password2 and password != password2:
            return Response(
                {
                    "error": "Password don't matching. Must be like pass1: Knife, pass2: Knife"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {
                    "error": "This login is busy. Take another login. Example: AnnoyingOrangeIsCool"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            full_name=data.get("full_name", ""),
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {"id": user.id, "username": user.username, "email": user.email},
            },
            status=status.HTTP_201_CREATED,
        )


class MarketLogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


###########################################################
###########################################################
###########################################################

"""
Профили и пользователи
"""


class ProfileView(APIView):

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(ProfileSerializer(request.user).data)

    def post(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        full_name = request.data.get("fullName")
        email = request.data.get("email")
        phone = request.data.get("phone")

        if not full_name or not email or not phone:
            return Response(
                {"error": "fullName, email and phone is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.full_name = full_name
        user.email = email
        user.phone = phone
        user.save()

        return Response(ProfileSerializer(user).data)


class ProfileAvatarView(APIView):

    def post(self, request: Request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        file = request.FILES.get("avatar")
        if not file:
            return Response(
                {"error": "avatar file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not file.content_type.startswith("image/"):
            return Response(
                {"error": "avatar must be an image"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
            return Response(
                {"error": "unsupported file type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filename = uuid4().hex + ext
        saved_path = default_storage.save(f"avatars/{filename}", file)

        src = settings.MEDIA_URL + saved_path

        image = Image.objects.create(src=src, alt=request.user.username)

        user = request.user
        user.avatar = image
        user.save()

        return Response(ImageSerializer(image).data)


class ProfilePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        password = request.data.get("password")

        if password:
            user = request.user
            user.set_password(password)
            user.save()

            update_session_auth_hash(request, user)

            return Response(status=status.HTTP_200_OK)

        else:
            return Response(
                {"error": "password is required"}, status=status.HTTP_400_BAD_REQUEST
            )


###########################################################
###########################################################
###########################################################
"""
Views каталога и всего что с ним связано напрямую: каталог, теги, sale и прочее
"""


class CatalogView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def _safe_int(value, default=None):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_decimal(value):
        try:
            return Decimal(value)
        except (TypeError, ValueError, InvalidOperation):
            return None

    def get(self, request):
        qp = request.query_params
        queryset = (
            Product.objects.filter(is_archived=False)
            .select_related("category")
            .prefetch_related("images", "tags")
        )

        name = qp.get("filter[name]")
        if name:
            queryset = queryset.filter(title__icontains=name)

        min_price = self._safe_decimal(qp.get("filter[minPrice]"))
        max_price = self._safe_decimal(qp.get("filter[maxPrice]"))
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if qp.get("filter[freeDelivery]") in ("true", "1"):
            queryset = queryset.filter(free_delivery=True)
        if qp.get("filter[available]", "true") in ("true", "1"):
            queryset = queryset.filter(count__gt=0)

        category = self._safe_int(qp.get("category"))
        if category is not None:
            queryset = queryset.filter(category_id=category)

        tags = qp.getlist("tags[]") or qp.getlist("tags")
        clean_tags = [t for t in (self._safe_int(x) for x in tags) if t is not None]
        if clean_tags:
            queryset = queryset.filter(tags__id__in=clean_tags).distinct()

        sort_map = {
            "rating": "rating",
            "price": "price",
            "reviews": "reviews_count",
            "date": "date",
        }
        order = sort_map.get(qp.get("sort"), "date")
        if qp.get("sortType", "dec") == "dec":
            order = "-" + order
        queryset = queryset.order_by(order)

        page = self._safe_int(qp.get("currentPage"), 1)
        limit = max(1, self._safe_int(qp.get("limit"), 20))
        last_page = math.ceil(queryset.count() / limit) or 1
        items = queryset[(page - 1) * limit : page * limit]

        return Response(
            {
                "items": ProductShortSerializer(items, many=True).data,
                "currentPage": page,
                "lastPage": last_page,
            }
        )


class CatalogPopularProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = (
            Product.objects.filter(is_archived=False)
            .select_related("category")
            .prefetch_related("images", "tags")
            .order_by("-rating", "-reviews_count")
        )
        serializer = ProductShortSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CatalogLimitedProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.now().date()
        queryset = (
            Product.objects.filter(
                is_archived=False, sales__date_from__lte=today, sales__date_to__gte=today
            )
            .distinct()
            .select_related("category")
            .prefetch_related("images", "tags")
            .order_by("-rating")[:8]
        )
        serializer = ProductShortSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TagsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        tags = Tag.objects.all()
        category = request.query_params.get("category")
        try:
            category = int(category) if category else None
        except (TypeError, ValueError):
            category = None
        if category:
            tags = tags.filter(
                products__category_id=category, products__is_archived=False
            ).distinct()
        return Response(TagSerializer(tags, many=True).data)


class CategoriesView(APIView):
    def get(self, request):
        categories = (
            Category.objects.filter(parent__isnull=True, is_archived=False)
            .select_related("image")
            .prefetch_related(
                Prefetch(
                    "subcategories",
                    queryset=Category.objects.filter(is_archived=False).select_related(
                        "image"
                    ),
                )
            )
        )
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class SaleView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.now().date()
        qp = request.query_params

        queryset = (
            Sale.objects.filter(
                date_from__lte=today, date_to__gte=today, product__is_archived=False
            )
            .prefetch_related("images")
            .order_by("-date_from")
        )

        page = int(qp.get("currentPage", 1))
        limit = int(qp.get("limit", 20))
        last_page = math.ceil(queryset.count() / limit) or 1
        items = queryset[(page - 1) * limit : page * limit]

        return Response(
            {
                "items": SaleItemSerializer(items, many=True).data,
                "currentPage": page,
                "lastPage": last_page,
            },
            status=status.HTTP_200_OK,
        )


###########################################################
###########################################################
###########################################################

"""
Продукты и корзина

"""


class BasketView(APIView):
    parser_classes = [JSONParser, TextPlainJSONParser]

    def get(self, request):

        if not request.user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)

        basket_items = (
            BasketItem.objects.filter(user=request.user, product__is_archived=False)
            .select_related("product")
            .prefetch_related("product__tags", "product__images")
        )

        serializer = OrderProductSerializer(basket_items, many=True)

        return Response(serializer.data)

    def post(self, request):

        if not request.user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)

        product_id = request.data.get("id")
        count = request.data.get("count", 1)

        if not product_id:
            return Response(
                {"error": "id required"}, status=status.HTTP_400_BAD_REQUEST
            )

        product = get_object_or_404(Product, id=product_id, is_archived=False)

        basket_item, created = BasketItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={"count": count, "price": product.price},
        )

        if not created:
            basket_item.count += count
            basket_item.price = product.price
            basket_item.save()

        basket_items = (
            BasketItem.objects.filter(user=request.user, product__is_archived=False)
            .select_related("product")
            .prefetch_related("product__images", "product__tags")
        )
        serializer = OrderProductSerializer(basket_items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):

        if not request.user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)

        product_id = request.data.get("id")
        count = request.data.get("count")

        if not product_id:
            return Response(
                {"error": "id required"}, status=status.HTTP_400_BAD_REQUEST
            )

        basket_item = get_object_or_404(
            BasketItem,
            user=request.user,
            product_id=product_id,
            product__is_archived=False,
        )

        if count is None or count >= basket_item.count:
            basket_item.delete()
        else:
            basket_item.count -= count
            basket_item.save()

        basket_items = (
            BasketItem.objects.filter(user=request.user, product__is_archived=False)
            .select_related("product")
            .prefetch_related("product__images", "product__tags")
        )
        serializer = OrderProductSerializer(basket_items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class BannersView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.now().date()
        queryset = (
            Product.objects.filter(
                is_archived=False, sales__date_from__lte=today, sales__date_to__gte=today
            )
            .distinct()
            .select_related("category")
            .prefetch_related("images", "tags")
            .order_by("-rating")[:3]
        )
        serializer = ProductShortSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductFullView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.prefetch_related(
                "images", "tags", "reviews", "specifications"
            ),
            id=pk,
            is_archived=False,
        )
        serializer = ProductFullSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductReviewView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, TextPlainJSONParser]

    def post(self, request, pk):
        product = get_object_or_404(Product, id=pk, is_archived=False)

        email = request.data.get("email")
        text = request.data.get("text")
        rate = request.data.get("rate")
        author = request.data.get("author")

        if not email or not text or rate is None:
            if request.user.is_authenticated and request.user.email:
                email = request.user.email
            else:
                return Response(
                    {"error": "email, text and rate is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            rate = int(rate)
        except (TypeError, ValueError):
            return Response(
                {"error": "rate must be integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not 1 <= rate <= 5:
            return Response(
                {"error": "rate must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not author:
            if request.user.is_authenticated:
                author = request.user.full_name or request.user.username
            else:
                return Response(
                    {"error": "author is required for guests"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        Review.objects.create(
            product=product, author=author, email=email, text=text, rate=rate
        )

        reviews = product.reviews.all()
        product.reviews_count = reviews.count()
        product.rating = round(sum(r.rate for r in reviews) / reviews.count(), 1)
        product.save()

        serializer = ReviewSerializer(reviews.order_by("-date"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


###########################################################
###########################################################
###########################################################
"""
Заказы и оплата
"""


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            order = get_object_or_404(Order, id=pk, user=request.user, is_archived=False)
            serializer = OrderSerializer(order)
        else:
            orders = (
                Order.objects.filter(is_archived=False, user=request.user)
                .order_by("-created_at")
                .prefetch_related(
                    "products__product__images", "products__product__tags"
                )
            )
            serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, pk=None):

        if request.data:
            total = 0
            if pk:
                order = get_object_or_404(
                    Order, id=pk, user=request.user, is_archived=False
                )
                order.full_name = request.data.get("fullName")
                order.email = request.data.get("email")
                order.phone = request.data.get("phone")
                order.delivery_type = request.data.get("deliveryType")
                order.payment_type = request.data.get("paymentType")
                order.city = request.data.get("city")
                order.address = request.data.get("address")
                order.status = "accepted"
                order.save()
            else:
                order = Order.objects.create(
                    user=request.user,
                    status="pending",
                    total_cost=total,
                    email="",
                    full_name="",
                    phone="",
                    delivery_type="",
                    payment_type="",
                    city="",
                    address="",
                )

                for item in request.data:
                    product = get_object_or_404(
                        Product, id=item["id"], is_archived=False
                    )
                    OrderProduct.objects.create(
                        order=order,
                        product=product,
                        count=item["count"],
                        price=product.price,
                    )
                    total += product.price * item["count"]

                order.total_cost = total
                order.save()
                BasketItem.objects.filter(user=request.user).delete()

            return Response({"orderId": order.id}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Orders is required"}, status=status.HTTP_400_BAD_REQUEST
            )


class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user, is_archived=False)

        if hasattr(order, "payment") and order.payment.status == "success":
            return Response(
                {"error": "Payment is exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        raw_number = (request.data.get("number") or "").strip()
        number = "".join(ch for ch in raw_number if ch.isdigit())
        name = (request.data.get("name") or "").strip()
        month = (request.data.get("month") or "").strip()
        year = (request.data.get("year") or "").strip()
        code = (request.data.get("code") or "").strip()

        if len(year) == 2:
            year = "20"+ year

        if raw_number and (not number or len(number) < 8):
            print(number)
            return Response(
                {"error": "number must be 8 digits or less"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if month and (not month.isdigit() or not 1 <= int(month) <= 12):
            return Response(
                {"error": "month must be between 01 and 12"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if year and (not year.isdigit() or len(year) not in (2, 4)):
            return Response(
                {"error": "year must be 2 or 4 digits"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if code and (not code.isdigit() or len(code) != 3):
            return Response(
                {"error": "code must be 3 digits"}, status=status.HTTP_400_BAD_REQUEST
            )
        if month and year:
            now = timezone.now()
            if (int(year), int(month)) < (now.year, now.month):
                print(now.year, now.month)
                print(year, month)
                return Response(
                    {"error": "card date must be not less than today"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        card = number if len(number) < 4 else "*" * (len(number) - 4) + number[-4:]

        payment = Payment.objects.filter(order=order).first()
        if payment is None:
            payment = Payment(order=order)
        payment.number = card
        payment.name = name
        payment.month = month
        payment.year = year
        payment.code = code
        if number and int(number) % 2 == 0 and not number.endswith("0"):
            payment.status = "success"
        else:
            payment.status = "error"
        payment.save()

        if payment.status == "success":
            order.status = "paid"
            order.save()
            return Response(status=status.HTTP_200_OK)

        return Response(
            {"error": "Payment error"}, status=status.HTTP_400_BAD_REQUEST
        )