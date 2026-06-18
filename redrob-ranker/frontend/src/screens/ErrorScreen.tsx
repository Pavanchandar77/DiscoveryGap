import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, RotateCcw } from 'lucide-react';

interface Props {
  message: string;
  onRetry: () => void;
}

export default function ErrorScreen({ message, onRetry }: Props) {
  return (
    <div className="fixed inset-0 bg-[#050505] flex items-center justify-center px-6 z-50">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-lg text-center"
      >
        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-8">
          <AlertCircle className="w-7 h-7 text-rose-400" />
        </div>
        <h2 className="text-2xl md:text-3xl font-medium text-white tracking-tight mb-4">That didn't rank</h2>
        <p className="text-slate-400 font-light leading-relaxed mb-10">{message}</p>
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-white text-black font-medium text-sm hover:bg-slate-200 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Try another file
        </button>
        <p className="mt-8 text-xs text-slate-600 font-light">
          Expecting a candidates <span className="text-slate-400">.jsonl</span> / <span className="text-slate-400">.zip</span> / <span className="text-slate-400">.jsonl.gz</span>.
          Need one? <a href="/sample_candidates.jsonl" download className="text-cyan-400 hover:underline">Download a sample</a>.
        </p>
      </motion.div>
    </div>
  );
}
