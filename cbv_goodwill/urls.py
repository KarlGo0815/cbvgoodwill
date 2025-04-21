from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("lenders/", include("lenders.urls")),  # ✅ das hier ist wichtig
]
def get_urls(self):
    from django.urls import path
    urls = super().get_urls()
    custom_urls = [
        path('report/payments-raw/', payment_list_raw),
        path('report/payments-with-usage/', payment_list_with_usage),
        path('report/apartment-prices/', apartment_price_list),
    ]
    return custom_urls + urls
