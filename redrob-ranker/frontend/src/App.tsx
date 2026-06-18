/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import LandingScreen from './screens/LandingScreen';
import ProcessingScreen from './screens/ProcessingScreen';
import ResultsScreen from './screens/ResultsScreen';
import ErrorScreen from './screens/ErrorScreen';
import { DashboardData } from './types';

type Screen = 'LANDING' | 'PROCESSING' | 'RESULTS' | 'ERROR';

export default function App() {
  const [screen, setScreen] = useState<Screen>('LANDING');
  const [data, setData] = useState<DashboardData | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');

  return (
    <div className="min-h-screen bg-[#050505] text-slate-200 font-sans selection:bg-white/30 selection:text-white">
      {screen === 'LANDING' && <LandingScreen
        onDemo={() => { setUploadFile(null); setScreen('PROCESSING'); }}
        onUpload={(file) => { setUploadFile(file); setScreen('PROCESSING'); }}
      />}
      {screen === 'PROCESSING' && <ProcessingScreen
        file={uploadFile}
        setData={setData}
        onComplete={() => setScreen('RESULTS')}
        onError={(msg) => { setError(msg); setScreen('ERROR'); }}
      />}
      {screen === 'RESULTS' && data && <ResultsScreen
        data={data}
        onExit={() => setScreen('LANDING')}
      />}
      {screen === 'ERROR' && <ErrorScreen
        message={error}
        onRetry={() => setScreen('LANDING')}
      />}
    </div>
  );
}
