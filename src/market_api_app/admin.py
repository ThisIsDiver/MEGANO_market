from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .admin_mixins import SoftDeleteAdminMixin
from .models import Category, Order, OrderProduct, Product, Review, User

# Register your models here.


class OrderProductInline(admin.TabularInline):
    model = OrderProduct


@admin.register(User)
class UserAdmin(SoftDeleteAdminMixin, DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (None, {"fields": ("full_name", "phone", "avatar")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("full_name", "phone", "avatar")}),
    )
    list_display = ("pk", "username", "full_name", "email", "phone", "avatar", "is_archived")


@admin.register(Product)
class ProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):

    list_display = (
        "pk",
        "title",
        "description",
        "full_description",
        "price",
        "count",
        "date",
        "free_delivery",
        "reviews_count",
        "rating",
        "is_archived"
    )
    list_display_links = (
        "pk",
        "title",
    )
    ordering = (
        "pk",
        "title",
    )


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("pk", "title", "parent", "is_archived")


@admin.register(Order)
class OrderAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "pk",
        "full_name",
        "email",
        "phone",
        "total_cost",
        "status",
        "created_at",
        "user",
        "is_archived"
    )

    inlines = [
        OrderProductInline,
    ]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("pk", "product", "author", "email", "rate", "date")
