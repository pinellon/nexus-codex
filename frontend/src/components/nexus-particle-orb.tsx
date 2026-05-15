import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

import type { OrbState } from "@/hooks/useConversationMode";

export type NexusParticleOrbProps = {
  state: OrbState;
  speakingLevel?: number;
  intensity?: number;
  size?: number;
};

type ParticleConfig = {
  core: [number, number, number];
  glow: [number, number, number];
  speed: number;
  spread: number;
  alpha: number;
};

const PARTICLE_CONFIG: Record<OrbState, ParticleConfig> = {
  idle: { core: [56, 154, 255], glow: [34, 211, 238], speed: 0.45, spread: 0.9, alpha: 0.42 },
  listening: { core: [34, 211, 238], glow: [103, 232, 249], speed: 0.7, spread: 1, alpha: 0.56 },
  thinking: { core: [245, 158, 11], glow: [250, 204, 21], speed: 1.05, spread: 1.08, alpha: 0.58 },
  generating_audio: { core: [245, 158, 11], glow: [250, 204, 21], speed: 1.18, spread: 1.12, alpha: 0.6 },
  speaking: { core: [34, 197, 94], glow: [34, 211, 238], speed: 0.88, spread: 1.04, alpha: 0.62 },
  ready: { core: [34, 197, 94], glow: [134, 239, 172], speed: 0.52, spread: 0.92, alpha: 0.5 },
  interrupted: { core: [148, 163, 184], glow: [100, 116, 139], speed: 0.32, spread: 0.78, alpha: 0.3 },
  error: { core: [239, 68, 68], glow: [251, 113, 133], speed: 1.24, spread: 0.86, alpha: 0.66 },
  paused: { core: [100, 116, 139], glow: [71, 85, 105], speed: 0.2, spread: 0.78, alpha: 0.28 },
};

function rgba([red, green, blue]: [number, number, number], alpha: number) {
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

export function NexusParticleOrb({
  state,
  speakingLevel = 0,
  intensity = 1,
  size = 260,
}: NexusParticleOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const dimension = size;
    canvas.width = dimension * dpr;
    canvas.height = dimension * dpr;
    canvas.style.width = `${dimension}px`;
    canvas.style.height = `${dimension}px`;
    context.scale(dpr, dpr);

    const particleCount = reducedMotion ? 18 : 42;
    const particles = Array.from({ length: particleCount }, (_unused, index) => ({
      seed: index / particleCount,
      radius: 1.4 + ((index * 7) % 9) * 0.28,
      orbit: 0.26 + ((index * 11) % 16) * 0.022,
      wobble: 0.6 + ((index * 13) % 10) * 0.08,
      drift: ((index * 17) % 12) * 0.11,
    }));

    let frameId = 0;
    const render = (timestamp: number) => {
      const config = PARTICLE_CONFIG[state];
      const time = timestamp / 1000;
      const center = dimension / 2;
      const pulseBoost = state === "speaking" ? 0.08 + speakingLevel * 0.14 : state === "listening" ? 0.05 : state === "thinking" ? 0.03 : 0;
      const pulse = reducedMotion ? 0 : Math.sin(time * (config.speed * 4.8)) * pulseBoost;
      const coreRadius = dimension * (0.14 + pulse) * Math.max(0.82, intensity * 0.92);
      const orbitScale = dimension * 0.28 * config.spread * Math.max(0.86, intensity * 0.94);

      context.clearRect(0, 0, dimension, dimension);

      const outerGlow = context.createRadialGradient(center, center, coreRadius * 0.25, center, center, orbitScale * 1.4);
      outerGlow.addColorStop(0, rgba(config.glow, 0.18 + config.alpha * 0.16));
      outerGlow.addColorStop(1, rgba(config.glow, 0));
      context.fillStyle = outerGlow;
      context.beginPath();
      context.arc(center, center, orbitScale * 1.45, 0, Math.PI * 2);
      context.fill();

      const coreGlow = context.createRadialGradient(center, center, coreRadius * 0.18, center, center, coreRadius * 1.3);
      coreGlow.addColorStop(0, rgba(config.core, 0.92));
      coreGlow.addColorStop(0.55, rgba(config.glow, 0.34 + config.alpha * 0.14));
      coreGlow.addColorStop(1, rgba(config.glow, 0));
      context.fillStyle = coreGlow;
      context.beginPath();
      context.arc(center, center, coreRadius * 1.35, 0, Math.PI * 2);
      context.fill();

      particles.forEach((particle, index) => {
        const speed = config.speed * (0.72 + particle.seed * 0.65);
        const angle = time * speed + particle.seed * Math.PI * 2;
        const orbitRadius = orbitScale * particle.orbit + Math.sin(time * particle.wobble + particle.drift) * 10;
        const x = center + Math.cos(angle) * orbitRadius;
        const y = center + Math.sin(angle) * orbitRadius * (0.82 + particle.seed * 0.16);
        const localAlpha = Math.max(0.16, config.alpha - particle.seed * 0.16);

        if (!reducedMotion && index % 4 === 0) {
          context.strokeStyle = rgba(config.glow, localAlpha * 0.3);
          context.lineWidth = 0.7;
          context.beginPath();
          context.moveTo(center, center);
          context.lineTo(x, y);
          context.stroke();
        }

        context.fillStyle = rgba(config.glow, localAlpha);
        context.beginPath();
        context.arc(x, y, particle.radius + pulseBoost * 6, 0, Math.PI * 2);
        context.fill();
      });

      if (state === "error" && !reducedMotion) {
        const shake = Math.sin(time * 22) * 1.4;
        context.strokeStyle = rgba(config.core, 0.32);
        context.lineWidth = 2;
        context.beginPath();
        context.arc(center + shake, center, coreRadius * 1.08, 0, Math.PI * 2);
        context.stroke();
      }

      frameId = window.requestAnimationFrame(render);
    };

    frameId = window.requestAnimationFrame(render);
    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [intensity, reducedMotion, size, speakingLevel, state]);

  return (
    <div className="relative flex items-center justify-center">
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="rounded-full"
        aria-label={`Orb do Nexus em estado ${state}`}
      />
      <div className="pointer-events-none absolute inset-0 rounded-full border border-white/10 bg-white/[0.01]" />
    </div>
  );
}
