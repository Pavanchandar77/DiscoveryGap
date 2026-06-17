export type Candidate = {
  candidate_id: string;
  title: string;
  fit: number;
  conviction: number;
  tmi: number;
  our_rank: number;
  ats_rank: number;
  evidence_density: number;
  verified_skills: number;
  claimed_skills: number;
  quadrant: string;
  trust_drivers: string[];
  concerns: string[];
  reasoning: string;
};

export type DashboardData = {
  n_candidates: number;
  market_efficiency_pct: number;
  mispriced_pct: number;
  hidden_gems: number;
  avg_tmi: number;
  highest_tmi: number;
  hero: Candidate;
  cards: Candidate[];
  ats_top10: string[];
  our_top10: string[];
  stuffers_in_ats_top: number;
  stuffers_in_our_top: number;
};
