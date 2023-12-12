import os
import csv
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class DCASettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    private_key = models.CharField(max_length=100)
    
    # Get the CSV file path in the static directory
    csv_file = os.path.join(settings.STATICFILES_DIRS[0], 'assets.csv')  # Use the appropriate index for your directory

    # Choices for asset IDs from CSV
    with open(csv_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        asset_choices = [(row['asset_id'], row['asset_name']) for row in reader]
    from_asset_id = models.CharField(max_length=45, choices=asset_choices)
    to_asset_id = models.CharField(max_length=45, choices=asset_choices)
    blocks_per_invoke = models.IntegerField()
    max_invokes = models.IntegerField()
    dapp_address = models.CharField(max_length=100)
    max_difference = models.IntegerField(name='max_difference_in_percent')
    function_name = models.CharField(max_length=100)
    amount = models.IntegerField()
    running = models.BooleanField(default=False)  # Hidden field initially set to False
    NETWORK_CHOICES = (
        ('MainNet', 'Main Network'),
        ('TestNet', 'Test Network'),
        ('CustomNet', 'Custom Network'),
    )
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES)

    def __str__(self):
        # return user's unique identifier
        return self.user.username
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Validate model fields before saving
        super().save(*args, **kwargs)
