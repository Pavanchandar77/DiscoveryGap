import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShieldCheck, AlertTriangle, FileSearch } from 'lucide-react';
import { Candidate } from '../types';
import { formatTmi, formatInt } from '../lib/utils';

/**
 * Explainability / audit panel for a single candidate. Every number shown here
 * traces to a field the engine extracted from the profile — it's the per-decision
 * audit trail (no black-box score, no protected attributes).
 */
function Bar({ label, value, suffix = '', accent = false }: { label: string; value: number; suffix?: string; accent?: boolean }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">{label}</span>
        <span className={`text-sm font-medium ${accent ? 'text-cyan-400' : 'text-white'}`}>{value}{suffix}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${accent ? 'bg-cyan-400' : 'bg-slate-400'}`}
          style={{ width: `${Math.max(2, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}

export default function CandidateModal({ candidate, onClose }: { candidate: Candidate | null; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (candidate) {
      document.addEventListener('keydown', onKey);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [candidate, onClose]);

  return (
    <AnimatePresence>
      {candidate && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4 md:p-8"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          role="dialog" aria-modal="true" aria-label={`Why we ranked candidate ${candidate.candidate_id}`}
        >
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 20 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full max-w-3xl max-h-[88vh] overflow-y-auto bg-[#0a0a0c] border border-white/10 rounded-3xl shadow-2xl"
          >
            <button
              onClick={onClose}
              aria-label="Close"
              className="absolute top-5 right-5 z-10 w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="p-8 md:p-12">
              {/* Header */}
              <div className="flex items-center gap-2 mb-5 text-cyan-400/80">
                <FileSearch className="w-4 h-4" />
                <span className="text-[10px] uppercase tracking-[0.2em] font-semibold">Why this ranking · audit trail</span>
              </div>
              <div className="flex flex-wrap items-center gap-3 mb-1">
                <h3 className="text-3xl font-medium text-white tracking-tight">Candidate {candidate.candidate_id.split('_').pop()}</h3>
                <span className="text-[10px] uppercase tracking-widest font-semibold px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">{candidate.quadrant}</span>
              </div>
              <p className="text-slate-400 font-light mb-8">{candidate.title}</p>

              {/* Rank movement */}
              <div className="grid grid-cols-3 gap-4 mb-10 p-5 rounded-2xl bg-white/[0.02] border border-white/5">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold mb-1">ATS rank</div>
                  <div className="text-2xl font-light text-slate-500 line-through decoration-rose-500/40">#{formatInt(candidate.ats_rank)}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-cyan-400/80 font-semibold mb-1">Our rank</div>
                  <div className="text-2xl font-medium text-white">#{formatInt(candidate.our_rank)}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold mb-1">TMI</div>
                  <div className="text-2xl font-medium text-cyan-400">{formatTmi(candidate.tmi)}</div>
                </div>
              </div>

              {/* Transparent metric breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-10 gap-y-6 mb-10">
                <Bar label="Fit (relevance)" value={candidate.fit} />
                <Bar label="Conviction (certainty)" value={candidate.conviction} accent />
                <Bar label="Evidence density" value={candidate.evidence_density} suffix="%" />
                <div>
                  <div className="flex items-baseline justify-between mb-2">
                    <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Skills verified</span>
                    <span className="text-sm font-medium text-white">{candidate.verified_skills}/{candidate.claimed_skills}</span>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-slate-400" style={{ width: `${candidate.claimed_skills ? Math.min(100, (candidate.verified_skills / candidate.claimed_skills) * 100) : 0}%` }} />
                  </div>
                </div>
              </div>

              {/* Drivers / concerns */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
                <div>
                  <div className="flex items-center gap-2 mb-4 text-cyan-400/80">
                    <ShieldCheck className="w-4 h-4" />
                    <span className="text-[10px] uppercase tracking-widest font-semibold">Trust drivers</span>
                  </div>
                  <ul className="space-y-3">
                    {candidate.trust_drivers.map((d, i) => (
                      <li key={i} className="flex gap-3 text-sm font-light text-slate-300 items-start leading-relaxed">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 mt-1.5 shrink-0" />{d}
                      </li>
                    ))}
                    {candidate.trust_drivers.length === 0 && <li className="text-slate-600 text-sm italic">None recorded.</li>}
                  </ul>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-4 text-rose-400/70">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-[10px] uppercase tracking-widest font-semibold">Concerns</span>
                  </div>
                  <ul className="space-y-3">
                    {candidate.concerns.map((c, i) => (
                      <li key={i} className="flex gap-3 text-sm font-light text-slate-400 items-start leading-relaxed">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-400/40 mt-1.5 shrink-0" />{c}
                      </li>
                    ))}
                    {candidate.concerns.length === 0 && <li className="text-slate-600 text-sm italic">No critical concerns flagged.</li>}
                  </ul>
                </div>
              </div>

              {/* Reasoning */}
              <div className="mb-2">
                <div className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-3">Plain-language reasoning</div>
                <p className="text-slate-300 font-light leading-relaxed bg-black/40 border border-white/5 rounded-2xl p-5">
                  {candidate.reasoning || 'Standard evaluation completed.'}
                </p>
              </div>

              <p className="mt-8 text-xs text-slate-600 font-light leading-relaxed">
                Every figure above is derived from fields in this candidate's own profile — skills, assessments,
                career history and platform signals. No protected attributes are used, and this is decision
                support for a human recruiter, not an automated hiring decision.
              </p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
