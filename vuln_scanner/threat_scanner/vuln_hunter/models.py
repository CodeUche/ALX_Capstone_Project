from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ScanJob(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    target = models.URLField()
    scan_type = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(auto_now=True)
    task_id = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.scan_type} on {self.target} ({self.status})"


class ScanResult(models.Model):
    scan_job_id = models.OneToOneField(ScanJob, on_delete=models.CASCADE)
    output_text = models.TextField()
    parsed_data = models.JSONField()
    vulnerabilities = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan Result for {self.scan_job_id}"


class AuthenticationLog(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} by {self.user_id}"
