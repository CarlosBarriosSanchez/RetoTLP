# Generated manually for Nivel 3

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RegistroAuditoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("secuencia", models.PositiveBigIntegerField(unique=True)),
                ("tipo_evento", models.CharField(max_length=64, verbose_name="tipo de evento")),
                ("referencia", models.CharField(blank=True, max_length=128)),
                ("payload", models.JSONField(default=dict)),
                ("hash_anterior", models.CharField(max_length=64)),
                ("hash_registro", models.CharField(max_length=64, unique=True)),
                ("ip_origen", models.GenericIPAddressField(blank=True, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="registros_auditoria",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de auditoría",
                "verbose_name_plural": "Registros de auditoría",
                "ordering": ["secuencia"],
            },
        ),
        migrations.CreateModel(
            name="ActividadSospechosa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("multiples_cuentas_ip", "Varias cuentas desde la misma IP"),
                            ("deposito_cashout_rapido", "Depósito seguido de cash-out rápido"),
                            ("apuestas_espejo", "Patrón de apuestas espejo"),
                        ],
                        max_length=48,
                    ),
                ),
                (
                    "severidad",
                    models.CharField(
                        choices=[("baja", "Baja"), ("media", "Media"), ("alta", "Alta")],
                        default="media",
                        max_length=16,
                    ),
                ),
                ("descripcion", models.TextField()),
                ("ip_origen", models.GenericIPAddressField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("resuelta", models.BooleanField(default=False)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alertas_fraude",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Actividad sospechosa",
                "verbose_name_plural": "Actividades sospechosas",
                "ordering": ["-creado_en"],
            },
        ),
    ]
