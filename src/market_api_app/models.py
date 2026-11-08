from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class ArchiveModel(models.Model):
    is_archived = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_archived = True
        self.save()


class Image(models.Model):
    src = models.CharField(max_length=100)
    alt = models.CharField(max_length=100, blank=True, null=True)


class Tag(models.Model):
    name = models.CharField(max_length=100)


class User(AbstractUser, ArchiveModel):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, null=True, blank=True)

    avatar = models.ForeignKey(
        Image, on_delete=models.SET_NULL, related_name="user", null=True, blank=True
    )

    def delete(self, *args, **kwargs):
        self.is_active = False
        super().delete(*args, **kwargs)


class Category(ArchiveModel):
    title = models.CharField(max_length=100)

    image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, related_name="category", null=True, blank=True
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="subcategories",
        null=True,
        blank=True,
    )


class Product(ArchiveModel):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    full_description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    free_delivery = models.BooleanField(default=False)
    reviews_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )

    images = models.ManyToManyField(Image, related_name="products", blank=True)
    tags = models.ManyToManyField(Tag, related_name="products")

    def __str__(self) -> str:
        return self.title


class Review(models.Model):
    email = models.EmailField()
    text = models.TextField()
    rate = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=100, blank=True, default="")

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )


class Specification(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="specifications"
    )


class Sale(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_from = models.DateField()
    date_to = models.DateField()

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    images = models.ManyToManyField(Image, related_name="sales")


class Order(ArchiveModel):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=100)
    delivery_type = models.CharField(max_length=100)
    payment_type = models.CharField(max_length=100)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="orders", blank=True, null=True
    )


class OrderProduct(models.Model):
    count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="orders"
    )


class Payment(models.Model):
    number = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    month = models.CharField(max_length=100)
    year = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    status = models.CharField(max_length=100, default="pending")

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment"
    )


class BasketItem(models.Model):
    count = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="basket_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="basket_items"
    )
