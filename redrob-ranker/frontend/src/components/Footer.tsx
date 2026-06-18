import React from 'react';

export default function Footer() {
  return (
    <footer className="border-t border-white/5 px-6 md:px-12 py-12 mt-12">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="text-xs text-slate-600 font-light max-w-xl leading-relaxed">
          <span className="text-slate-400 font-medium">Discovery</span> is decision-support for human
          recruiters. Scores are explainable and derived from candidate-provided profile data; no
          protected attributes are used. It does not make automated hiring decisions.
        </div>
        <div className="flex items-center gap-6 text-xs font-medium tracking-wide text-slate-500">
          <a href="/sample_candidates.jsonl" download className="hover:text-white transition-colors">Sample data</a>
          <span className="text-slate-700">·</span>
          <span className="text-slate-600">Talent Market Intelligence</span>
        </div>
      </div>
    </footer>
  );
}
