import React, { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchDemoDashboard, uploadCandidatesAndRank } from "../api";
import { DashboardData } from "../types";

const STEPS = [
  "Initializing Talent Market Feed...",
  "Scanning Inefficient Assets...",
  "Pricing Experience Signals...",
  "Detecting Value Discrepancies...",
  "Isolating High-Conviction Anomalies...",
  "Acquiring Hidden Gems..."
];

interface Props {
  file: File | null;
  setData: (data: DashboardData) => void;
  onComplete: () => void;
}

export default function ProcessingScreen({ file, setData, onComplete }: Props) {
  const [currentStep, setCurrentStep] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Accelerated Canvas Market
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: {x: number, y: number, speed: number, size: number, targetSize: number, opacity: number, targetOpacity: number, highlight: boolean}[] = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      
      particles = [];
      const numParticles = 400;
      for (let i = 0; i < numParticles; i++) {
        // One specific particle becomes the "highlight"
        const isHighlight = i === Math.floor(numParticles / 2);
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          speed: 1 + Math.random() * 3, // Faster speed
          size: Math.random() * 2 + 1,
          targetSize: isHighlight ? 8 : (Math.random() * 2 + 1),
          opacity: 0.1,
          targetOpacity: isHighlight ? 1 : Math.random() * 0.3,
          highlight: isHighlight
        });
      }
    };

    window.addEventListener('resize', resize);
    resize();

    const draw = () => {
      ctx.fillStyle = 'rgba(5, 5, 5, 0.2)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // We use currentStep to drive the progression
      // As steps progress, particles fade, highlight grows
      const progress = currentStep / (STEPS.length - 1);

      particles.forEach(p => {
        p.x -= p.speed * (1 + progress); // Speed up as it progresses
        if (p.x < -20) p.x = canvas.width + 20;

        // Animate size and opacity based on progress
        if (p.highlight) {
           p.targetSize = 4 + progress * 10;
           p.targetOpacity = 0.2 + progress * 0.8;
           // Move highlight towards center vertically
           p.y += (canvas.height/2 - p.y) * 0.05 * progress;
        } else {
           p.targetOpacity = Math.max(0, 0.3 - progress * 0.4); // Fade out normal particles
        }

        p.size += (p.targetSize - p.size) * 0.1;
        p.opacity += (p.targetOpacity - p.opacity) * 0.1;

        if (p.opacity <= 0) return;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        
        if (p.highlight) {
          ctx.fillStyle = `rgba(34, 211, 238, ${p.opacity})`;
          ctx.shadowBlur = 20 + progress * 30;
          ctx.shadowColor = 'rgba(34, 211, 238, 1)';
        } else {
          ctx.fillStyle = `rgba(255, 255, 255, ${p.opacity})`;
          ctx.shadowBlur = 0;
        }
        
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [currentStep]);

  useEffect(() => {
    // Determine pacing
    const totalTime = 6000;
    const intervalTime = totalTime / STEPS.length;
    
    const interval = setInterval(() => {
      setCurrentStep(curr => {
        if (curr < STEPS.length - 1) return curr + 1;
        clearInterval(interval);
        return curr;
      });
    }, intervalTime);
    
    const fetchData = async () => {
      try {
        let result: DashboardData;
        if (file) {
           result = await uploadCandidatesAndRank(file);
        } else {
           result = await fetchDemoDashboard();
        }
        setData(result);
        
        setTimeout(() => {
           onComplete();
        }, totalTime + 500); 

      } catch (e) {
        console.error(e);
      }
    };
    
    fetchData();

    return () => clearInterval(interval);
  }, [file, setData, onComplete]);

  return (
    <div className="fixed inset-0 bg-[#050505] flex flex-col items-center justify-center z-50 overflow-hidden font-sans">
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 z-0 pointer-events-none opacity-80"
      />
      <div className="absolute inset-0 pointer-events-none z-0 bg-[radial-gradient(circle_at_center,transparent_0%,#050505_100%)] opacity-80" />

      <AnimatePresence mode="wait">
        <motion.div
           key={currentStep}
           initial={{ opacity: 0, filter: "blur(10px)", y: 10 }}
           animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
           exit={{ opacity: 0, filter: "blur(10px)", y: -10 }}
           transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
           className="z-10 text-xl md:text-3xl text-white font-medium tracking-tight text-center px-6"
        >
          {STEPS[currentStep]}
        </motion.div>
      </AnimatePresence>

      <div className="absolute bottom-20 left-1/2 -translate-x-1/2 flex gap-3 z-10">
         {STEPS.map((_, i) => (
            <div 
              key={i} 
              className={`w-1 h-3 rounded-full transition-all duration-500 ${
                i === currentStep ? "bg-cyan-400 scale-y-150" : 
                i < currentStep ? "bg-white/40" : "bg-white/10"
              }`} 
            />
         ))}
      </div>
    </div>
  );
}
