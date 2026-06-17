import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, ScanLine } from "lucide-react";
import { cn } from "../lib/utils";

interface Props {
  onDemo: () => void;
  onUpload: (file: File) => void;
}

export default function LandingScreen({ onDemo, onUpload }: Props) {
  const [dragActive, setDragActive] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Canvas living market effect
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: {x: number, y: number, baseY: number, speed: number, size: number, opacity: number, id: number}[] = [];
    let highlightEvent: { id: number, start: number, duration: number, yOffset: number } | null = null;
    let lastTime = performance.now();

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      
      particles = [];
      const numParticles = window.innerWidth < 768 ? 60 : 150;
      for (let i = 0; i < numParticles; i++) {
        particles.push({
          id: i,
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          baseY: Math.random() * canvas.height,
          speed: 0.1 + Math.random() * 0.4,
          size: Math.random() * 1.5 + 0.5,
          opacity: Math.random() * 0.4 + 0.1,
        });
      }
    };

    window.addEventListener('resize', resize);
    resize();

    const draw = (time: number) => {
      const delta = time - lastTime;
      lastTime = time;

      ctx.clearRect(0, 0, canvas.width, canvas.height); // Use clearRect for better transparency blending

      // Draw shifting valuation bands (subtle horizontal noise/lines)
      for (let i = 0; i < 5; i++) {
        const bandY = (canvas.height / 6) * (i + 1) + Math.sin(time / 2000 + i) * 30;
        ctx.beginPath();
        ctx.moveTo(0, bandY);
        ctx.bezierCurveTo(canvas.width / 3, bandY + 50, (canvas.width / 3) * 2, bandY - 50, canvas.width, bandY);
        ctx.strokeStyle = `rgba(255, 255, 255, 0.02)`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // Handle random signature Highlight event every 6-8 seconds
      if (!highlightEvent && Math.random() < 0.002) { // roughly every few seconds
        const randomP = particles[Math.floor(Math.random() * particles.length)];
        highlightEvent = { id: randomP.id, start: time, duration: 4000, yOffset: 0 };
      }

      const isInteracting = dragActive || isHovered;
      const centerX = canvas.width / 2;
      const centerY = canvas.height * 0.6; // roughly where the upload box is

      particles.forEach(p => {
        // Move horizontally
        p.x -= p.speed;
        if (p.x < -10) {
          p.x = canvas.width + 10;
          p.baseY = Math.random() * canvas.height;
        }

        let currentY = p.baseY;
        let pOpacity = p.opacity;
        let pSize = p.size;
        let isHighlighted = false;

        // Apply highlight event
        if (highlightEvent && highlightEvent.id === p.id) {
          const progress = (time - highlightEvent.start) / highlightEvent.duration;
          if (progress >= 1) {
            highlightEvent = null;
          } else {
            isHighlighted = true;
            // Ease in out
            const ease = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
            
            // Rise up
            currentY = p.baseY - (ease * 60);
            
            // Pulse glow
            const glowPhase = Math.sin(progress * Math.PI);
            pOpacity = Math.min(1, p.opacity + (glowPhase * 0.8));
            pSize = p.size + (glowPhase * 2);
          }
        } else if (highlightEvent) {
          // Dim others to create focus
          const progress = (time - highlightEvent.start) / highlightEvent.duration;
          const dimPhase = Math.sin(progress * Math.PI);
          pOpacity = Math.max(0.02, p.opacity - (dimPhase * 0.3));
        }

        // Convergence interaction
        if (isInteracting && !isHighlighted) {
           const dx = centerX - p.x;
           const dy = centerY - p.baseY; // Use baseY to steer
           const dist = Math.sqrt(dx * dx + dy * dy);
           const pull = Math.min(1, 500 / Math.max(50, dist)) * 0.05; // pull factor
           
           p.baseY += dy * pull; // Pull towards center y
           p.speed = Math.min(2, p.speed + 0.05); // Speed up slightly towards center area
           
           // Slight cyan tint for drawn points
           pOpacity = Math.min(0.8, pOpacity + 0.2);
        } else if (!isInteracting && p.speed > 0.5) {
           p.speed -= 0.01; // slow down to normal
        }

        // Draw particle
        ctx.beginPath();
        ctx.arc(p.x, currentY, pSize, 0, Math.PI * 2);
        
        if (isHighlighted) {
          ctx.fillStyle = `rgba(34, 211, 238, ${pOpacity})`;
          ctx.shadowBlur = 15;
          ctx.shadowColor = 'rgba(34, 211, 238, 0.8)';
          
          // Draw subtle vertical line for highlight
          ctx.moveTo(p.x, currentY);
          ctx.lineTo(p.x, currentY + 100);
          ctx.strokeStyle = `rgba(34, 211, 238, ${Math.max(0, pOpacity - 0.5)})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        } else if (isInteracting) {
          ctx.fillStyle = `rgba(34, 211, 238, ${pOpacity * 0.5})`;
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = `rgba(255, 255, 255, ${pOpacity})`;
          ctx.shadowBlur = 0;
        }
        
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    animationFrameId = requestAnimationFrame(draw);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [dragActive, isHovered]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const f = e.dataTransfer.files[0];
      if (f.name.endsWith('.zip') || f.name.endsWith('.jsonl') || f.name.endsWith('.jsonl.gz') || f.name.endsWith('.gz')) {
         onUpload(f);
      } else {
         alert("Please upload a .zip, .jsonl or .jsonl.gz file");
      }
    }
  };

  return (
    <div className="relative min-h-screen bg-[#020202] flex flex-col pt-32 pb-24 items-center justify-start overflow-y-auto font-sans selection:bg-white/30">
      
      {/* Cinematic animated background */}
      <canvas 
        ref={canvasRef} 
        className="fixed inset-0 z-0 pointer-events-none opacity-80"
      />
      
      {/* Directional Lighting Gradients */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_120%_100%_at_50%_-10%,_rgba(34,211,238,0.06)_0%,_transparent_60%)]" />
      <div className="fixed bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-[#020202] via-[#020202]/80 to-transparent pointer-events-none z-0" />

      <div className="z-10 w-full max-w-6xl px-6 flex flex-col items-center text-center mt-12 md:mt-24">
        
        <motion.div
           initial={{ opacity: 0, y: 10 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-10 rounded-full bg-[#0A1015] border border-white/5 shadow-[0_0_20px_rgba(34,211,238,0.05)] text-[10px] font-semibold tracking-widest uppercase text-slate-400 backdrop-blur-md">
            Talent Market Intelligence
          </div>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          className="text-5xl md:text-8xl font-medium tracking-tighter text-white mb-8 leading-[1.1]"
        >
          57% of Top Talent <br />
          <span className="text-slate-600">Is Mispriced.</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          className="text-xl md:text-2xl text-slate-400 max-w-3xl font-light tracking-wide mb-16"
        >
          Traditional ATS systems reward visibility. <br className="hidden md:block" />
          <span className="text-slate-200">Discovery finds value where everyone else looks away.</span>
        </motion.p>


        <motion.div 
           initial={{ opacity: 0, scale: 0.95, y: 30 }}
           animate={{ opacity: 1, scale: 1, y: 0 }}
           transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1], delay: 0.4 }}
           className="w-full max-w-2xl relative group"
           onMouseEnter={() => setIsHovered(true)}
           onMouseLeave={() => setIsHovered(false)}
        >
          {/* Abstract deep glow anchoring the upload area */}
          <div className={cn(
             "absolute -inset-8 bg-cyan-500/10 rounded-full blur-3xl transition-opacity duration-1000 pointer-events-none",
             isHovered || dragActive ? "opacity-100" : "opacity-0"
          )} />

          {/* Upload Area */}
          <div 
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={cn(
              "relative rounded-[2.5rem] border flex flex-col md:flex-row items-center justify-between p-3 pl-8 transition-all duration-700 backdrop-blur-2xl shadow-2xl overflow-hidden",
              dragActive 
                ? "border-cyan-500/50 bg-[#0A1520]/80 scale-[1.02]" 
                : "border-white/10 bg-[#070709]/80 hover:bg-[#0A0D12]/90 hover:border-white/20 hover:scale-[1.01]"
            )}
          >
            {/* Inner hover gradient */}
            <div className={`absolute inset-0 bg-gradient-to-r ${dragActive || isHovered ? 'from-cyan-500/10' : 'from-transparent'} to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none`} />

            <div className="flex-1 text-center md:text-left mb-4 md:mb-0">
              <p className={cn("text-lg font-medium transition-colors duration-500", dragActive ? "text-cyan-400" : "text-white")}>
                 {dragActive ? "Release to Analyze Market" : "Activate Discovery Engine"}
              </p>
              <p className="text-sm text-slate-500 font-light mt-1">Upload candidate ZIP to reveal hidden density.</p>
            </div>
            
            <label className={cn(
              "relative z-10 flex items-center gap-3 px-8 py-5 rounded-full cursor-pointer transition-all duration-500 font-medium text-sm overflow-hidden",
              dragActive ? "bg-cyan-400 text-black shadow-[0_0_20px_rgba(34,211,238,0.4)]" : (isHovered ? "bg-cyan-50 text-black shadow-[0_0_15px_rgba(255,255,255,0.2)]" : "bg-white text-black hover:bg-slate-200")
            )}>
               <ScanLine className="w-5 h-5 flex-shrink-0" />
               <span className="whitespace-nowrap">Select File</span>
               <input 
                 type="file"
                 className="hidden"
                 accept=".zip,.jsonl,.jsonl.gz,.gz"
                 onChange={(e) => {
                   if (e.target.files?.[0]) onUpload(e.target.files[0]);
                 }} 
               />
               
               {/* Shine effect inside button */}
               <div className="absolute inset-0 -translate-x-[150%] animate-[shimmer_3s_infinite] bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12 pointer-events-none" />
            </label>
          </div>
        </motion.div>

        {/* Demo Button */}
        <motion.div
           initial={{ opacity: 0 }}
           animate={{ opacity: 1 }}
           transition={{ duration: 1, delay: 0.8 }}
           className="mt-8"
        >
          <button 
            onClick={onDemo}
            className="flex items-center gap-3 text-sm font-medium tracking-wide text-slate-500 hover:text-white transition-colors duration-300"
          >
            <span>Or run market simulation</span>
            <div className="w-6 h-6 rounded-full border border-white/10 flex items-center justify-center bg-white/5">
              <Play className="w-2.5 h-2.5 ml-0.5" />
            </div>
          </button>
        </motion.div>

        {/* Premium Proof Strip */}
        <motion.div
           initial={{ opacity: 0, y: 30 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 1 }}
           className="mt-32 w-full border-t border-white/5 pt-12"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4 max-w-5xl mx-auto">
            <div className="flex flex-col items-center md:items-start text-center md:text-left">
              <span className="text-3xl lg:text-4xl font-medium text-white tracking-tighter mb-1">100,000+</span>
              <span className="text-[10px] tracking-widest uppercase text-slate-500 font-semibold">Candidates Analyzed</span>
            </div>
            <div className="flex flex-col items-center md:items-start text-center md:text-left">
              <span className="text-3xl lg:text-4xl font-medium text-white tracking-tighter mb-1">57</span>
              <span className="text-[10px] tracking-widest uppercase text-cyan-400/80 font-semibold">Hidden Gems Found</span>
            </div>
            <div className="flex flex-col items-center md:items-start text-center md:text-left">
              <span className="text-3xl lg:text-4xl font-medium text-slate-400 strike line-through decoration-slate-600 mb-1">#1788</span>
              <span className="text-[10px] tracking-widest uppercase text-slate-500 font-semibold">ATS Missed Rank</span>
            </div>
            <div className="flex flex-col items-center md:items-start text-center md:text-left">
              <span className="text-3xl lg:text-4xl font-medium text-white tracking-tighter mb-1">43%</span>
              <span className="text-[10px] tracking-widest uppercase text-slate-500 font-semibold">Market Inefficiency</span>
            </div>
          </div>
        </motion.div>

      </div>
    </div>
  );
}


