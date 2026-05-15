"""Voice profiles used by the professional speech layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class VoiceProfile:
    id: str
    label: str
    provider: str
    voice: str
    speed: float
    pitch: str
    instructions: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


PROFILES: dict[str, VoiceProfile] = {
    "natural": VoiceProfile(
        id="natural",
        label="Natural",
        provider="auto",
        voice="alloy",
        speed=1.0,
        pitch="+0Hz",
        instructions="Fale em portugues do Brasil com tom natural, claro e direto.",
    ),
    "jarvis": VoiceProfile(
        id="jarvis",
        label="Jarvis",
        provider="auto",
        voice="onyx",
        speed=1.02,
        pitch="-2Hz",
        instructions=(
            "Fale em portugues do Brasil com tom calmo, confiante, preciso e profissional. "
            "Soar como assistente pessoal de alta eficiencia, sem exagerar na emocao."
        ),
    ),
    "professor": VoiceProfile(
        id="professor",
        label="Professor",
        provider="auto",
        voice="echo",
        speed=0.96,
        pitch="+0Hz",
        instructions="Fale em portugues do Brasil como tutor paciente, didatico e objetivo.",
    ),
    "rapido": VoiceProfile(
        id="rapido",
        label="Rapido",
        provider="auto",
        voice="alloy",
        speed=1.14,
        pitch="+0Hz",
        instructions="Fale em portugues do Brasil com ritmo um pouco mais rapido, mantendo clareza.",
    ),
    "calmo": VoiceProfile(
        id="calmo",
        label="Calmo",
        provider="auto",
        voice="shimmer",
        speed=0.9,
        pitch="-1Hz",
        instructions="Fale em portugues do Brasil com tom tranquilo, acolhedor e sem pressa.",
    ),
}


def get_profile(profile_id: str | None) -> VoiceProfile:
    key = (profile_id or "jarvis").strip().lower()
    return PROFILES.get(key, PROFILES["jarvis"])


def list_profiles() -> list[dict[str, object]]:
    return [profile.to_dict() for profile in PROFILES.values()]
