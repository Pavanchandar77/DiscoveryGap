import React from 'react';
import { motion } from 'framer-motion';
import { DashboardData } from '../../types';
import { formatTmi } from '../../lib/utils';

export default function HiddenGemsSection({ data }: { data: DashboardData }) {
  const gems = [...data.cards]
    .sort((a, b) => b.tmi - a.tmi)
    .slice(0, 4);

  return (
    <section className="min-h-screen py-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col justify-center">
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true, margin: "-100px" }}
         className="mb-16"
      >
        <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
          High Conviction Value
        </h2>
        <p className="text-xl text-slate-400 font-light max-w-2xl leading-relaxed">
          Assets that hold extraordinary evidence density but are completely mispriced by standard models.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
        {gems.map((gem, i) => (
          <motion.div
            key={gem.candidate_id}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="group relative bg-[#070709] border border-white/5 rounded-[2rem] p-8 md:p-10 hover:bg-[#0a0a0c] hover:border-cyan-500/20 transition-all duration-700 hover:-translate-y-2 shadow-2xl overflow-hidden"
          >
             <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />

             <div className="absolute top-0 right-0 p-8 md:p-10">
               <div className="text-right">
                 <div className="text-[10px] uppercase font-semibold tracking-widest text-slate-500 mb-1">Talent Mispricing Index</div>
                 <div className="text-3xl font-medium tracking-tighter text-cyan-400">{formatTmi(gem.tmi)}</div>
               </div>
             </div>

             <div className="mb-8 mt-2">
                <div className="flex items-center gap-3 mb-3">
                  <div className="text-[10px] uppercase font-semibold tracking-widest text-slate-500">Identified Asset</div>
                  <span className="text-[9px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">{gem.quadrant}</span>
                </div>
                <h3 className="text-3xl font-medium text-white tracking-tight mb-2">Candidate {gem.candidate_id.split('_').pop()}</h3>
                <p className="text-base text-slate-400 font-light">{gem.title}</p>
             </div>

             {/* Conviction metrics */}
             <div className="grid grid-cols-3 gap-4 mb-8">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold mb-1">Fit</div>
                  <div className="text-2xl font-medium text-white tracking-tighter">{gem.fit}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold mb-1">Conviction</div>
                  <div className="text-2xl font-medium text-white tracking-tighter">{gem.conviction}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold mb-1">Evidence</div>
                  <div className="text-2xl font-medium text-white tracking-tighter">{gem.evidence_density}<span className="text-sm text-slate-500">%</span></div>
                </div>
             </div>

             <div className="grid grid-cols-2 gap-8 mb-10 pb-10 border-b border-white/5">
                <div>
                   <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold mb-2 block">Prior ATS Value</div>
                   <div className="text-4xl font-light text-slate-600 strike line-through decoration-white/10 tracking-tighter">#{gem.ats_rank}</div>
                </div>
                <div>
                   <div className="text-[10px] uppercase tracking-widest text-cyan-400/80 font-semibold mb-2 block">Discovery Value</div>
                   <div className="text-4xl font-medium text-white tracking-tighter">#{gem.our_rank}</div>
                </div>
             </div>

             <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">
                <div>
                  <div className="text-[10px] uppercase font-semibold tracking-widest text-cyan-400/70 mb-4 block">Core Signals</div>
                  <ul className="space-y-4">
                    {gem.trust_drivers.slice(0, 3).map((driver, idx) => (
                      <li key={idx} className="flex gap-4 text-sm font-light text-slate-300 items-start">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/50 mt-1.5 shrink-0" />
                        <span className="leading-relaxed">{driver}</span>
                      </li>
                    ))}
                    {gem.trust_drivers.length === 0 && <span className="text-slate-500 text-xs text-light italic">None provided.</span>}
                  </ul>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold tracking-widest text-rose-400/70 mb-4 block">Risk Vectors</div>
                  <ul className="space-y-4">
                    {gem.concerns.slice(0, 2).map((concern, idx) => (
                      <li key={idx} className="flex gap-4 text-sm font-light text-slate-400 items-start">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400/30 mt-1.5 shrink-0" />
                        <span className="leading-relaxed">{concern}</span>
                      </li>
                    ))}
                    {gem.concerns.length === 0 && <span className="text-slate-500 text-xs text-light italic">No critical concerns.</span>}
                  </ul>
                </div>
             </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
