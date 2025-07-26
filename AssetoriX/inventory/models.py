from django.db import models
from django.utils import timezone


class Store(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField()

    def __str__(self):
        return f"{self.code} - {self.name}"


class Asset(models.Model):
    item = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    invoice_number = models.CharField(max_length=100)
    purchase_date = models.DateField()
    serial_number = models.CharField(max_length=100, unique=True)
    current_location = models.CharField(max_length=100, null=True, blank=True)
    previous_location = models.CharField(max_length=100, blank=True, null=True)
    supplier_name = models.CharField(max_length=100)
    working_status = models.CharField(max_length=50, null=True, blank=True)
    current_custodian = models.CharField(max_length=100, blank=True, null=True)
    previous_custodian = models.CharField(max_length=100,
                                          blank=True,
                                          null=True)
    warranty_end_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    location_last_updated = models.DateTimeField(null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old = Asset.objects.filter(pk=self.pk).first()

            # Track location change
            if old and old.current_location != self.current_location:
                self.previous_location = old.current_location
                self.location_last_updated = timezone.now()

            # Track custodian change
            if old and old.current_custodian != self.current_custodian:
                self.previous_custodian = old.current_custodian
                CustodianHistory.objects.create(
                    asset=self,
                    from_custodian=old.current_custodian or "N/A",
                    to_custodian=self.current_custodian or "N/A")
        else:
            # New asset entry
            self.location_last_updated = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item} - {self.serial_number}"


class CustodianHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    from_custodian = models.CharField(max_length=100)
    to_custodian = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.asset.serial_number}: {self.from_custodian} → {self.to_custodian} on {self.changed_at}"


class ReturnNote(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True, null=True)
    condition = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ReturnNote for {self.asset} - {self.condition}"
