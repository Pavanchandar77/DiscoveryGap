import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import { DashboardData } from '../../types';

export default function ComparisonSection({ data }: { data: DashboardData }) {
  const atsList = data.ats_top10 ?? [];
  const ourList = data.our_top10 ?? [];
  const rows = Math.max(atsList.length, ourList.length);

  return (
    <section className="min-h-screen py-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col justify-center">
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true, margin: "-100px" }}
         className="mb-16 text-center"
      >
        <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
          ATS vs Discovery
        </h2>
        <p className="text-xl text-slate-400 font-light max-w-2xl mx-auto leading-relaxed">
          The legacy keyword index against the Discovery engine — same pool, two different top tens.
        </p>
      </motion.div>

      {/* Stuffer scoreboard */}
      <motion.div
         initial={{ opacity: 0, y: 20 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true }}
         className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16"
      >
        <div className="bg-rose-500/[0.04] border border-rose-500/10 rounded-3xl p-8 flex items-center gap-6">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/10 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-6 h-6 text-rose-400" />
          </div>
          <div>
            <div className="text-4xl md:text-5xl font-medium tracking-tighter text-white">{data.stuffers_in_ats_top}</div>
            <div className="text-sm text-slate-400 font-light mt-1">Keyword stuffers in the ATS top-100</div>
          </div>
        </div>
        <div className="bg-cyan-500/[0.04] border border-cyan-500/10 rounded-3xl p-8 flex items-center gap-6">
          <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <div className="text-4xl md:text-5xl font-medium tracking-tighter text-white">{data.stuffers_in_our_top}</div>
            <div className="text-sm text-slate-400 font-light mt-1">Keyword stuffers in the Discovery top</div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 relative">
        {/* Connection divider */}
        <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-white/10 to-transparent -translate-x-1/2" />

        {/* ATS Side */}
        <div className="relative">
           <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-8 pb-4 border-b border-white/5 pl-4">Legacy ATS · Top 10</div>
           <div className="space-y-3">
             {atsList.map((title, i) => (
               <div
                 key={`ats-${i}`}
                 className="flex items-center gap-6 p-5 rounded-2xl transition-all duration-300 border border-transparent hover:bg-white/[0.02]"
               >
                 <div className="text-2xl font-light text-slate-600 w-8 tracking-tighter text-right">{i + 1}</div>
                 <div className="flex-1 min-w-0">
                   <div className="text-slate-300 font-medium truncate">{title}</div>
                 </div>
               </div>
             ))}
             {atsList.length === 0 && <div className="text-slate-600 text-sm font-light pl-4">No ATS ranking provided.</div>}
           </div>
        </div>

        {/* Discovery Side */}
        <div className="relative">
           <div className="text-[10px] font-semibold uppercase tracking-widest text-cyan-400 mb-8 pb-4 border-b border-white/5 pl-4">Discovery Engine · Top 10</div>
           <div className="space-y-3">
             {ourList.map((title, i) => (
               <div
                 key={`our-${i}`}
                 className="flex items-center gap-6 p-5 rounded-2xl transition-all duration-300 border border-transparent hover:bg-cyan-950/10"
               >
                 <div className="text-2xl font-medium text-cyan-500 w-8 tracking-tighter text-right drop-shadow-sm">{i + 1}</div>
                 <div className="flex-1 min-w-0">
                   <div className="text-white font-medium truncate">{title}</div>
                 </div>
               </div>
             ))}
             {ourList.length === 0 && <div className="text-slate-600 text-sm font-light pl-4">No Discovery ranking provided.</div>}
           </div>
        </div>

        {rows === 0 && null}
      </div>
    </section>
  )
}
