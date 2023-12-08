from django.contrib import admin
from .models import DCASettings

@admin.register(DCASettings)
class DCASettingsAdmin(admin.ModelAdmin):
    list_display = ('id','user','address', 'from_asset_id', 'to_asset_id', 'blocks_per_invoke', 'max_invokes', 'network', 'running')
    search_fields = ('address', 'function_name', 'network', 'user')
    list_filter = ('network', 'max_invokes')
    # You can add more configurations as needed
    # Show user name instead of user ID
    def user(self, obj):
        return obj.user.username
