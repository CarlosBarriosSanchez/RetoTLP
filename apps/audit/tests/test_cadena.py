import pytest

from apps.audit.services import registrar_auditoria, verificar_integridad_cadena


@pytest.mark.django_db
def test_cadena_auditoria_valida():
    registrar_auditoria("test_a", {"monto": "10"}, referencia="ref-1")
    registrar_auditoria("test_b", {"monto": "20"}, referencia="ref-2")
    resultado = verificar_integridad_cadena()
    assert resultado["valida"] is True
    assert resultado["registros"] == 2


@pytest.mark.django_db
def test_cadena_detecta_alteracion():
    reg = registrar_auditoria("test", {"x": 1}, referencia="r1")
    reg.payload = {"x": 999}
    reg.save()
    resultado = verificar_integridad_cadena()
    assert resultado["valida"] is False


@pytest.mark.django_db
def test_registros_encadenados():
    r1 = registrar_auditoria("a", {}, "1")
    r2 = registrar_auditoria("b", {}, "2")
    assert r2.hash_anterior == r1.hash_registro
    assert r1.secuencia == 1
    assert r2.secuencia == 2
