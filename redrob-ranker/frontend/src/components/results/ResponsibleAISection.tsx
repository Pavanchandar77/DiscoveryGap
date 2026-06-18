import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, UserCheck, ScanSearch, Scale } from 'lucide-react';

const PILLARS = [
  {
    icon: UserCheck,
    title: 'Decision support, not automation',
    body: 'Discovery ranks and explains — a human recruiter decides. Nothing is auto-rejected or auto-hired, the legally defensible posture for hiring tools.',
  },
  {
    icon: ScanSearch,
    title: 'Transparent, not a black box',
    body: 'A gated feature ensemble, not a trained model. Every score traces to a real profile field, with a per-candidate audit trail of drivers, concerns and reasoning.',
  },
  {
    icon: Scale,
    title: 'No protected attributes',
    body: 'Scoring uses skills, evidence and role-fit only — never name, gender, age, ethnicity or photos. Reasoning is generated from extracted facts, with no hallucination.',
  },
  {
    icon: ShieldCheck,
    title: 'Built to widen the funnel',
    body: 'Keyword filters bury qualified non-traditional candidates — the real adverse-impact risk. Surfacing those overlooked-but-qualified people reduces that bias.',
  },
];

export default function ResponsibleAISection() {
  return (
    <section className="py-28 px-6 md:px-12 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mb-16 max-w-2xl"
      >
        <div className="text-[10px] font-semibold tracking-[0.2em] text-cyan-400/80 uppercase mb-4">Responsible AI</div>
        <h2 className="text-3xl md:text-5xl font-medium tracking-tight text-white mb-6">
          Explainable by construction
        </h2>
        <p className="text-xl text-slate-400 font-light leading-relaxed">
          The same rigor that finds hidden talent is what makes this defensible to a risk officer:
          transparent scoring, a human in the loop, and an audit trail on every candidate.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {PILLARS.map((p, i) => (
          <motion.div
            key={p.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
            className="bg-white/[0.02] border border-white/5 rounded-3xl p-8 md:p-10 hover:border-white/10 transition-colors duration-500"
          >
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 flex items-center justify-center mb-6">
              <p.icon className="w-5 h-5 text-cyan-400" />
            </div>
            <h3 className="text-lg font-medium text-white mb-3 tracking-tight">{p.title}</h3>
            <p className="text-sm text-slate-400 font-light leading-relaxed">{p.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
