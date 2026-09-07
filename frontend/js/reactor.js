/**
 * J.A.R.V.I.S. Holographic Arc Reactor Visualizer
 * HTML5 Canvas 2D dynamic animation engine.
 */

class ArcReactor {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.centerX = this.width / 2;
    this.centerY = this.height / 2;

    // Animation state
    this.angleOuter = 0;
    this.angleMiddle = 0;
    this.angleInner = 0;
    this.state = 'idle'; // 'idle', 'listening', 'thinking', 'speaking'
    this.audioLevel = 0.0; // 0.0 to 1.0
    this.pulseFactor = 0;
    this.particles = [];

    this._initParticles();
    this.render = this.render.bind(this);
    requestAnimationFrame(this.render);
  }

  _initParticles() {
    this.particles = [];
    for (let i = 0; i < 24; i++) {
      this.particles.push({
        angle: (i / 24) * Math.PI * 2,
        dist: 45 + Math.random() * 30,
        speed: 0.3 + Math.random() * 0.5,
        size: 1.5 + Math.random() * 2,
        alpha: 0.3 + Math.random() * 0.7
      });
    }
  }

  setState(state) {
    this.state = state;
    const phaseText = document.getElementById('statusPhaseText');
    const subText = document.getElementById('statusSubText');
    
    if (state === 'listening') {
      if (phaseText) {
        phaseText.textContent = 'LISTENING...';
        phaseText.style.color = 'var(--cyan-primary)';
      }
      if (subText) subText.textContent = 'VOICE INPUT DETECTED';
    } else if (state === 'thinking') {
      if (phaseText) {
        phaseText.textContent = 'ANALYZING...';
        phaseText.style.color = 'var(--gold-alert)';
      }
      if (subText) subText.textContent = 'NEURAL ENGINE PROCESSING';
    } else if (state === 'speaking') {
      if (phaseText) {
        phaseText.textContent = 'TRANSMITTING';
        phaseText.style.color = 'var(--cyan-primary)';
      }
      if (subText) subText.textContent = 'AUDIO SYNTHESIS ACTIVE';
    } else {
      if (phaseText) {
        phaseText.textContent = 'SYSTEM READY';
        phaseText.style.color = 'var(--cyan-primary)';
      }
      if (subText) subText.textContent = 'STANDBY FOR DIRECTIVE';
    }
  }

  setAudioLevel(level) {
    this.audioLevel = Math.max(0, Math.min(1, level));
  }

  render(time) {
    this.ctx.clearRect(0, 0, this.width, this.height);

    // Dynamic rotation speeds & colors based on state
    let speedMult = 1.0;
    let primaryColor = '#00f0ff';
    let secondaryColor = '#0077ff';
    let glowColor = 'rgba(0, 240, 255, 0.4)';

    if (this.state === 'listening') {
      speedMult = 2.2;
      primaryColor = '#00f0ff';
      glowColor = 'rgba(0, 240, 255, 0.7)';
    } else if (this.state === 'thinking') {
      speedMult = 3.5;
      primaryColor = '#ffb703';
      secondaryColor = '#ff8800';
      glowColor = 'rgba(255, 183, 3, 0.6)';
    } else if (this.state === 'speaking') {
      speedMult = 1.6;
      primaryColor = '#38bdf8';
      glowColor = 'rgba(56, 189, 248, 0.6)';
    }

    this.angleOuter += 0.008 * speedMult;
    this.angleMiddle -= 0.012 * speedMult;
    this.angleInner += 0.018 * speedMult;

    this.pulseFactor = Math.sin(time * 0.003) * 0.5 + 0.5;
    const reactiveBoost = this.audioLevel * 15;

    this.ctx.save();
    this.ctx.translate(this.centerX, this.centerY);

    // 1. Draw outermost tick ring
    this._drawOuterRing(145 + reactiveBoost * 0.5, primaryColor, glowColor);

    // 2. Draw middle notched segmented ring
    this._drawMiddleRing(105, secondaryColor, glowColor);

    // 3. Draw inner reactor capacitor ring
    this._drawInnerCapacitors(75, primaryColor, glowColor);

    // 4. Draw central pulsing glowing core
    this._drawCore(35 + reactiveBoost, primaryColor, secondaryColor, glowColor);

    // 5. Draw orbiting particle energy sparks
    this._drawParticles(primaryColor);

    this.ctx.restore();
    requestAnimationFrame(this.render);
  }

  _drawOuterRing(radius, color, glow) {
    const ctx = this.ctx;
    ctx.save();
    ctx.rotate(this.angleOuter);
    ctx.shadowBlur = 10;
    ctx.shadowColor = glow;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    // 4 segmented arcs
    const segments = 4;
    const arcLen = (Math.PI * 2) / segments;
    const gap = 0.25;

    for (let i = 0; i < segments; i++) {
      ctx.beginPath();
      ctx.arc(0, 0, radius, i * arcLen + gap, (i + 1) * arcLen - gap);
      ctx.stroke();
    }

    // Outer ticks
    const tickCount = 48;
    for (let i = 0; i < tickCount; i++) {
      const a = (i / tickCount) * Math.PI * 2;
      const isMajor = i % 4 === 0;
      const len = isMajor ? 8 : 4;
      ctx.lineWidth = isMajor ? 2 : 1;
      ctx.beginPath();
      ctx.moveTo(Math.cos(a) * (radius - len), Math.sin(a) * (radius - len));
      ctx.lineTo(Math.cos(a) * (radius + len), Math.sin(a) * (radius + len));
      ctx.stroke();
    }
    ctx.restore();
  }

  _drawMiddleRing(radius, color, glow) {
    const ctx = this.ctx;
    ctx.save();
    ctx.rotate(this.angleMiddle);
    ctx.shadowBlur = 8;
    ctx.shadowColor = glow;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;

    // Tech triangular notches
    const notches = 12;
    for (let i = 0; i < notches; i++) {
      const a = (i / notches) * Math.PI * 2;
      ctx.beginPath();
      ctx.arc(0, 0, radius, a - 0.12, a + 0.12);
      ctx.stroke();

      // Mini triangle notch
      const tipX = Math.cos(a) * (radius - 8);
      const tipY = Math.sin(a) * (radius - 8);
      const b1X = Math.cos(a - 0.06) * radius;
      const b1Y = Math.sin(a - 0.06) * radius;
      const b2X = Math.cos(a + 0.06) * radius;
      const b2Y = Math.sin(a + 0.06) * radius;

      ctx.beginPath();
      ctx.moveTo(tipX, tipY);
      ctx.lineTo(b1X, b1Y);
      ctx.lineTo(b2X, b2Y);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
    }
    ctx.restore();
  }

  _drawInnerCapacitors(radius, color, glow) {
    const ctx = this.ctx;
    ctx.save();
    ctx.rotate(this.angleInner);
    ctx.shadowBlur = 12;
    ctx.shadowColor = glow;

    const blocks = 10;
    for (let i = 0; i < blocks; i++) {
      const a = (i / blocks) * Math.PI * 2;
      ctx.save();
      ctx.rotate(a);
      ctx.fillStyle = color;
      ctx.fillRect(radius - 8, -6, 16, 12);
      ctx.restore();
    }
    ctx.restore();
  }

  _drawCore(radius, primary, secondary, glow) {
    const ctx = this.ctx;
    ctx.save();
    ctx.shadowBlur = 25;
    ctx.shadowColor = glow;

    // Radial gradient core
    const grad = ctx.createRadialGradient(0, 0, 4, 0, 0, radius + 10);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.3, primary);
    grad.addColorStop(0.7, secondary);
    grad.addColorStop(1, 'rgba(0,0,0,0)');

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Central geometric aperture
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, radius * 0.45, 0, Math.PI * 2);
    ctx.stroke();

    ctx.restore();
  }

  _drawParticles(color) {
    const ctx = this.ctx;
    ctx.save();
    ctx.fillStyle = color;
    for (const p of this.particles) {
      p.angle += 0.01 * p.speed;
      const x = Math.cos(p.angle) * p.dist;
      const y = Math.sin(p.angle) * p.dist;
      ctx.globalAlpha = p.alpha;
      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }
}
