from django.urls import path

from apps.betting.views import (
    VistaCashout,
    VistaColocarApuesta,
    VistaColocarCombinada,
    VistaListaEventos,
    VistaMisApuestas,
)

urlpatterns = [
    path("events/", VistaListaEventos.as_view(), name="events-list"),
    path("bets/", VistaColocarApuesta.as_view(), name="bets-place"),
    path("bets/combined/", VistaColocarCombinada.as_view(), name="bets-combined"),
    path("bets/<uuid:apuesta_id>/cashout/", VistaCashout.as_view(), name="bets-cashout"),
    path("bets/mine/", VistaMisApuestas.as_view(), name="bets-mine"),
]
