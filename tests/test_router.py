from app.core.command_router import CommandRouter
from app.core.safety import SafetyManager
from app.intent_apps import detectar_intent_apps
from app.intent_desktop_actions import detect_desktop_intent
from app.intent_router import detectar_intent


def test_basic_routes():
    router = CommandRouter("nexus")

    assert router.route("nexus abrir chrome").intent == "abrir_app"
    assert router.route("nexus pesquisar python no google").intent == "pesquisar_google"
    assert router.route("nexus rode esse codigo").intent == "executar_codigo"
    assert router.route("nexus desligar pc").intent == "desligar_pc"


def test_smart_feature_routes():
    router = CommandRouter("nexus")

    focus = router.route("nexus modo foco")
    assert focus.intent == "run_template"
    assert focus.args["template"] == "modo_foco"

    health = router.route("nexus diagnostico do projeto")
    assert health.intent == "project_health"

    events = router.route("nexus ultimos eventos")
    assert events.intent == "session_summary"


def test_vision_routes():
    router = CommandRouter("nexus")

    screen = router.route("nexus descreve a tela")
    assert screen.domain == "vision"
    assert screen.args["intent"] == "describe_screen"

    code = router.route("nexus analisa o codigo na tela")
    assert code.domain == "vision"
    assert code.args["intent"] == "analyze_code"


def test_dangerous_confirmation_can_cancel():
    router = CommandRouter("nexus")
    command = router.route("nexus desligar pc")

    assert SafetyManager().confirm_if_needed(command, lambda _q: False) == "Acao cancelada."


def test_artist_request_uses_smart_music_route():
    router = CommandRouter("nexus")
    command = router.route("nexus quero ouvir luan santana")

    assert command.intent == "tocar_musica_smart"


def test_close_app_command_maps_to_window_close():
    command = detect_desktop_intent("fechar spotify")

    assert command is not None
    assert command.name == "close_window"
    assert command.params["title"] == "spotify"


def test_open_youtube_skips_app_launcher():
    assert detectar_intent_apps("abrir youtube") is None
    assert detectar_intent("abrir youtube").name == "abrir_youtube"
