from django.contrib import admin

from apps.wallet.models import LedgerEntry, LedgerTransaction


class LedgerEntryInline(admin.TabularInline):
    model = LedgerEntry
    extra = 0
    readonly_fields = ("account", "amount", "direction", "user", "creado_en")


@admin.register(LedgerTransaction)
class LedgerTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "referencia", "idempotency_key", "creado_en")
    inlines = [LedgerEntryInline]
