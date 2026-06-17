import React, { useEffect } from 'react';
import { DashboardData } from '../types';
import RevealSection from '../components/results/RevealSection';
import InsightsSection from '../components/results/InsightsSection';
import TalentMapSection from '../components/results/TalentMapSection';
import HiddenGemsSection from '../components/results/HiddenGemsSection';
import ComparisonSection from '../components/results/ComparisonSection';
import ExplorerSection from '../components/results/ExplorerSection';
import DownloadSection from '../components/results/DownloadSection';
import { buildSubmissionCsv, downloadCsv } from '../lib/csv';
import { motion, useScroll, useSpring } from 'framer-motion';

export default function ResultsScreen({ data, onExit }: { data: DashboardData, onExit: () => void }) {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="bg-[#050505] min-h-screen text-slate-200 selection:bg-white/30 selection:text-white">
      {/* Global Scroll Progress */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-0.5 bg-white origin-left z-50"
        style={{ scaleX }}
      />
      
      {/* Sticky Header */}
      <header className="fixed top-0 inset-x-0 h-20 z-40 flex items-center justify-between px-6 lg:px-12 pointer-events-none mix-blend-exclusion text-white">
        <div className="font-semibold tracking-widest text-xs uppercase pointer-events-auto">
          Discovery AI
        </div>
        <div className="flex items-center gap-6 pointer-events-auto">
          <button
            onClick={() => downloadCsv('discovery_submission.csv', buildSubmissionCsv(data.cards))}
            className="text-xs font-semibold uppercase tracking-widest hover:opacity-70 transition-opacity"
          >
            Export CSV
          </button>
          <button onClick={onExit} className="text-xs font-semibold uppercase tracking-widest hover:opacity-70 transition-opacity">
            Exit View
          </button>
        </div>
      </header>

      <main className="flex flex-col">
        <RevealSection hero={data.hero} />
        <InsightsSection data={data} />
        <TalentMapSection data={data} />
        <HiddenGemsSection data={data} />
        <ComparisonSection data={data} />
        <ExplorerSection data={data} />
        <DownloadSection data={data} />
      </main>
    </div>
  )
}
