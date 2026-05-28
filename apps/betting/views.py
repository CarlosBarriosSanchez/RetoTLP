from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.betting.models import Apuesta, EventoDeportivo, SeleccionMercado
from apps.betting.serializers import (
    ApuestaCombinadaSerializer,
    ApuestaSerializer,
    ColocarApuestaSerializer,
    ColocarCombinadaSerializer,
    EventoDeportivoListaSerializer,
)
from apps.betting.services import (
    ErrorApuesta,
    RequoteRequired,
    colocar_apuesta_combinada,
    colocar_apuesta_simple,
    ejecutar_cashout_apuesta,
)


class VistaListaEventos(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        eventos = EventoDeportivo.objects.prefetch_related("mercados__selecciones").all()
        return Response(EventoDeportivoListaSerializer(eventos, many=True).data)


class VistaColocarApuesta(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ColocarApuestaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = data.get("idempotency_key") or None
        if key == "":
            key = None

        try:
            evento = EventoDeportivo.objects.get(pk=data["event_id"])
            seleccion = SeleccionMercado.objects.select_related("mercado__evento").get(
                pk=data["selection_id"]
            )
            apuesta = colocar_apuesta_simple(
                request.user,
                evento,
                seleccion,
                data["stake"],
                idempotency_key=key,
                odds_esperada=data.get("odds_esperada"),
                confirmar_requote=data.get("confirmar_requote", False),
            )
        except EventoDeportivo.DoesNotExist:
            return Response({"error": "Evento no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except SeleccionMercado.DoesNotExist:
            return Response({"error": "Selección no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except RequoteRequired as e:
            return Response(
                {
                    "requiere_reconfirmacion": True,
                    "nueva_cuota": str(e.nueva_cuota),
                    "error": str(e),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except ErrorApuesta as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "apuesta": ApuestaSerializer(apuesta).data,
                "juego_responsable": (
                    "Apuesta con moneda virtual. Establece límites y juega con responsabilidad."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class VistaColocarCombinada(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ColocarCombinadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = data.get("idempotency_key") or None
        if key == "":
            key = None
        try:
            combinada = colocar_apuesta_combinada(
                request.user,
                data["selection_ids"],
                data["stake"],
                idempotency_key=key,
            )
        except ErrorApuesta as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "combinada": ApuestaCombinadaSerializer(combinada).data,
                "juego_responsable": "Apuesta combinada con moneda virtual. Juego responsable.",
            },
            status=status.HTTP_201_CREATED,
        )


class VistaCashout(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, apuesta_id):
        try:
            apuesta = Apuesta.objects.select_related("seleccion__mercado").get(
                pk=apuesta_id, user=request.user
            )
            apuesta = ejecutar_cashout_apuesta(apuesta)
        except Apuesta.DoesNotExist:
            return Response({"error": "Apuesta no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except ErrorApuesta as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "mensaje": "Cash-out aplicado.",
                "apuesta": ApuestaSerializer(apuesta).data,
            }
        )


class VistaMisApuestas(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        simples = request.user.apuestas.select_related("evento", "seleccion")[:50]
        combinadas = request.user.apuestas_combinadas.prefetch_related("piernas__evento")[:20]
        return Response(
            {
                "simples": ApuestaSerializer(simples, many=True).data,
                "combinadas": ApuestaCombinadaSerializer(combinadas, many=True).data,
            }
        )
