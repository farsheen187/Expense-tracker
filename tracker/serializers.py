from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from rest_framework import serializers

from .models import Budget, Category, Transaction


def money(value) -> str:
    if value is None:
        value = Decimal("0.00")
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "type", "color", "created_at")
        read_only_fields = ("id", "created_at")


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "category",
            "category_name",
            "type",
            "amount",
            "date",
            "note",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "category_name")

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        category = attrs.get("category") or getattr(self.instance, "category", None)
        tx_type = attrs.get("type") or getattr(self.instance, "type", None)

        if category is not None:
            if category.user_id != user.id:
                raise serializers.ValidationError(
                    {"category": "Category not found or does not belong to you."}
                )
            if tx_type is not None and category.type != tx_type:
                raise serializers.ValidationError(
                    {
                        "category": (
                            f"Category type '{category.type}' does not match "
                            f"transaction type '{tx_type}'."
                        )
                    }
                )
        return attrs


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = (
            "id",
            "category",
            "category_name",
            "month",
            "year",
            "limit_amount",
            "spent",
            "remaining",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "category_name",
            "spent",
            "remaining",
            "created_at",
            "updated_at",
        )

    def validate_category(self, category):
        user = self.context["request"].user
        if category.user_id != user.id:
            raise serializers.ValidationError(
                "Category not found or does not belong to you."
            )
        if category.type != Category.Type.EXPENSE:
            raise serializers.ValidationError("Budgets can only be set for expense categories.")
        return category

    def _spent_for(self, obj):
        total = (
            Transaction.objects.filter(
                user=obj.user,
                category=obj.category,
                type=Transaction.Type.EXPENSE,
                date__year=obj.year,
                date__month=obj.month,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        return total

    def get_spent(self, obj):
        return money(self._spent_for(obj))

    def get_remaining(self, obj):
        return money(obj.limit_amount - self._spent_for(obj))
