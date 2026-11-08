from django.urls import path

from .views import (BannersView, BasketView, CatalogLimitedProductsView,
                    CatalogPopularProductsView, CatalogView, CategoriesView,
                    MarketLoginView, MarketLogoutView, MarketRegisterView,
                    OrderView, PaymentView, ProductFullView, ProductReviewView,
                    ProfileAvatarView, ProfilePasswordView, ProfileView,
                    SaleView, TagsView)

urlpatterns = [
    path("sign-in/", MarketLoginView.as_view(), name="sign-in"),
    path("sign-up/", MarketRegisterView.as_view(), name="sign-up"),
    path("sign-out/", MarketLogoutView.as_view(), name="logout"),
    path("categories/", CategoriesView.as_view(), name="categories"),
    path("catalog/", CatalogView.as_view(), name="catalog"),
    path("tags/", TagsView.as_view(), name="tags"),
    path("sales/", SaleView.as_view(), name="sales"),
    path(
        "products/popular/",
        CatalogPopularProductsView.as_view(),
        name="popular-products",
    ),
    path(
        "products/limited/", CatalogLimitedProductsView.as_view(), name="products-sale"
    ),
    path("banners/", BannersView.as_view(), name="banners"),
    path("product/<int:pk>/", ProductFullView.as_view(), name="full-product"),
    path(
        "product/<int:pk>/reviews/", ProductReviewView.as_view(), name="product-reviews"
    ),
    path("basket/", BasketView.as_view(), name="basket"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/avatar/", ProfileAvatarView.as_view(), name="profile-avatar"),
    path("profile/password/", ProfilePasswordView.as_view(), name="profile-password"),
    path("orders/", OrderView.as_view(), name="order"),
    path("order/<int:pk>/", OrderView.as_view(), name="order-item"),
    path("payment/<int:pk>/", PaymentView.as_view(), name="payment"),
]
