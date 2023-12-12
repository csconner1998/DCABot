from django.contrib import admin
from .models import DCASettings, UserWallet

@admin.register(DCASettings)
class DCASettingsAdmin(admin.ModelAdmin):
    list_display = ('id','user','address', 'from_asset_id', 'to_asset_id', 'blocks_per_invoke', 'max_invokes', 'network', 'running')
    search_fields = ('address', 'function_name', 'network', 'user')
    list_filter = ('network', 'max_invokes')
    # You can add more configurations as needed
    # Show user name instead of user ID
    def user(self, obj):
        return obj.user.username

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'public_address', 'public_key', 'encrypted_private_key')
    search_fields = ('user', 'public_address')
    list_filter = ('user',)
    # You can add more configurations as needed
    # Show user name instead of user ID
    def user(self, obj):
        return obj.user.username
