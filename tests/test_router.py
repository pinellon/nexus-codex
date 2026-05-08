from app.core.command_router import CommandRouter
from app.core.safety import SafetyManager


def test_basic_routes():
    router = CommandRouter("nexus")

    assert router.route("nexus abrir chrome").intent == "abrir_app"
    assert router.route("nexus pesquisar python no google").intent == "pesquisar_google"
    assert router.route("nexus rode esse codigo").intent == "executar_codigo"
    assert router.route("nexus desligar pc").intent == "desligar_pc"


def test_dangerous_confirmation_can_cancel():
    router = CommandRouter("nexus")
    command = router.route("nexus desligar pc")

    assert SafetyManager().confirm_if_needed(command, lambda _q: False) == "Acao cancelada."
