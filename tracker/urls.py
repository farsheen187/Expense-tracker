from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BudgetViewSet,
    CategoryViewSet,
    MonthlyReportView,
    SummaryReportView,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("budgets", BudgetViewSet, basename="budget")

urlpatterns = [
    path("reports/summary/", SummaryReportView.as_view(), name="report_summary"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="report_monthly"),
    path("", include(router.urls)),
]
