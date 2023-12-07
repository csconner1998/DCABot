from django.contrib import admin
from .models import InputData

@admin.register(InputData)
class InputDataAdmin(admin.ModelAdmin):
    list_display = ('address', 'from_asset_id', 'to_asset_id', 'blocks_per_invoke', 'max_invokes', 'network')
    search_fields = ('address', 'function_name', 'network')
    list_filter = ('network', 'max_invokes')
    # You can add more configurations as needed
