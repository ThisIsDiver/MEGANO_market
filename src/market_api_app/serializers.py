from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (BasketItem, Category, Image, Order, Product, Review, Sale,
                     Specification, Tag)

User = get_user_model()


###########################################################
###########################################################
###########################################################
"""
Простые сериализаторы для сериализаторов или views
"""

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["src", "alt"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class SubcategorySerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "title", "image"]


class CategorySerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "title", "image", "subcategories"]

###########################################################
###########################################################
###########################################################
"""
Профиль
"""

class ProfileSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source="full_name", read_only=True)
    avatar = ImageSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["fullName", "avatar", "email", "phone"]

###########################################################
###########################################################
###########################################################
"""
Сериализация продуктов
"""


class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    author = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["author", "email", "text", "rate", "date"]

    def get_author(self, obj):
        return obj.author or "Anonymous"
class SpecificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Specification
        fields = [
            "name",
            "value",
        ]

class ProductShortSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(source="category_id", read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source="reviews.count", read_only=True)
    freeDelivery = serializers.BooleanField(source="free_delivery", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "title",
            "price",
            "count",
            "date",
            "description",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]

class ProductFullSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(source="category_id", read_only=True)
    freeDelivery = serializers.BooleanField(source="free_delivery", read_only=True)
    fullDescription = serializers.CharField(source="full_description", read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)

    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "title",
            "price",
            "count",
            "date",
            "description",
            "fullDescription",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "specifications",
            "rating",
        ]

    def get_images(self, obj):
        return [image.src for image in obj.images.all()]

###########################################################
###########################################################
###########################################################
"""
Корзина, заказы,  и прочее
"""

class OrderProductSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="product.id", read_only=True)
    category = serializers.IntegerField(source="product.category_id", read_only=True)
    title = serializers.CharField(source="product.title", read_only=True)
    description = serializers.CharField(source="product.description", read_only=True)
    freeDelivery = serializers.BooleanField(
        source="product.free_delivery", read_only=True
    )
    images = ImageSerializer(source="product.images", many=True, read_only=True)
    tags = TagSerializer(source="product.tags", many=True, read_only=True)
    reviews = serializers.IntegerField(source="product.reviews.count", read_only=True)
    rating = serializers.FloatField(source="product.rating", read_only=True)
    date = serializers.DateTimeField(source="product.date", read_only=True)

    class Meta:
        model = BasketItem
        fields = [
            "id",
            "category",
            "title",
            "price",
            "count",
            "date",
            "description",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]

class OrderSerializer(serializers.ModelSerializer):
    fullName = serializers.CharField(source="full_name", read_only=True)
    totalCost = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="total_cost", read_only=True
    )
    deliveryType = serializers.CharField(source="delivery_type", read_only=True)
    paymentType = serializers.CharField(source="payment_type", read_only=True)
    products = OrderProductSerializer(many=True, read_only=True)
    createdAt = serializers.DateTimeField(
        source="created_at", format="%Y-%m-%d %H:%M", read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "fullName",
            "email",
            "phone",
            "products",
            "totalCost",
            "deliveryType",
            "paymentType",
            "city",
            "address",
            "createdAt",
        ]


class SaleItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="product.id", read_only=True)
    title = serializers.CharField(source="product.title", read_only=True)
    salePrice = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="sale_price", read_only=True
    )
    dateFrom = serializers.DateField(source="date_from", read_only=True)
    dateTo = serializers.DateField(source="date_to", read_only=True)

    images = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = ["id", "title", "price", "salePrice", "dateFrom", "dateTo", "images"]

    def get_images(self, obj):
        return [image.src for image in obj.images.all()]
