#!/usr/bin/env python3
"""Generate a professionally designed PDF pitch deck for the Talent Conviction Engine."""
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "pitch_deck.pdf"

# Color Palette
BG_COLOR = colors.HexColor('#020202')
CARD_BG = colors.HexColor('#070709')
BORDER_COLOR = colors.HexColor('#1f1f2e')
TEXT_WHITE = colors.HexColor('#ffffff')
TEXT_MUTED = colors.HexColor('#94a3b8')
CYAN = colors.HexColor('#22d3ee')
ROSE = colors.HexColor('#fb7185')

class PitchDeckCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_slide_decorations(page_count)
            super().showPage()
        super().save()

    def draw_slide_decorations(self, total_pages):
        # Draw background
        self.setFillColor(BG_COLOR)
        self.rect(0, 0, 792, 612, fill=True, stroke=False)
        
        # Subtle glow effects
        self.setFillColor(colors.HexColor('#112233'))
        self.circle(396, -200, 500, fill=True, stroke=False)
        
        # Grid/Footer (Except on Title page)
        if self._pageNumber > 1:
            # Top accent line
            self.setStrokeColor(CYAN)
            self.setLineWidth(1.5)
            self.line(40, 570, 752, 570)
            
            # Bottom info line
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(40, 45, 752, 45)
            
            # Footer text
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(CYAN)
            self.drawString(40, 30, "DISCOVERY")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(110, 30, "|  Talent Conviction Engine Pitch Deck")
            
            self.drawRightString(752, 30, f"Slide {self._pageNumber} of {total_pages}")

def draw_p(canv, text, size, color, x, y, width, height, is_bold=False, leading=None):
    if leading is None:
        leading = size + 4
    style = ParagraphStyle(
        name=f"p_{size}_{color.hexval()}_{is_bold}",
        fontName="Helvetica-Bold" if is_bold else "Helvetica",
        fontSize=size,
        textColor=color,
        leading=leading
    )
    p = Paragraph(text, style)
    p.wrapOn(canv, width, height)
    p.drawOn(canv, x, y - p.height)
    return p.height

def draw_card(canv, x, y, w, h, border_color=BORDER_COLOR):
    canv.setFillColor(CARD_BG)
    canv.setStrokeColor(border_color)
    canv.setLineWidth(1)
    canv.roundRect(x, y, w, h, 16, fill=True, stroke=True)

def generate_deck():
    c = PitchDeckCanvas(str(OUTPUT_PATH), pagesize=landscape(letter))
    
    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    # Centered Title
    draw_p(c, "TALENT CONVICTION ENGINE", 40, TEXT_WHITE, 60, 360, 672, 100, is_bold=True, leading=48)
    draw_p(c, "Pricing the Information Asymmetry in Hiring", 22, CYAN, 60, 300, 672, 50, is_bold=False)
    
    # Subtext / Presenter Info
    desc = ("Most teams built a better keyword ATS. We built talent market intelligence: "
            "a system that quantifies and prices the gap between what a résumé says "
            "and what a candidate actually knows.")
    draw_p(c, desc, 12, TEXT_MUTED, 60, 240, 500, 100, leading=18)
    
    draw_p(c, "India.Runs Track 2  ·  Team Discovery", 10, CYAN, 60, 100, 500, 30, is_bold=True)
    c.showPage()
    
    # -------------------------------------------------------------
    # SLIDE 2: The Core Problem
    # -------------------------------------------------------------
    draw_p(c, "THE CORE THESIS", 10, CYAN, 40, 550, 500, 20, is_bold=True)
    draw_p(c, "Hiring Markets Systematically Misprice People", 26, TEXT_WHITE, 40, 530, 600, 40, is_bold=True)
    
    # Left Column: The Problem
    draw_card(c, 40, 120, 340, 330)
    draw_p(c, "The Keyword Trap", 16, ROSE, 70, 410, 280, 30, is_bold=True)
    prob_text = ("Traditional ATS and search indexers treat profiles as flat bags of words. "
                 "Candidates who possess deep expertise but omit specific buzzwords are "
                 "buried. Conversely, keyword stuffers who copy-paste the job description "
                 "surface at the top.<br/><br/>"
                 "Naive semantic similarity models exacerbate this by matching titles rather than underlying evidence, "
                 "ranking junior lookalikes above senior practitioners.")
    draw_p(c, prob_text, 11, TEXT_MUTED, 70, 370, 280, 230, leading=16)
    
    # Right Column: The Solution
    draw_card(c, 412, 120, 340, 330)
    draw_p(c, "Talent Market Intelligence", 16, CYAN, 442, 410, 280, 30, is_bold=True)
    sol_text = ("We treat hiring as an <b>information asymmetry</b> problem.<br/><br/>"
                "The Talent Conviction Engine gates keywords and titles with concrete evidence: "
                "assessed skill scores, verified project momentum, and experience scale. "
                "It calculates a <b>Talent Mispricing Index (TMI)</b> for every profile to "
                "find high-conviction assets that the market has undervalued.")
    draw_p(c, sol_text, 11, TEXT_MUTED, 442, 370, 280, 230, leading=16)
    
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 3: The Recruiter Dashboard
    # -------------------------------------------------------------
    draw_p(c, "THE METRICS", 10, CYAN, 40, 550, 500, 20, is_bold=True)
    draw_p(c, "57% of Top Talent is Mispriced by Legacy Systems", 26, TEXT_WHITE, 40, 530, 700, 40, is_bold=True)
    
    # Big Stat Card (Left)
    draw_card(c, 40, 120, 340, 330, border_color=ROSE)
    draw_p(c, "SYSTEMIC INEFFICIENCY", 11, ROSE, 70, 410, 280, 20, is_bold=True)
    draw_p(c, "57%", 72, TEXT_WHITE, 70, 380, 280, 80, is_bold=True)
    metric_desc = ("On the India.Runs pool, 57% of the true top-100 candidates are mispriced "
                   "and overlooked by keyword-matching ATS algorithms.<br/><br/>"
                   "By indexing the <b>Discovery Gap</b>, we surface these buried profiles directly "
                   "to recruiters before they are poached by competitors.")
    draw_p(c, metric_desc, 11, TEXT_MUTED, 70, 280, 280, 150, leading=16)
    
    # Small Stat Cards (Right)
    # Card 1: Hidden Gems
    draw_card(c, 400, 290, 170, 160, border_color=CYAN)
    draw_p(c, "HIDDEN GEMS FOUND", 9, TEXT_MUTED, 420, 420, 130, 20, is_bold=True)
    draw_p(c, "56", 36, CYAN, 420, 390, 130, 40, is_bold=True)
    draw_p(c, "Top-tier profiles buried deep in the applicant pool.", 9, TEXT_MUTED, 420, 340, 130, 60, leading=12)
    
    # Card 2: Avg TMI
    draw_card(c, 582, 290, 170, 160)
    draw_p(c, "AVG MISPRICING", 9, TEXT_MUTED, 602, 420, 130, 20, is_bold=True)
    draw_p(c, "+1,034", 36, TEXT_WHITE, 602, 390, 130, 40, is_bold=True)
    draw_p(c, "Average positions saved per candidate vs baseline.", 9, TEXT_MUTED, 602, 340, 130, 60, leading=12)

    # Card 3: Market Efficiency
    draw_card(c, 400, 120, 170, 150)
    draw_p(c, "MARKET EFFICIENCY", 9, TEXT_MUTED, 420, 240, 130, 20, is_bold=True)
    draw_p(c, "43%", 36, TEXT_WHITE, 420, 210, 130, 40, is_bold=True)
    draw_p(c, "Overlap between ATS and Discovery top lists.", 9, TEXT_MUTED, 420, 160, 130, 50, leading=12)

    # Card 4: Max TMI
    draw_card(c, 582, 120, 170, 150)
    draw_p(c, "MAX MISPRICING", 9, TEXT_MUTED, 602, 240, 130, 20, is_bold=True)
    draw_p(c, "+23k+", 36, TEXT_WHITE, 602, 210, 130, 40, is_bold=True)
    draw_p(c, "Highest individual position saved from keyword void.", 9, TEXT_MUTED, 602, 160, 130, 50, leading=12)

    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 4: Exhibit A Case Study
    # -------------------------------------------------------------
    draw_p(c, "CASE STUDY", 10, CYAN, 40, 550, 500, 20, is_bold=True)
    draw_p(c, "Exhibit A: From Keyword Void to Top Shortlist", 26, TEXT_WHITE, 40, 530, 700, 40, is_bold=True)
    
    # Left: The Failure
    draw_card(c, 40, 120, 340, 330)
    draw_p(c, "Burying the Best", 16, ROSE, 70, 410, 280, 30, is_bold=True)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_WHITE)
    c.drawString(70, 360, "Candidate #1788 in ATS")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(70, 340, "Status: Not Reviewed (Rank 1,788 / 100,000)")
    
    failure_text = ("The candidate's resume lacked the buzzwords 'embeddings' and 'retrieval' "
                    "in its skill lists. Because similarity-based models matched titles rather than "
                    "evidence, the candidate was pushed deep into the stack.<br/><br/>"
                    "No human recruiter would ever have scrolled down to see them.")
    draw_p(c, failure_text, 11, TEXT_MUTED, 70, 310, 280, 180, leading=16)

    # Right: Our ranking
    draw_card(c, 412, 120, 340, 330, border_color=CYAN)
    draw_p(c, "Surfacing True Fit", 16, CYAN, 442, 410, 280, 30, is_bold=True)
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_WHITE)
    c.drawString(442, 360, "Candidate #4 in Discovery")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(CYAN)
    c.drawString(442, 340, "Talent Mispricing Index: +1,784 Positions")
    
    success_text = ("We ranked them #4 because our parser extracted:<br/>"
                    "  ✓ <b>Proven experience:</b> Built core ranking and vector search systems at product-company scale.<br/>"
                    "  ✓ <b>Verified capabilities:</b> 94/100 assessment score in Information Retrieval.<br/>"
                    "  ✓ <b>Growth momentum:</b> Strong upward trajectory toward search & ranking engineering.")
    draw_p(c, success_text, 11, TEXT_MUTED, 442, 310, 280, 180, leading=16)

    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 5: Core Solution Framework
    # -------------------------------------------------------------
    draw_p(c, "THE FRAMEWORK", 10, CYAN, 40, 550, 500, 20, is_bold=True)
    draw_p(c, "Fit, Conviction, and Mispricing", 26, TEXT_WHITE, 40, 530, 700, 40, is_bold=True)
    
    # Card 1: Fit
    draw_card(c, 40, 120, 230, 330)
    draw_p(c, "01. Fit", 16, TEXT_WHITE, 60, 410, 190, 30, is_bold=True)
    draw_p(c, "Is the candidate capable?", 11, CYAN, 60, 380, 190, 20, is_bold=True)
    fit_desc = ("Calculated via a gated 4-bucket model:<br/>"
                "• <b>Capability:</b> Semantic/lexical JD fit + verified assessments.<br/>"
                "• <b>Growth:</b> Momentum + role trajectory.<br/>"
                "• <b>Adaptability:</b> Product scale + company velocity.<br/>"
                "• <b>Authenticity:</b> Notice period, notice penalties, location preferences.")
    draw_p(c, fit_desc, 10, TEXT_MUTED, 60, 340, 190, 200, leading=15)

    # Card 2: Conviction
    draw_card(c, 281, 120, 230, 330, border_color=CYAN)
    draw_p(c, "02. Conviction", 16, TEXT_WHITE, 301, 410, 190, 30, is_bold=True)
    draw_p(c, "How sure are we?", 11, CYAN, 301, 380, 190, 20, is_bold=True)
    conv_desc = ("Measures evidence density and trustworthiness:<br/>"
                 "• <b>Evidence Density:</b> Ratio of verified to claimed skills.<br/>"
                 "• <b>Authenticity Multiplier:</b> Penalty for skill bluffing and mismatching profiles.<br/>"
                 "• <b>Stability Analysis:</b> Sensitivity of candidate rank under perturbed weights.")
    draw_p(c, conv_desc, 10, TEXT_MUTED, 301, 340, 190, 200, leading=15)

    # Card 3: Mispricing
    draw_card(c, 522, 120, 230, 330)
    draw_p(c, "03. Mispricing", 16, TEXT_WHITE, 542, 410, 190, 30, is_bold=True)
    draw_p(c, "Where is the gap?", 11, CYAN, 542, 380, 190, 20, is_bold=True)
    mis_desc = ("Calculates the market opportunity:<br/>"
                "• <b>TMI:</b> <code>ats_rank − our_rank</code>.<br/>"
                "• Surfaces <b>Hidden Gems</b>: High-fit, high-conviction profiles buried by keyword-matching.<br/>"
                "• Exposes systemic gaps in legacy screening algorithms.")
    draw_p(c, mis_desc, 10, TEXT_MUTED, 542, 340, 190, 200, leading=15)

    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 6: The Bet Map Grid
    # -------------------------------------------------------------
    draw_p(c, "THE STRATEGY", 10, CYAN, 40, 550, 500, 20, is_bold=True)
    draw_p(c, "The Bet Map: Aligning Quality and Risk", 26, TEXT_WHITE, 40, 530, 700, 40, is_bold=True)
    
    # 2x2 Grid Layout
    # Top Left: Hidden Gems
    draw_card(c, 40, 290, 340, 160, border_color=CYAN)
    draw_p(c, "HIDDEN GEMS", 14, CYAN, 60, 420, 300, 20, is_bold=True)
    draw_p(c, "High Fit × High Conviction (Buried by ATS)", 10, TEXT_MUTED, 60, 400, 300, 15, is_bold=True)
    gems_desc = ("Profiles with strong evidence and career trajectory that lacks keyword alignment. "
                 "Represent 56% of our shortlist. Surfacing these is our primary value proposition.")
    draw_p(c, gems_desc, 10, TEXT_MUTED, 60, 375, 300, 70, leading=14)

    # Top Right: Obvious Fits
    draw_card(c, 412, 290, 340, 160)
    draw_p(c, "OBVIOUS FITS", 14, TEXT_WHITE, 432, 420, 300, 20, is_bold=True)
    draw_p(c, "High Fit × High Conviction (Ranked High by ATS)", 10, TEXT_MUTED, 432, 400, 300, 15, is_bold=True)
    fits_desc = ("Candidates with strong alignment that both keyword search and semantic engines agree on. "
                 "Important to keep, but highly competitive and expensive to acquire.")
    draw_p(c, fits_desc, 10, TEXT_MUTED, 432, 375, 300, 70, leading=14)

    # Bottom Left: Uncertain/Underdeveloped
    draw_card(c, 40, 120, 340, 150)
    draw_p(c, "PROMISING BUT UNCERTAIN", 14, TEXT_WHITE, 60, 240, 300, 20, is_bold=True)
    draw_p(c, "High Fit × Low Conviction", 10, TEXT_MUTED, 60, 220, 300, 15, is_bold=True)
    unc_desc = ("Candidates claiming relevant keywords but lacking assessment backing or verified product momentum. "
                "Routed to manual screening or phone screens to verify claims.")
    draw_p(c, unc_desc, 10, TEXT_MUTED, 60, 195, 300, 60, leading=14)

    # Bottom Right: Ignore
    draw_card(c, 412, 120, 340, 150, border_color=ROSE)
    draw_p(c, "IGNORE / REJECT", 14, ROSE, 432, 240, 300, 20, is_bold=True)
    draw_p(c, "Low Fit / Genuineness Risks (Honeypots)", 10, TEXT_MUTED, 432, 220, 300, 15, is_bold=True)
    ign_desc = ("Keyword stuffers and honeypot profiles flagged by inconsistency checks "
                "(e.g., claiming 10y experience in a 2y old technology or high scores with short tenure). "
                "Hard-gated out with a score of 0.")
    draw_p(c, ign_desc, 10, TEXT_MUTED, 432, 195, 300, 60, leading=14)

    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 7: Safety, Trust, and Robustness
    # -------------------------------------------------------------
    draw_p(c, "TRUST & INTEGRITY", 10, CYAN, 40, 550, 500, 20, is_bold=True)
    draw_p(c, "Category-Defining Robustness & Safety", 26, TEXT_WHITE, 40, 530, 700, 40, is_bold=True)
    
    # Left Column: Trap Resistance
    draw_card(c, 40, 120, 340, 330)
    draw_p(c, "Trap Resistance by Design", 16, CYAN, 70, 410, 280, 30, is_bold=True)
    
    trap_text = ("• <b>Zero Honeypots:</b> 7 logic checks catch fabricated resumes (e.g., skill/tenure contradictions). "
                 "Under evaluation, our top-100 contains <b>0</b> honeypot profiles.<br/><br/>"
                 "• <b>Zero Stuffers:</b> Multiplicative title-level gates prevent keyword-stuffed resumes from surfacing "
                 "unless they have the career tenure to back it up. Our top-10 has <b>0</b> keyword-stuffers.")
    draw_p(c, trap_text, 11, TEXT_MUTED, 70, 370, 280, 230, leading=18)

    # Right Column: Explainable AI & Self-Awareness
    draw_card(c, 412, 120, 340, 330, border_color=CYAN)
    draw_p(c, "Explainable AI (XAI) & Reliability", 16, CYAN, 442, 410, 280, 30, is_bold=True)
    
    trust_text = ("• <b>Counterfactual Explanations:</b> For candidates ranked 16-100, the system calculates and prints "
                  "the single highest-leverage skill action that would raise their score (e.g., adding retrieval depth).<br/><br/>"
                  "• <b>Rank Stability Meta-Analysis:</b> Perturbs scoring weights randomly to assign each candidate "
                  "a rank stability rating ('Stable', 'Moderate', 'Fragile') so recruiters know where scoring is sensitive.")
    draw_p(c, trust_text, 11, TEXT_MUTED, 442, 370, 280, 230, leading=18)

    c.showPage()
    
    c.save()
    print("Successfully generated pitch_deck.pdf!")

if __name__ == "__main__":
    generate_deck()
