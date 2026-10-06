from rest_framework import serializers

from .models import SalesReport


class SalesReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(read_only=True)

    class Meta:
        model = SalesReport
        fields = [
            "id",
            "admin",
            "manager",
            "generated_by_name",
            "start_date",
            "end_date",
            "sales_count",
            "items_sold",
            "total_revenue",
            "generated_at",
        ]
        read_only_fields = fields
