from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Budget, Category, Transaction
from .public_user import get_public_user
from .serializers import BudgetSerializer, CategorySerializer, TransactionSerializer


def money(value) -> str:
    """Format amounts as fixed 2-decimal strings."""
    if value is None:
        value = Decimal("0.00")
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)
    search_fields = ("name",)
    ordering_fields = ("name", "type", "created_at")

    def get_queryset(self):
        qs = Category.objects.filter(user=get_public_user())
        cat_type = self.request.query_params.get("type")
        if cat_type in (Category.Type.INCOME, Category.Type.EXPENSE):
            qs = qs.filter(type=cat_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=get_public_user())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.transactions.exists():
            return Response(
                {
                    "detail": (
                        "Cannot delete a category that has transactions. "
                        "Delete or reassign those transactions first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = (AllowAny,)
    search_fields = ("note",)
    ordering_fields = ("date", "amount", "created_at")

    def get_queryset(self):
        qs = Transaction.objects.filter(user=get_public_user()).select_related(
            "category"
        )
        params = self.request.query_params

        tx_type = params.get("type")
        if tx_type in (Transaction.Type.INCOME, Transaction.Type.EXPENSE):
            qs = qs.filter(type=tx_type)

        category = params.get("category")
        if category:
            qs = qs.filter(category_id=category)

        start = params.get("start")
        if start:
            qs = qs.filter(date__gte=start)

        end = params.get("end")
        if end:
            qs = qs.filter(date__lte=end)

        search = params.get("search")
        if search:
            qs = qs.filter(note__icontains=search)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=get_public_user())


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = (AllowAny,)
    ordering_fields = ("year", "month", "limit_amount")

    def get_queryset(self):
        qs = Budget.objects.filter(user=get_public_user()).select_related("category")
        params = self.request.query_params
        month = params.get("month")
        year = params.get("year")
        if month:
            qs = qs.filter(month=month)
        if year:
            qs = qs.filter(year=year)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=get_public_user())


class SummaryReportView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        today = date.today()
        try:
            month = int(request.query_params.get("month", today.month))
            year = int(request.query_params.get("year", today.year))
        except (TypeError, ValueError):
            return Response(
                {"detail": "month and year must be integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (1 <= month <= 12) or not (2000 <= year <= 2100):
            return Response(
                {"detail": "Invalid month or year."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = get_public_user()
        _, last_day = monthrange(year, month)
        start = date(year, month, 1)
        end = date(year, month, last_day)

        qs = Transaction.objects.filter(user=user, date__gte=start, date__lte=end)

        income_total = (
            qs.filter(type=Transaction.Type.INCOME).aggregate(t=Sum("amount"))["t"]
            or Decimal("0.00")
        )
        expense_total = (
            qs.filter(type=Transaction.Type.EXPENSE).aggregate(t=Sum("amount"))["t"]
            or Decimal("0.00")
        )

        by_category = []
        cat_rows = (
            qs.values("category_id", "category__name", "type")
            .annotate(total=Sum("amount"))
            .order_by("type", "category__name")
        )
        for row in cat_rows:
            by_category.append(
                {
                    "category_id": row["category_id"],
                    "category_name": row["category__name"],
                    "type": row["type"],
                    "total": money(row["total"]),
                }
            )

        budgets = Budget.objects.filter(user=user, month=month, year=year).select_related(
            "category"
        )
        budget_status = []
        for b in budgets:
            spent = (
                Transaction.objects.filter(
                    user=user,
                    category=b.category,
                    type=Transaction.Type.EXPENSE,
                    date__gte=start,
                    date__lte=end,
                ).aggregate(t=Sum("amount"))["t"]
                or Decimal("0.00")
            )
            remaining = b.limit_amount - spent
            budget_status.append(
                {
                    "budget_id": b.id,
                    "category_id": b.category_id,
                    "category_name": b.category.name,
                    "limit_amount": money(b.limit_amount),
                    "spent": money(spent),
                    "remaining": money(remaining),
                    "over_budget": spent > b.limit_amount,
                }
            )

        return Response(
            {
                "month": month,
                "year": year,
                "total_income": money(income_total),
                "total_expense": money(expense_total),
                "balance": money(income_total - expense_total),
                "by_category": by_category,
                "budgets": budget_status,
            }
        )


class MonthlyReportView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            months = int(request.query_params.get("months", 6))
        except (TypeError, ValueError):
            return Response(
                {"detail": "months must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        months = max(1, min(months, 24))

        today = date.today()
        start_month = today.month - (months - 1)
        start_year = today.year
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start = date(start_year, start_month, 1)

        qs = (
            Transaction.objects.filter(user=get_public_user(), date__gte=start)
            .annotate(period=TruncMonth("date"))
            .values("period", "type")
            .annotate(total=Sum("amount"))
            .order_by("period")
        )

        series_map = {}
        y, m = start_year, start_month
        for _ in range(months):
            key = f"{y:04d}-{m:02d}"
            series_map[key] = {
                "year": y,
                "month": m,
                "income": Decimal("0.00"),
                "expense": Decimal("0.00"),
            }
            m += 1
            if m > 12:
                m = 1
                y += 1

        for row in qs:
            period = row["period"]
            if period is None:
                continue
            key = f"{period.year:04d}-{period.month:02d}"
            if key not in series_map:
                continue
            if row["type"] == Transaction.Type.INCOME:
                series_map[key]["income"] = row["total"]
            else:
                series_map[key]["expense"] = row["total"]

        series = []
        for key in series_map:
            item = series_map[key]
            income = item["income"]
            expense = item["expense"]
            series.append(
                {
                    "year": item["year"],
                    "month": item["month"],
                    "label": key,
                    "income": money(income),
                    "expense": money(expense),
                    "balance": money(income - expense),
                }
            )

        return Response({"months": months, "series": series})
