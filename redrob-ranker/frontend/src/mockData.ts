import { DashboardData } from "./types";

export const MOCK_DASHBOARD_DATA: DashboardData = {
  n_candidates: 342,
  market_efficiency_pct: 43,
  mispriced_pct: 57,
  hidden_gems: 14,
  avg_tmi: 88,
  highest_tmi: 141,
  hero: {
    candidate_id: "CAND_00142",
    title: "Senior Machine Learning Engineer",
    ats_rank: 142,
    our_rank: 1,
    tmi: 141,
    evidence_density: 88,
    fit: 96,
    conviction: 98,
    verified_skills: 15,
    claimed_skills: 16,
    quadrant: "Hidden Gem",
    trust_drivers: [
      "Authored highly cited paper on efficient attention mechanisms matching company's core challenge",
      "Contributed to open source ML infrastructure library used by target team",
    ],
    concerns: [
      "Lacks formal CS degree (Self-taught/Physics Background) - likely cause of ATS penalty",
    ],
    reasoning: "Exceptional evidence of deep ML expertise despite missing traditional keyword requirements."
  },
  ats_top10: [
    "Machine Learning Engineer",
    "Senior Data Scientist",
    "AI Researcher",
    "Software Engineer, AI",
    "Data Engineer",
    "Principal Generative AI Engineer",
    "Senior NLP Engineer",
    "ML Ops Engineer",
    "Lead AI Architect",
    "Data Scientist"
  ],
  our_top10: [
    "Senior Machine Learning Engineer",
    "Lead AI Engineer",
    "Research Scientist",
    "Principal ML Engineer",
    "NLP Specialist",
    "Senior NLP Engineer",
    "AI Product Engineer",
    "Machine Learning Architect",
    "Senior AI Researcher",
    "ML Infrastructure Engineer"
  ],
  stuffers_in_ats_top: 4,
  stuffers_in_our_top: 0,
  cards: []
};

for (let i = 1; i <= 50; i++) {
  const isStuffer = Math.random() < 0.1;
  const ats_rank = isStuffer ? i : Math.floor(Math.random() * 342) + 1;
  const our_rank = isStuffer ? 300 + i : i;
  const fit = isStuffer ? Math.floor(Math.random() * 40) : Math.floor(80 + Math.random() * 20);
  const conviction = isStuffer ? Math.floor(Math.random() * 30) : Math.floor(70 + Math.random() * 30);
  const evidence_density = isStuffer ? Math.floor(Math.random() * 20) : Math.floor(60 + Math.random() * 40);
  const tmi = ats_rank - our_rank;
  
  let quadrant = "Promising but Uncertain";
  if (tmi > 80 && fit > 85) quadrant = "Hidden Gem";
  else if (tmi < 20 && tmi > -20 && fit > 80) quadrant = "Obvious Fit";
  else if (isStuffer) quadrant = "Ignore";

  MOCK_DASHBOARD_DATA.cards.push({
    candidate_id: `CAND_${i.toString().padStart(5, '0')}`,
    title: i % 3 === 0 ? "Senior Data Scientist" : i % 5 === 0 ? "NLP Engineer" : "Machine Learning Engineer",
    ats_rank,
    our_rank,
    tmi,
    evidence_density,
    fit,
    conviction,
    verified_skills: Math.floor(evidence_density / 10),
    claimed_skills: isStuffer ? 20 : Math.floor(evidence_density / 10) + 2,
    quadrant,
    trust_drivers: quadrant === "Hidden Gem" ? ["High code quality shown", "Strong repo history"] : [],
    concerns: isStuffer ? ["Excessive skill keywords without clear experience mapping"] : [],
    reasoning: "Generated reasoning based on candidate profile."
  });
}
