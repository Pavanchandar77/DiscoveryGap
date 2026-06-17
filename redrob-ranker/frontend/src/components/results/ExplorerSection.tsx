import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, ChevronUp } from 'lucide-react';
import { DashboardData } from '../../types';
import { formatTmi } from '../../lib/utils';

export default function ExplorerSection({ data }: { data: DashboardData }) {
  const [query, setQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const maxTmi = useMemo(
    () => Math.max(1, ...data.cards.map((c) => c.tmi)),
    [data]
  );

  const filtered = useMemo(() => {
    return data.cards.filter(c => 
       c.candidate_id.toLowerCase().includes(query.toLowerCase()) || 
       c.title.toLowerCase().includes(query.toLowerCase())
    ).sort((a,b) => a.our_rank - b.our_rank);
  }, [data, query]);

  return (
    <section className="min-h-screen py-24 px-6 md:px-12 max-w-7xl mx-auto flex flex-col justify-center">
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true, margin: "-100px" }}
         className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-8"
      >
        <div>
          <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
            Asset Discovery
          </h2>
          <p className="text-xl text-slate-400 font-light max-w-xl leading-relaxed">
            Examine the entire talent pool through the lens of pure evidence density. Search for undervalued assets.
          </p>
        </div>
        
        <div className="relative w-full md:w-80">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input 
            type="text" 
            placeholder="Search identified assets..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-[#0a0a0c] border border-white/10 rounded-full py-4 pl-12 pr-6 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:bg-white/5 transition-all duration-300"
          />
        </div>
      </motion.div>

      <div className="bg-[#050505] border border-white/10 rounded-3xl overflow-hidden shadow-2xl pb-16">
         {/* Table Header */}
         <div className="grid grid-cols-12 gap-4 px-8 py-6 border-b border-white/5 text-[10px] font-semibold uppercase tracking-widest text-slate-500 hidden md:grid bg-[#070709]">
           <div className="col-span-4">Identified Asset</div>
           <div className="col-span-2 text-right">Market Value (ATS)</div>
           <div className="col-span-2 text-right text-cyan-500/80">True Value</div>
           <div className="col-span-3 text-right">Talent Mispricing Index</div>
           <div className="col-span-1"></div>
         </div>

         {/* Table Body */}
         <div className="divide-y divide-white/5 block">
           {filtered.slice(0, 50).map(c => {
             const isExpanded = expandedId === c.candidate_id;
             const shift = c.ats_rank - c.our_rank;
             const isGem = shift > 100;
             const displayId = c.candidate_id.split('_').pop();

             return (
               <div key={c.candidate_id} className="relative group hover:bg-[#0a0a0c] transition-colors duration-300 w-full overflow-hidden">
                 {/* Row base */}
                 <div 
                   onClick={() => setExpandedId(isExpanded ? null : c.candidate_id)}
                   className="grid grid-cols-1 md:grid-cols-12 gap-4 px-8 py-6 items-center cursor-pointer relative z-10 w-full"
                 >
                   <div className="col-span-1 md:col-span-4 block">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-[#050505] border border-white/10 flex items-center justify-center text-xs font-medium text-white/70 tracking-tighter">
                          {displayId}
                        </div>
                        <div>
                          <div className="text-white font-medium mb-1 drop-shadow-sm">Candidate {displayId}</div>
                          <div className="text-slate-500 text-xs truncate max-w-[200px]">{c.title}</div>
                        </div>
                      </div>
                   </div>
                   
                   <div className="col-span-2 text-right hidden md:block w-full">
                      <div className="text-slate-500 line-through decoration-white/10 tracking-tighter font-mono">#{c.ats_rank}</div>
                   </div>
                   
                   <div className="col-span-2 text-right hidden md:block w-full">
                      <div className="text-white font-medium tracking-tighter font-mono">#{c.our_rank}</div>
                      {isGem && <div className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider mt-1">Undervalued Hit</div>}
                   </div>
                   
                   <div className="col-span-3 text-right hidden md:block w-full">
                      <div className="text-slate-300 font-medium font-mono">{formatTmi(c.tmi)}</div>
                      <div className="w-full h-1 bg-white/5 rounded-full mt-2 overflow-hidden flex justify-end">
                        <div
                           className={`h-full rounded-full transition-all duration-1000 ${isGem ? 'bg-cyan-500 shadow-[0_0_10px_rgba(34,211,238,0.5)]' : 'bg-slate-500'}`}
                           style={{ width: `${Math.max(2, Math.min(100, (c.tmi / maxTmi) * 100))}%` }}
                        />
                      </div>
                   </div>
                   
                   <div className="col-span-1 hidden md:flex justify-end w-full">
                      {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                   </div>
                 </div>

                 <AnimatePresence initial={false}>
                   {isExpanded && (
                     <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden bg-[#070709] border-t border-white/5 w-full relative z-0"
                     >
                       <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 p-8 lg:p-12 text-sm w-full">
                          
                          <div className="w-full">
                            <h4 className="text-[10px] uppercase font-semibold tracking-widest text-cyan-400/80 mb-6 flex items-center gap-2">
                              <span className="w-1 h-3 bg-cyan-400/80 rounded-full" />
                              Underlying Asset Strengths
                            </h4>
                            <ul className="space-y-4">
                              {c.trust_drivers.map((d, i) => (
                                <li key={i} className="flex gap-4 items-start w-full text-slate-300 font-light leading-relaxed">
                                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-500/50 mt-1.5 shrink-0" />
                                  <span className="block">{d}</span>
                                </li>
                              ))}
                              {c.trust_drivers.length === 0 && <span className="text-slate-500 italic">No extra evidence provided.</span>}
                            </ul>
                          </div>

                          <div className="w-full">
                            <h4 className="text-[10px] uppercase font-semibold tracking-widest text-slate-500 mb-6 flex items-center gap-2">
                              <span className="w-1 h-3 bg-slate-500 rounded-full" />
                              Pricing Rationale
                            </h4>
                            <p className="text-slate-400 font-light leading-relaxed mb-8 w-full block bg-black/50 p-5 rounded-2xl border border-white/5">
                               {c.reasoning || "Standard candidate evaluation completed. No deep rationale available."}
                            </p>

                            <h4 className="text-[10px] uppercase font-semibold tracking-widest text-rose-400/60 mb-6 flex items-center gap-2">
                              <span className="w-1 h-3 bg-rose-500/60 rounded-full" />
                              Risk Exposure
                            </h4>
                            <ul className="space-y-4">
                              {c.concerns.map((cnc, i) => (
                                <li key={i} className="flex gap-4 items-start w-full text-slate-400 font-light leading-relaxed">
                                  <div className="w-1.5 h-1.5 rounded-full bg-rose-500/30 mt-1.5 shrink-0" />
                                  <span className="block">{cnc}</span>
                                </li>
                              ))}
                              {c.concerns.length === 0 && <span className="text-slate-500 italic font-light">No red flags flagged.</span>}
                            </ul>
                          </div>
                          
                       </div>
                     </motion.div>
                   )}
                 </AnimatePresence>
               </div>
             )
           })}

           {filtered.length === 0 && (
             <div className="p-16 text-center text-slate-500 font-light">
               No assets match your search criteria.
             </div>
           )}
         </div>
      </div>
    </section>
  )
}
