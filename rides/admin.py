from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin
from rides.models import Destination, Ride, RideConfirmation, DestinationAttachment


class RideAdmin(admin.ModelAdmin):
    raw_id_fields = ("destination", "start", "customer", "rider_link")


class DestinationAttachmentAdmin(admin.ModelAdmin):
    raw_id_fields = ("destination", "uploaded_by")


class DestinationAttachmentInline(AdminImageMixin, admin.TabularInline):
    model = DestinationAttachment
    raw_id_fields = ("destination", "uploaded_by")


class DestinationAdmin(admin.ModelAdmin):
    inlines = [
        DestinationAttachmentInline
    ]


admin.site.register(Destination, DestinationAdmin)
admin.site.register(DestinationAttachment, DestinationAttachmentAdmin)
admin.site.register(Ride, RideAdmin)
admin.site.register(RideConfirmation)
