import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Candidate } from '../../types';
import { formatInt } from '../../lib/utils';

export default function RevealSection({ hero }: { hero?: Candidate }) {
  const [phase, setPhase] = useState<'scan' | 'isolate' | 'reveal'>('scan');

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const t1 = setTimeout(() => setPhase('isolate'), 2000);
    const t2 = setTimeout(() => {
      setPhase('reveal');
      document.body.style.overflow = '';
    }, 4500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      document.body.style.overflow = '';
    };
  }, []);

  if (!hero) return null;
  const improvement = hero.ats_rank - hero.our_rank;

  return (
    <section className="relative min-h-screen flex items-center justify-center py-24 px-6 overflow-hidden bg-[#050505]">
      {/* Cinematic Intro Overlay */}
      <AnimatePresence>
        {phase !== 'reveal' && (
          <motion.div 
            key="overlay"
            exit={{ opacity: 0, scale: 1.1, filter: "blur(20px)" }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            className="absolute inset-0 z-50 bg-[#050505] flex items-center justify-center flex-col"
          >
            {/* Geometric Scanner */}
            <motion.div 
              className="relative w-64 h-64 flex items-center justify-center"
            >
              {/* Outer faint ring */}
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 10, ease: "linear", repeat: Infinity }}
                className="absolute inset-0 rounded-full border border-white/5 border-t-white/20"
              />
              
              {/* Mid ring */}
              <motion.div 
                animate={{ rotate: -360, scale: phase === 'isolate' ? [1, 0.8, 1.1, 0.9, 1] : 1 }}
                transition={{ duration: phase === 'isolate' ? 2 : 15, ease: "easeInOut", repeat: phase === 'isolate' ? 0 : Infinity }}
                className={`absolute inset-8 rounded-full border ${phase === 'isolate' ? 'border-cyan-500/50' : 'border-white/10'} border-b-transparent`}
              />

              {/* Inner core */}
              {phase === 'isolate' ? (
                <motion.div 
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: [0, 1.5, 1], opacity: [0, 1, 1] }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                  className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_30px_10px_rgba(34,211,238,0.6)]"
                />
              ) : (
                <div className="w-1 h-1 rounded-full bg-white/30" />
              )}

              {/* Targeting Lines (Crosshair) */}
              <motion.div 
                animate={{ opacity: phase === 'isolate' ? 1 : 0.2 }}
                className="absolute inset-0 pointer-events-none"
              >
                <div className="absolute top-1/2 left-0 right-0 h-px bg-white/5 -translate-y-1/2" />
                <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/5 -translate-x-1/2" />
              </motion.div>
            </motion.div>

            <div className="mt-16 h-12 flex items-center justify-center">
              <AnimatePresence mode="wait">
                {phase === 'scan' && (
                  <motion.div 
                    key="scan-text"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex flex-col items-center gap-2"
                  >
                    <div className="text-slate-500 font-mono text-[10px] tracking-[0.3em] uppercase">
                      Compiling Market Baseline
                    </div>
                    <div className="w-32 h-px bg-gradient-to-r from-transparent via-slate-500/50 to-transparent relative overflow-hidden">
                      <motion.div 
                        initial={{ x: "-100%" }}
                        animate={{ x: "100%" }}
                        transition={{ duration: 1.5, ease: "linear", repeat: Infinity }}
                        className="absolute inset-0 bg-white/50"
                      />
                    </div>
                  </motion.div>
                )}
                {phase === 'isolate' && (
                  <motion.div 
                    key="isolate-text"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, filter: "blur(5px)" }}
                    className="flex flex-col items-center gap-3"
                  >
                    <div className="text-cyan-400 font-mono text-xs tracking-[0.2em] uppercase drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]">
                      Extreme Discrepancy Found
                    </div>
                    <div className="text-white/50 font-mono text-[10px] tracking-widest uppercase">
                      Asset {hero.candidate_id.split('_').pop()} Isolated
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content Reveal */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#0A0F15] via-[#050505] to-[#050505] pointer-events-none" />
      
      <div className="z-10 w-full max-w-5xl flex flex-col items-center">
        <motion.div
           initial={{ opacity: 0, y: 40 }}
           animate={{ opacity: phase === 'reveal' ? 1 : 0, y: phase === 'reveal' ? 0 : 40 }}
           transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: phase === 'reveal' ? 0.2 : 0 }}
           className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-6xl font-medium tracking-tighter text-white mb-6">
            The Market Missed <span className="text-cyan-400">This Asset</span>.
          </h2>
          <p className="text-xl md:text-2xl text-slate-400 font-light tracking-wide max-w-2xl mx-auto">
            A stark example of market inefficiency. Keywords hide true potential.
          </p>
        </motion.div>

        <motion.div 
           initial={{ opacity: 0, scale: 0.9, y: 50 }}
           animate={{ opacity: phase === 'reveal' ? 1 : 0, scale: phase === 'reveal' ? 1 : 0.9, y: phase === 'reveal' ? 0 : 50 }}
           transition={{ duration: 1.5, ease: [0.16, 1, 0.3, 1], delay: phase === 'reveal' ? 0.4 : 0 }}
           className="w-full relative group"
        >
          {/* Abstract minimal glow */}
          <div className="absolute -inset-0.5 bg-gradient-to-br from-cyan-500/20 to-transparent rounded-[2rem] opacity-0 group-hover:opacity-100 transition-opacity duration-1000 blur-xl pointer-events-none" />
          
          <div className="relative bg-[#070709]/80 backdrop-blur-2xl border border-white/10 rounded-[2rem] p-8 md:p-16 flex flex-col md:flex-row gap-12 md:gap-24 overflow-hidden shadow-2xl">
            
            {/* Abstract Avatar Placeholder */}
            <div className="hidden md:flex relative shrink-0 items-center justify-center w-56 h-56 rounded-full border border-cyan-500/20 bg-cyan-950/10">
               <motion.div 
                 initial={{ rotate: 0 }}
                 animate={{ rotate: 360 }}
                 transition={{ duration: 30, ease: "linear", repeat: Infinity }}
                 className="absolute inset-0 rounded-full border border-cyan-400/20" 
                 style={{ borderTopColor: 'rgba(34, 211, 238, 0.8)' }} 
               />
               <motion.div 
                 initial={{ rotate: 360 }}
                 animate={{ rotate: 0 }}
                 transition={{ duration: 25, ease: "linear", repeat: Infinity }}
                 className="absolute inset-2 rounded-full border border-cyan-400/10" 
                 style={{ borderBottomColor: 'rgba(34, 211, 238, 0.6)' }} 
               />
               <div className="text-5xl font-light text-cyan-400 tracking-tighter text-center">
                 {hero.candidate_id.split('_').pop()}
               </div>
            </div>

            <div className="flex-1 flex flex-col justify-center text-center md:text-left">
               <div className="uppercase tracking-widest text-xs font-semibold text-cyan-400/70 mb-3 block">Highest Conviction Outlier</div>
               <h3 className="text-4xl md:text-5xl font-medium text-white tracking-tight mb-2">Candidate {hero.candidate_id.split('_').pop()}</h3>
               <p className="text-xl text-slate-400 font-light mb-12">{hero.title}</p>

               <div className="grid grid-cols-2 gap-8 w-full border-t border-white/5 pt-8">
                 <div className="relative overflow-hidden">
                   <div className="text-xs uppercase tracking-widest text-slate-600 font-semibold mb-3 block">ATS Market Rank</div>
                   <motion.div 
                     initial={{ opacity: 0, x: -20 }}
                     animate={{ opacity: phase === 'reveal' ? 1 : 0, x: phase === 'reveal' ? 0 : -20 }}
                     transition={{ duration: 0.8, delay: phase === 'reveal' ? 1.0 : 0 }}
                     className="text-4xl md:text-5xl text-slate-500 font-light strike tracking-tighter line-through decoration-rose-500/50"
                   >
                     #{hero.ats_rank}
                   </motion.div>
                 </div>
                 <div className="relative overflow-hidden">
                   <div className="text-xs uppercase tracking-widest text-cyan-400 font-semibold mb-3 block">Discovery Rank</div>
                   <motion.div 
                     initial={{ opacity: 0, x: -20 }}
                     animate={{ opacity: phase === 'reveal' ? 1 : 0, x: phase === 'reveal' ? 0 : -20 }}
                     transition={{ duration: 0.8, delay: phase === 'reveal' ? 1.4 : 0 }}
                     className="text-5xl md:text-6xl text-white font-medium tracking-tighter drop-shadow-[0_0_15px_rgba(34,211,238,0.3)]"
                   >
                     #{hero.our_rank}
                   </motion.div>
                 </div>
               </div>

               <motion.div 
                 initial={{ opacity: 0, y: 20 }}
                 animate={{ opacity: phase === 'reveal' ? 1 : 0, y: phase === 'reveal' ? 0 : 20 }}
                 transition={{ duration: 1, delay: phase === 'reveal' ? 2 : 0 }}
                 className="mt-12 flex flex-col md:flex-row md:items-center gap-6"
               >
                 <div className="px-6 py-2.5 bg-cyan-400/10 text-cyan-400 text-sm font-semibold rounded-full inline-flex md:mr-auto justify-center border border-cyan-400/20 shadow-[0_0_20px_rgba(34,211,238,0.1)]">
                   +{improvement} Position Gain
                 </div>
                 <div className="text-sm font-light text-slate-400 max-w-xs text-left leading-relaxed">
                    Talent Mispricing Index of <span className="text-white font-medium">{formatInt(hero.tmi)}</span> — the positions the ATS buried this candidate by.
                 </div>
               </motion.div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
