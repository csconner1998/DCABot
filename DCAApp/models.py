from django.db import models

class InputData(models.Model):
    address = models.CharField(max_length=100)
    private_key = models.CharField(max_length=100)
    from_asset_id = models.IntegerField()
    to_asset_id = models.IntegerField()
    blocks_per_invoke = models.IntegerField()
    max_invokes = models.IntegerField()
    dapp_address = models.CharField(max_length=100)
    max_difference = models.IntegerField()
    function_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    NETWORK_CHOICES = (
        ('MainNet', 'Main Network'),
        ('TestNet', 'Test Network'),
        ('CustomNet', 'Custom Network'),
    )
    network = models.CharField(max_length=20, choices=NETWORK_CHOICES)

    def __str__(self):
        return self.address  # Change this to whatever field you want to represent the object
