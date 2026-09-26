import React, { useEffect, useRef } from 'react';

/**
 * Ambient Particles Component from React Bits
 * High-performance lightweight 2D canvas particle effect for the Landing screen.
 */
export default function Particles({
  particleCount = 45,
  particleSpread = 10,
  speed = 0.3,
  particleColors = ['#B23A2E', '#D9A441', '#EDE6D6'],
  moveParticlesOnHover = true,
  particleHoverFactor = 1.5,
  alpha = 0.4,
  particleBaseSize = 1.5,
  sizeRandomness = 1,
  className = '',
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = canvas.parentElement?.offsetWidth || window.innerWidth || 800);
    let height = (canvas.height = canvas.parentElement?.offsetHeight || window.innerHeight || 600);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.parentElement?.offsetWidth || window.innerWidth || 800;
      height = canvas.height = canvas.parentElement?.offsetHeight || window.innerHeight || 600;
    };

    window.addEventListener('resize', handleResize);

    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * speed,
        vy: (Math.random() - 0.5) * speed,
        size: particleBaseSize + Math.random() * sizeRandomness,
        color: particleColors[Math.floor(Math.random() * particleColors.length)],
        opacity: Math.random() * alpha + 0.1,
      });
    }

    let mouse = { x: -1000, y: -1000 };
    const handleMouseMove = (e) => {
      if (!moveParticlesOnHover) return;
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    window.addEventListener('mousemove', handleMouseMove);

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Mouse hover interaction
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 100) {
          p.x -= (dx / dist) * particleHoverFactor;
          p.y -= (dy / dist) * particleHoverFactor;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.opacity;
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, [particleCount, speed, particleColors, moveParticlesOnHover, particleHoverFactor, alpha, particleBaseSize, sizeRandomness]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none ${className}`}
      style={{ width: '100%', height: '100%' }}
    />
  );
}
