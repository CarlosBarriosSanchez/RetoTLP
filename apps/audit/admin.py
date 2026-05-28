from django.contrib import admin

from apps.audit.models import ActividadSospechosa, RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("secuencia", "tipo_evento", "referencia", "usuario", "ip_origen", "creado_en")
    list_filter = ("tipo_evento",)
    search_fields = ("referencia", "hash_registro", "usuario__username")
    readonly_fields = (
        "secuencia",
        "tipo_evento",
        "referencia",
        "payload",
        "hash_anterior",
        "hash_registro",
        "ip_origen",
        "usuario",
        "creado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ActividadSospechosa)
class ActividadSospechosaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "severidad", "usuario", "ip_origen", "resuelta", "creado_en")
    list_filter = ("tipo", "severidad", "resuelta")
    search_fields = ("descripcion", "usuario__username")
    readonly_fields = ("creado_en",)
