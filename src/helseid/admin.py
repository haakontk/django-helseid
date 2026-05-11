from django.contrib import admin
from .models import HelseIDProfile

# Register your models here.
@admin.register(HelseIDProfile)
class HelseIDProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_first_name", "get_last_name", "hpr_number", "subject")
    search_fields = ("user__username", "user__first_name", "user__last_name", "hpr_number", "subject")
    list_select_related = ("user",)

    @admin.display(description="First Name", ordering="user__first_name")
    def get_first_name(self, obj):
        return obj.user.first_name

    @admin.display(description="Last Name", ordering="user__last_name")
    def get_last_name(self, obj):
        return obj.user.last_name
