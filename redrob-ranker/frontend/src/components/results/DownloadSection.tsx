import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Check } from 'lucide-react';
import { DashboardData } from '../../types';
import { buildSubmissionCsv, downloadCsv } from '../../lib/csv';

export default function DownloadSection({ data }: { data: DashboardData }) {
  const [done, setDone] = useState(false);

  const handleDownload = () => {
    const csv = buildSubmissionCsv(data.cards);
    downloadCsv('discovery_submission.csv', csv);
    setDone(true);
    setTimeout(() => setDone(false), 2500);
  };

  return (
    <section className="py-32 px-6 md:px-12 max-w-5xl mx-auto flex flex-col items-center text-center">
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         whileInView={{ opacity: 1, y: 0 }}
         viewport={{ once: true, margin: "-100px" }}
         className="w-full bg-white/[0.02] border border-white/5 rounded-[2rem] p-12 md:p-20 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(34,211,238,0.06)_0%,_transparent_60%)] pointer-events-none" />

        <div className="relative z-10 flex flex-col items-center">
          <div className="text-[10px] font-semibold tracking-widest text-cyan-400/80 uppercase mb-4">Export</div>
          <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
            Take the Ranking With You
          </h2>
          <p className="text-lg text-slate-400 font-light max-w-xl leading-relaxed mb-12">
            Download the {data.cards.length} ranked candidates as the 4-column submission CSV
            — <span className="text-slate-300 font-mono text-sm">candidate_id, rank, score, reasoning</span>.
          </p>

          <button
            onClick={handleDownload}
            className="group inline-flex items-center gap-3 px-8 py-4 rounded-full bg-white text-black font-medium text-sm hover:bg-cyan-50 transition-all duration-300 shadow-[0_0_30px_rgba(34,211,238,0.1)] hover:shadow-[0_0_40px_rgba(34,211,238,0.25)]"
          >
            {done ? <Check className="w-5 h-5" /> : <Download className="w-5 h-5" />}
            <span>{done ? 'Downloaded' : 'Download Submission CSV'}</span>
          </button>
        </div>
      </motion.div>
    </section>
  );
}
