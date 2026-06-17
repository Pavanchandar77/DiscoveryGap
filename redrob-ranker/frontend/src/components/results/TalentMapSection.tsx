import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ZAxis } from 'recharts';
import { DashboardData } from '../../types';
import { formatTmi } from '../../lib/utils';

// Quadrant -> colour mapping (Talent Conviction Engine taxonomy).
const QUADRANT_COLORS: Record<string, string> = {
  'Hidden Gem': '#22d3ee',
  'Obvious Fit': '#a3e635',
  'Promising but Uncertain': '#fbbf24',
  'Ignore': 'rgba(255,255,255,0.18)',
};

function quadrantColor(quadrant: string): string {
  return QUADRANT_COLORS[quadrant] ?? 'rgba(255,255,255,0.3)';
}

export default function TalentMapSection({ data }: { data: DashboardData }) {

  const chartData = useMemo(() => {
    return data.cards.map(c => ({
      x: c.fit,
      y: c.conviction,
      z: Math.max(10, c.tmi), // Bubble size = TMI (positions undervalued)
      name: c.candidate_id,
      role: c.title,
      tmi: c.tmi,
      quadrant: c.quadrant,
    }))
  }, [data]);

  const quadrantsPresent = useMemo(() => {
    const order = ['Hidden Gem', 'Obvious Fit', 'Promising but Uncertain', 'Ignore'];
    const seen = new Set(data.cards.map(c => c.quadrant));
    return order.filter(q => seen.has(q));
  }, [data]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const pData = payload[0].payload;
      return (
        <div className="bg-[#0a0a0c]/90 backdrop-blur-xl border border-white/10 p-5 rounded-2xl shadow-2xl">
          <p className="text-white font-medium mb-1 drop-shadow tracking-tight">Asset {pData.name.split('_').pop()}</p>
          <p className="text-slate-400 text-xs mb-1 font-light">{pData.role}</p>
          <div className="inline-flex items-center gap-2 mb-4">
            <span className="w-2 h-2 rounded-full" style={{ background: quadrantColor(pData.quadrant) }} />
            <span className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: quadrantColor(pData.quadrant) }}>{pData.quadrant}</span>
          </div>
          <div className="grid grid-cols-3 gap-5 text-xs">
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1 font-semibold">Fit</span>
              <span className="text-slate-300 font-medium text-lg">{pData.x}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest block mb-1 font-semibold">Conviction</span>
              <span className="text-slate-300 font-medium text-lg">{pData.y}</span>
            </div>
            <div>
              <span className="text-[10px] text-cyan-400 uppercase tracking-widest block mb-1 font-semibold">TMI</span>
              <span className="text-white font-medium text-lg">{formatTmi(pData.tmi)}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <section className="min-h-screen py-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col justify-center">
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true, margin: "-100px" }}
         className="mb-16"
      >
        <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
          The Bet Map
        </h2>
        <p className="text-xl text-slate-400 font-light max-w-2xl leading-relaxed">
          Every ranked candidate plotted by <span className="text-white">Fit</span> against our <span className="text-white">Conviction</span>. Bubble size is the Talent Mispricing Index — how far the ATS buried them.
        </p>
      </motion.div>

      <motion.div
         initial={{ opacity: 0 }}
         whileInView={{ opacity: 1 }}
         viewport={{ once: true }}
         transition={{ duration: 1.5, delay: 0.2 }}
         className="w-full h-[600px] bg-white/[0.01] border border-white/5 rounded-3xl p-4 md:p-8 relative group shadow-2xl"
      >
        <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none rounded-3xl" />
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 20, bottom: 30, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
            <XAxis
              type="number"
              dataKey="x"
              name="Fit"
              domain={[0, 100]}
              stroke="rgba(255,255,255,0.1)"
              tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'monospace' }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              label={{ value: 'FIT →', position: 'insideBottom', offset: -15, fill: 'rgba(255,255,255,0.25)', fontSize: 10, letterSpacing: 2 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Conviction"
              domain={[0, 100]}
              stroke="rgba(255,255,255,0.1)"
              tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'monospace' }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              label={{ value: 'CONVICTION →', angle: -90, position: 'insideLeft', fill: 'rgba(255,255,255,0.25)', fontSize: 10, letterSpacing: 2 }}
            />
            <ZAxis type="number" dataKey="z" range={[30, 600]} name="TMI" />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: 'rgba(255,255,255,0.05)' }} />
            <Scatter name="Candidates" data={chartData} isAnimationActive={false}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={quadrantColor(entry.quadrant)}
                  fillOpacity={entry.quadrant === 'Ignore' ? 0.5 : 0.75}
                  className={entry.quadrant === 'Hidden Gem'
                    ? "drop-shadow-[0_0_12px_rgba(34,211,238,0.6)] mix-blend-screen transition-all duration-300 hover:scale-[1.8] origin-center cursor-pointer"
                    : "cursor-pointer hover:scale-[1.4] transition-all"}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Quadrant legend */}
      <div className="flex flex-wrap gap-x-8 gap-y-3 mt-8">
        {quadrantsPresent.map(q => (
          <div key={q} className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: quadrantColor(q) }} />
            <span className="text-xs font-medium tracking-wide text-slate-400">{q}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
