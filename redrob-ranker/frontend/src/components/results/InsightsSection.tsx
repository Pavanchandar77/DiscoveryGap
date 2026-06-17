import React from 'react';
import { motion } from 'framer-motion';
import { DashboardData } from '../../types';
import { formatInt } from '../../lib/utils';

export default function InsightsSection({ data }: { data: DashboardData }) {
  const avgTmi = formatInt(data.avg_tmi);
  const highestTmi = formatInt(data.highest_tmi);

  return (
    <section className="min-h-screen py-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col justify-center">
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true, margin: "-100px" }}
         className="mb-24"
      >
        <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
          Quantifying Market Failure
        </h2>
        <p className="text-xl text-slate-400 font-light max-w-2xl leading-relaxed">
          The discrepancy between traditional keyword indexing and true evidence density across {data.n_candidates} processed market assets.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
          className="md:col-span-8 bg-white/[0.02] border border-white/5 rounded-3xl p-10 md:p-16 flex flex-col justify-between overflow-hidden relative group"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-rose-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none" />
          <div className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase mb-4 z-10 block">Systemic Inefficiency</div>
          <div className="text-7xl md:text-9xl font-medium tracking-tighter text-white mb-6 z-10">{data.mispriced_pct}%</div>
          <p className="text-lg text-slate-400 max-w-md font-light z-10 leading-relaxed">
             Over half the talent pool is fundamentally mispriced by standard ATS ranking algorithms.
          </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}
          className="md:col-span-4 bg-white/[0.02] border border-white/5 rounded-3xl p-8 md:p-12 flex flex-col justify-between relative group overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none" />
          <div className="text-[10px] font-semibold tracking-widest text-cyan-400/80 uppercase mb-4 block z-10">Hidden Value</div>
          <div className="text-6xl md:text-7xl font-medium tracking-tighter text-white mb-4 z-10">{data.hidden_gems}</div>
          <p className="text-sm md:text-base text-slate-400 font-light z-10 leading-relaxed">
             High-conviction outliers buried deep in the market queue.
          </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.3 }}
          className="md:col-span-4 bg-white/[0.02] border border-white/5 rounded-3xl p-8 md:p-12 flex flex-col justify-between"
        >
           <div className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase mb-4 block">Average TMI</div>
           <div className="text-5xl md:text-6xl font-medium tracking-tighter text-white mb-4">{avgTmi}<span className="text-2xl text-slate-500 ml-2">pos</span></div>
           <p className="text-sm md:text-base text-slate-400 font-light leading-relaxed">
              Mean Talent Mispricing Index — positions the ATS undervalues talent by across the dataset.
           </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.4 }}
          className="md:col-span-4 bg-white/[0.02] border border-white/5 rounded-3xl p-8 md:p-12 flex flex-col justify-between"
        >
           <div className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase mb-4 block">Market Efficiency</div>
           <div className="text-5xl md:text-6xl font-medium tracking-tighter text-white mb-4">{data.market_efficiency_pct}%</div>
           <p className="text-sm md:text-base text-slate-400 font-light leading-relaxed">
              Correlation between traditional valuation and actual discovery score.
           </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.5 }}
          className="md:col-span-4 bg-white/[0.02] border border-white/5 rounded-3xl p-8 md:p-12 flex flex-col justify-between"
        >
           <div className="text-[10px] font-semibold tracking-widest text-cyan-400/80 uppercase mb-4 block">Highest TMI</div>
           <div className="text-5xl md:text-6xl font-medium tracking-tighter text-white mb-4">{highestTmi}<span className="text-2xl text-slate-500 ml-2">pos</span></div>
           <p className="text-sm md:text-base text-slate-400 font-light leading-relaxed">
              The single biggest mispricing — positions between this candidate's ATS rank and ours.
           </p>
        </motion.div>

      </div>
    </section>
  )
}
