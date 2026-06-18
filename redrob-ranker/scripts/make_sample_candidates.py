#!/usr/bin/env python3
"""Generate frontend/public/sample_candidates.jsonl — a 654-candidate demo pool
for the upload button (real fits, hidden gems, keyword stuffers, honeypots, filler).
Run from redrob-ranker/:  python scripts/make_sample_candidates.py
"""
import json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))
random.seed(42)
CORE=["Python","Information Retrieval","Ranking","Embeddings","Semantic Search","Recommendation Systems","NLP","Learning to Rank","Evaluation Metrics","Vector Search"]
NICE=["FAISS","Pinecone","Qdrant","Sentence Transformers","BGE","E5","NDCG","MRR","A/B Testing","LoRA","XGBoost"]
FIRST=["Aarav","Diya","Kabir","Ananya","Vivaan","Isha","Arjun","Mira","Rohan","Sara","Dev","Tara","Nikhil","Priya","Aditya","Neha","Karan","Riya","Vikram","Anjali","Sahil","Pooja","Yash","Meera","Raj","Sneha","Ishaan","Kavya","Aryan","Zoya"]
LOC=["Pune","Bengaluru","Hyderabad","Noida","Mumbai","Delhi NCR","Gurugram"]; COMP=["Nimbus","Quanta","Vector","Helix","Orbit","Forge","Cobalt","Aster","Lumen","Drift"]
rows=[]; n=0
def rec(title,industry,skills,desc,yoe,dur,assess,rrr,active,notice=30):
    global n; n+=1
    rows.append({"candidate_id":f"CAND_{n:07d}","profile":{"name":FIRST[n%len(FIRST)],"current_title":title,"headline":title,"summary":desc,"years_of_experience":yoe,"current_industry":industry,"location":random.choice(LOC),"country":"India"},
      "career_history":[{"title":title,"company":f"{random.choice(COMP)} {random.choice(['AI','Labs','Tech'])}","description":desc,"duration_months":max(1,dur),"start_date":"2019-01-01","end_date":"2024-06-01"}],
      "education":[{"degree":"BTech Computer Science","institution":"IIT","end_year":2016}],
      "skills":[{"name":s,"proficiency":"expert","duration_months":30} for s in skills],"certifications":[],
      "redrob_signals":{"last_active_date":active,"recruiter_response_rate":rrr,"open_to_work_flag":True,"interview_completion_rate":0.8,"offer_acceptance_rate":-1,"saved_by_recruiters_30d":random.randint(0,12),"search_appearance_30d":random.randint(5,40),"profile_views_received_30d":random.randint(3,30),"github_activity_score":-1,"notice_period_days":notice,"willing_to_relocate":True,"preferred_work_mode":"hybrid","profile_completeness_score":random.randint(75,98),"verified_email":True,"verified_phone":True,"linkedin_connected":True,"skill_assessment_scores":assess}})
FIT="Built and shipped production semantic search and ranking systems using embeddings and sentence transformers behind a vector index, evaluated with NDCG and MRR and validated with online A/B tests at a product company at scale."
GEM="Owned how results get ordered for millions of users; rebuilt relevance so the most useful matches surface first and proved the lift with controlled experiments. Plain work, real impact."
# Stuffer text is buzzword-stuffed so the keyword/ATS proxy pulls them up — but the title gate vetoes them.
STUFF="AI-driven marketing leader leveraging machine learning, NLP, embeddings and semantic search for ranking and recommendation of campaigns; data-driven audience targeting, retrieval and evaluation metrics across channels."
MEH="Built backend services and data pipelines; some search/analytics features, dashboards and reporting for internal product teams."
fit_t=["Machine Learning Engineer","NLP Engineer","Search Engineer","Applied Scientist","Recommendation Systems Engineer","ML Engineer","Relevance Engineer","Research Engineer","Senior Machine Learning Engineer"]
gem_t=["Software Engineer","Backend Engineer","Data Scientist","Platform Engineer","Founding Engineer"]
stuff_t=["Marketing Manager","Sales Executive","Accountant","HR Manager","Content Writer","Operations Manager","Graphic Designer","Customer Support","Civil Engineer","Mechanical Engineer"]
meh_t=["Backend Developer","Data Analyst","Software Developer","Analytics Engineer","Backend Engineer","Data Engineer"]
infra=["SQL","AWS","Docker","Kubernetes","Spark","Airflow","Pandas","Java"]
for i in range(40): rec(random.choice(fit_t),"Software/Product",CORE[:8]+random.sample(NICE,4),FIT,random.randint(5,8),random.randint(60,90),{k:random.randint(82,95) for k in ["Information Retrieval","Ranking","Python","Embeddings"]},round(random.uniform(0.6,0.85),2),"2026-05-20")
for i in range(15): rec(random.choice(gem_t),"Software/Product",["Python","Information Retrieval","Ranking","Recommendation Systems"],GEM,random.randint(6,9),random.randint(70,95),{k:random.randint(86,97) for k in ["Information Retrieval","Ranking","Recommendation Systems","Python"]},round(random.uniform(0.55,0.8),2),"2026-04-15")
for i in range(30): rec(random.choice(stuff_t),"Marketing/Sales",random.sample(CORE,5)+random.sample(NICE,4),STUFF,random.randint(6,10),random.randint(72,110),{k:random.randint(3,22) for k in random.sample(CORE,2)},round(random.uniform(0.02,0.08),2),"2023-09-01",notice=120)
for i in range(20): rec("AI Engineer","Software",CORE[:6],"Senior AI engineering across many teams.",2,260,{"Python":70},0.5,"2026-03-01")
for i in range(550):
    sk=["Python",random.choice(["Evaluation Metrics","NLP","Semantic Search"])]+random.sample(infra,3)
    rec(random.choice(meh_t),"Software",sk,MEH,random.randint(2,9),random.randint(30,80),{"Python":random.randint(60,85),random.choice(infra):random.randint(55,80)},round(random.uniform(0.25,0.6),2),random.choice(["2026-01-10","2025-11-01","2025-09-15"]))
random.shuffle(rows)
for i,r in enumerate(rows,1): r["candidate_id"]=f"CAND_{i:07d}"
out=Path(__file__).resolve().parents[1]/"frontend"/"public"/"sample_candidates.jsonl"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text("\n".join(json.dumps(r) for r in rows))
print("wrote %d candidates, %.2f MB"%(len(rows),out.stat().st_size/1e6))
from redrob_ranker import service, config as C
d=service.rank_and_dashboard(rows,(C.DATA/"job_description.txt").read_text(),top_k=100)
print("hidden_gems=%d avg_tmi=%d highest_tmi=%d mispriced=%s%% efficiency=%s%%"%(d["hidden_gems"],d["avg_tmi"],d["highest_tmi"],d["mispriced_pct"],d["market_efficiency_pct"]))
print("stuffers_in_ats_top=%d stuffers_in_our_top=%d"%(d["stuffers_in_ats_top"],d["stuffers_in_our_top"]))
idmap={r["candidate_id"]:r["profile"]["current_title"] for r in rows}
print("our top 8:", [idmap[c["candidate_id"]] for c in d["cards"][:8]])
print("hero: %s ats#%d->our#%d tmi=%d"%(idmap[d["hero"]["candidate_id"]],d["hero"]["ats_rank"],d["hero"]["our_rank"],d["hero"]["tmi"]))
