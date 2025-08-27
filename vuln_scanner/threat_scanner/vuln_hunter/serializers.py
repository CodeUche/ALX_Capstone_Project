from rest_framework import serializers
from .models import ScanJob


class ScanJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanJob
        fields = "__all__"
        read_only_fields = [
            "id",
            "target",
            "scan_type",
            "status",
            "result",
            "start_time",
            "end_time",
        ]
