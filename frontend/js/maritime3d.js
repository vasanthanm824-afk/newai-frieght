/**
 * SmartVesselAI — Slow, Majestic 3D Cinematic Maritime Background Engine
 * 
 * STRICT ANIMATION REQUIREMENTS:
 * 1. CRUISE SHIP (MOST IMPORTANT):
 *    - Visibly moves VERY SLOWLY and naturally through the ocean (like a real ship sailing).
 *    - Slow forward sailing motion.
 *    - Very subtle 3D rocking left and right (roll).
 *    - Gentle up/down movement following ocean wave swells (pitch & heave).
 *    - Realistic water splashes/foam at the bow stem.
 *    - Moving wake foam expanding behind the stern.
 *    - Subtle sunlight reflection glints sliding on the white ship hull.
 * 2. OCEAN WAVES:
 *    - Slow ocean waves moving towards camera with foam crests.
 * 3. FLYING SEAGULLS:
 *    - Multiple seagulls slowly flying across the sky with natural smooth wing flapping.
 * 4. DRIFTING CLOUDS:
 *    - Clouds moving very slowly horizontally.
 * 5. 3D PARALLAX & UI INTEGRITY:
 *    - Subtle 3D mouse depth parallax.
 *    - Entire SMARTVESSEL AI UI remains 100% fixed, crisp, and readable.
 *    - Starts automatically on page load and loops continuously.
 */

(function() {
  'use strict';

  function initEngine() {
    let canvas = document.getElementById('maritime-3d-bg-canvas');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'maritime-3d-bg-canvas';
      canvas.style.cssText = 'position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-2; pointer-events:none; background:transparent;';
      document.body.insertBefore(canvas, document.body.firstChild);
    }

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    let mouseX = 0, mouseY = 0;
    let targetMouseX = 0, targetMouseY = 0;

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    document.addEventListener('mousemove', (e) => {
      targetMouseX = (e.clientX - width / 2) * 0.035;
      targetMouseY = (e.clientY - height / 2) * 0.035;
    });

    // --- SLOW FLYING SEAGULLS ---
    const birds = [];
    for (let i = 0; i < 12; i++) {
      birds.push({
        x: Math.random() * width,
        y: 35 + Math.random() * (height * 0.32),
        scale: 0.55 + Math.random() * 0.75,
        speedX: 0.5 + Math.random() * 0.6, // Slow flight speed
        speedY: (Math.random() - 0.5) * 0.2,
        wingPhase: Math.random() * Math.PI * 2,
        wingSpeed: 0.08 + Math.random() * 0.05, // Smooth wing flap
        amplitude: 6 + Math.random() * 6
      });
    }

    // --- SLOW DRIFTING CLOUDS ---
    const clouds = [];
    for (let c = 0; c < 8; c++) {
      clouds.push({
        x: Math.random() * width,
        y: 25 + Math.random() * (height * 0.22),
        scale: 0.7 + Math.random() * 1.1,
        speed: 0.08 + Math.random() * 0.12 // Very slow cloud drift
      });
    }

    // --- BOW SPRAY WATER PARTICLES ---
    const sprayParticles = [];
    for (let p = 0; p < 50; p++) {
      sprayParticles.push({
        x: 0,
        y: 0,
        vx: (Math.random() - 0.5) * 2,
        vy: -1 - Math.random() * 2,
        radius: 1.2 + Math.random() * 2.5,
        alpha: 0.75,
        life: Math.random()
      });
    }

    let time = 0;

    // --- MAIN RENDER LOOP (60 FPS, SLOW & SMOOTH) ---
    function renderFrame() {
      time += 0.012; // Slow, relaxing time progression
      mouseX += (targetMouseX - mouseX) * 0.04;
      mouseY += (targetMouseY - mouseY) * 0.04;

      ctx.clearRect(0, 0, width, height);

      // 1. SUNSET LENS FLARE GLOW OVER PHOTOREALISTIC BACKGROUND
      const sunX = width * 0.28 + mouseX * 0.15;
      const sunY = height * 0.40 + mouseY * 0.15;
      const sunGlow = ctx.createRadialGradient(sunX, sunY, 8, sunX, sunY, 160);
      sunGlow.addColorStop(0, 'rgba(255, 183, 77, 0.25)');
      sunGlow.addColorStop(0.3, 'rgba(245, 158, 11, 0.08)');
      sunGlow.addColorStop(1, 'transparent');
      ctx.fillStyle = sunGlow;
      ctx.beginPath();
      ctx.arc(sunX, sunY, 160, 0, Math.PI * 2);
      ctx.fill();

      // 2. DRIFTING CLOUDS (VERY SLOW)
      clouds.forEach(cloud => {
        cloud.x += cloud.speed;
        if (cloud.x > width + 150) cloud.x = -150;

        const cx = cloud.x + mouseX * 0.08;
        const cy = cloud.y + mouseY * 0.08;

        ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.beginPath();
        ctx.arc(cx, cy, 32 * cloud.scale, 0, Math.PI * 2);
        ctx.arc(cx + 22 * cloud.scale, cy - 8 * cloud.scale, 26 * cloud.scale, 0, Math.PI * 2);
        ctx.arc(cx - 22 * cloud.scale, cy - 4 * cloud.scale, 22 * cloud.scale, 0, Math.PI * 2);
        ctx.arc(cx + 45 * cloud.scale, cy, 18 * cloud.scale, 0, Math.PI * 2);
        ctx.fill();
      });

      // 3. DYNAMIC TRANSLUCENT OCEAN WATER WAVE RIPPLES
      const horizonY = height * 0.44;

      // Rolling Ocean Wave Layers (Slow Movement)
      ctx.lineWidth = 1.5;
      for (let w = 0; w < 6; w++) {
        const waveY = horizonY + (w * (height - horizonY) / 6);
        const waveAmp = 5 + w * 2.5;
        const waveFreq = 0.007 - w * 0.0008;
        const waveSpeed = time * (0.8 + w * 0.25);

        ctx.strokeStyle = `rgba(56, 189, 248, ${0.1 + w * 0.035})`;
        ctx.fillStyle = `rgba(12, 30, 56, ${0.12 + w * 0.04})`;
        ctx.beginPath();
        ctx.moveTo(0, height);

        for (let x = 0; x <= width + 20; x += 15) {
          const y = waveY + Math.sin(x * waveFreq + waveSpeed) * waveAmp + Math.cos(x * 0.012 - waveSpeed * 0.4) * (waveAmp * 0.4);
          ctx.lineTo(x, y);
        }
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }

      // 4. SEPARATE CRUISE SHIP ANIMATION ENGINE & OCEAN WAKE / BOW SPRAY
      const shipCenterX = width * 0.48 + Math.sin(time * 0.35) * 55 + mouseX * 0.25;
      const shipCenterY = horizonY + 28 + Math.sin(time * 0.75) * 6.5 + mouseY * 0.15;
      const shipRoll = Math.sin(time * 0.55) * 2.0; // 3D roll rocking

      // A. EXPANDING WHITE V-WAKE FOAM TRAIL (ON OCEAN CANVAS BEHIND SHIP)
      ctx.save();
      ctx.translate(shipCenterX, shipCenterY);
      ctx.rotate(shipRoll * Math.PI / 180);

      const wakeGrad = ctx.createLinearGradient(0, 35, 0, 180);
      wakeGrad.addColorStop(0, 'rgba(224, 242, 254, 0.65)');
      wakeGrad.addColorStop(0.4, 'rgba(186, 230, 253, 0.35)');
      wakeGrad.addColorStop(1, 'transparent');
      
      ctx.fillStyle = wakeGrad;
      ctx.beginPath();
      ctx.moveTo(-15, 18);
      ctx.lineTo(-110, 170 + Math.sin(time * 1.5) * 10);
      ctx.lineTo(110, 170 + Math.sin(time * 1.5) * 10);
      ctx.lineTo(15, 18);
      ctx.closePath();
      ctx.fill();

      // B. WATER BOW SPRAY PARTICLES (GENTLE WAVE SPLASH AT BOW)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
      sprayParticles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.08; // Gravity

        if (p.y > 18 || p.x > 85 || p.x < -40) {
          p.x = 160 + (Math.random() - 0.5) * 10;
          p.y = -6 + Math.random() * 5;
          p.vx = 1.2 + Math.random() * 2.0;
          p.vy = -1.2 - Math.random() * 2.0;
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();

      // C. DRIVE INDEPENDENT DOM SEPARATE SHIP LAYER POSITION (#vessel-ship-layer)
      const shipLayer = document.getElementById('vessel-ship-layer');
      if (shipLayer) {
        const approachProgress = (Math.sin(time * 0.12) + 1) * 0.5;
        const depthScale = (0.95 + approachProgress * 0.11).toFixed(3);
        const translateY = ((approachProgress * 14) + Math.sin(time * 0.75) * 3.5 + mouseY * 0.04).toFixed(2);

        const newTransform = `translate(-50%, -50%) translate3d(0px, ${translateY}px, 0px) scale(${depthScale})`;
        if (shipLayer.dataset.lastTransform !== newTransform) {
          shipLayer.style.transform = newTransform;
          shipLayer.dataset.lastTransform = newTransform;
        }
      }

      // 5. ARTICULATED FLYING SEAGULLS (SLOW & NATURAL FLIGHT)
      birds.forEach(bird => {
        bird.x += bird.speedX;
        bird.y += Math.sin(time * 1.2 + bird.wingPhase) * 0.4 + bird.speedY;

        if (bird.x > width + 50) {
          bird.x = -50;
          bird.y = 35 + Math.random() * (height * 0.32);
        }

        const flap = Math.sin(time * 6 * bird.wingSpeed + bird.wingPhase) * bird.amplitude;
        const bx = bird.x + mouseX * 0.12;
        const by = bird.y + mouseY * 0.12;

        ctx.save();
        ctx.translate(bx, by);
        ctx.scale(bird.scale, bird.scale);

        // Bird Body & Beak
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.ellipse(0, 0, 7, 2.8, 0.08, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.moveTo(6, -1);
        ctx.lineTo(10, 0);
        ctx.lineTo(6, 1.8);
        ctx.closePath();
        ctx.fill();

        // Flapping Wings
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.2;
        ctx.lineCap = 'round';

        // Left Wing
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(-5, -10 + flap, -14, -3 + flap * 0.5);
        ctx.stroke();

        // Right Wing
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(3, -10 + flap, 12, -3 + flap * 0.5);
        ctx.stroke();

        ctx.restore();
      });

      requestAnimationFrame(renderFrame);
    }

    renderFrame();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEngine);
  } else {
    initEngine();
  }

})();
