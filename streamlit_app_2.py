import streamlit as st
from openai import OpenAI
from io import BytesIO
from docx import Document

# ─────────────────────────────────────────────────────────────
#  OpenAI client
# ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=st.secrets.openai_api_key)

# ─────────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="✍️ Motley Fool AI Copywriter",
    initial_sidebar_state="expanded"   # ← ensures sidebar is open
)
st.title("✍️ Motley Fool AI Copywriter")

st.markdown(
    "<style> div.stButton > button { width: 100%; } </style>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
#  Session-state helper
# ─────────────────────────────────────────────────────────────
def _init(**defaults):
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init(
    generated_copy="",
    brief=None,
    last_traits=None,
    adapted_copy="",
)

def line(label: str, value: str) -> str:
    return f"- {label}: {value}\n" if value else ""

# ─────────────────────────────────────────────────────────────
#  Prompt snippets
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT_BASE = (
    "You are an expert Motley Fool copywriter. "
    "Write in plain, transparent, optimistic, conversational style. "
    "Apply Ogilvy clarity, Sugarman storytelling, Halbert persuasion, and Cialdini influence as appropriate."
)

COUNTRY_PROMPTS = {
    "Australia":      "Use Australian English, prices in AUD, and reference the ASX where relevant.",
    "United Kingdom": "Use British English, prices in GBP, and reference the FTSE where relevant.",
    "Canada":         "Use Canadian English, prices in CAD, and reference the TSX where relevant.",
    "United States":  "Use American English, prices in USD, and reference the S&P 500 where relevant.",
}

# ─────────────────────────────────────────────────────────────
#  Tab layout
# ─────────────────────────────────────────────────────────────
tab_gen, tab_adapt = st.tabs(["✍️ Generate Copy", "🌐 Adapt Copy"])

# ============================================================
#  TAB 1 — Generate Copy
# ============================================================
with tab_gen:

    # ---------- Trait sliders in sidebar ----------
    with st.sidebar.expander("🎚️ Linguistic Trait Intensity", expanded=True):
        with st.form("trait_form"):
            trait_scores = {
                "Urgency":             st.slider("Urgency & Time Sensitivity", 1, 10, 8),
                "Data_Richness":       st.slider("Data-Richness & Numerical Emphasis", 1, 10, 7),
                "Social_Proof":        st.slider("Social Proof & Testimonials", 1, 10, 6),
                "Comparative_Framing": st.slider("Comparative Framing", 1, 10, 6),
                "Imagery":             st.slider("Imagery & Metaphors", 1, 10, 7),
                "Conversational_Tone": st.slider("Conversational Tone", 1, 10, 8),
                "FOMO":                st.slider("FOMO (Fear of Missing Out)", 1, 10, 7),
                "Repetition":          st.slider("Repetition for Emphasis", 1, 10, 5),
            }
            trait_submit = st.form_submit_button("🔄 Update Copy with Adjusted Traits")

    # ---------- Generation inputs ----------
    country       = st.selectbox("🌐 Target Country", list(COUNTRY_PROMPTS))
    copy_type     = st.selectbox("Copy Type", ["📧 Email", "📝 Sales Page"])
    length_choice = st.selectbox(
        "Desired Length",
        [
            "📏 Short (100–200 words)",
            "📐 Medium (200–500 words)",
            "📖 Long (500–1500 words)",
            "📚 Extra Long (1500–3000 words)",
            "📜 Scrolling Monster (3000+ words)",
        ],
    )

    st.subheader("Campaign Brief")
    hook    = st.text_area("🪝 Campaign Hook")
    details = st.text_area("📦 Product / Offer Details")

    st.subheader("💰 Offer Breakdown")
    c1, c2, c3 = st.columns(3)
    offer_price  = c1.text_input("Special Offer Price")
    retail_price = c2.text_input("Retail Price")
    offer_term   = c3.text_input("Subscription Term")

    reports         = st.text_area("📑 Included Reports (if any)")
    stocks_to_tease = st.text_input("📈 Stocks to Tease (optional)")

    st.subheader("📰 Quotes or Recent News (optional)")
    quotes_news = st.text_area("Add quotes, stats, or timely news to reference")

    # ---------- Trait guide helper ----------
    def trait_guide(traits: dict) -> str:
        examples = {
            "Urgency":             "This isn't a drill — once midnight hits, your chance to secure these savings is gone forever.",
            "Data_Richness":       "Last year alone, our recommendations averaged returns 220% higher than the market average.",
            "Social_Proof":        "Thousands of investors trust Motley Fool every year to transform their financial future.",
            "Comparative_Framing": "Think back to those who seized early opportunities in the smartphone revolution.",
            "Imagery":             "When that switch flips, the next phase could accelerate even faster.",
            "Conversational_Tone": "Look — investing can feel complicated, but what if it didn't have to be?",
            "FOMO":                "Opportunities like these pass quickly — and regret can last forever.",
            "Repetition":          "This offer is for today only. Today only means exactly that: today only.",
        }
        return "\n".join(
            f"{i+1}. {name.replace('_',' ')} ({score}/10) — e.g., \"{examples[name]}\""
            for i, (name, score) in enumerate(traits.items())
        )

    # ---------- Copy structure ----------
    EMAIL_STRUCT = (
        "- Subject Line\n"
        "- Greeting\n"
        "- Body (benefits, urgency, proofs)\n"
        "- Clear call-to-action\n"
        "- Sign-off"
    )
    SALES_STRUCT = (
        "- Attention-grabbing Headline\n"
        "- Engaging Introduction\n"
        "- Bullets: key benefits/features\n"
        "- Detailed Body explaining offer & urgency\n"
        "- Strong call-to-action"
    )
    copy_structure = EMAIL_STRUCT if copy_type.startswith("📧") else SALES_STRUCT

    # ---------- Build prompt ----------
    def build_prompt(traits, brief, original_copy=None):
        edit_block = (
            f"\n\nYou are editing the EXISTING copy to reflect UPDATED trait intensities and new inputs."
            f"\n\n--- ORIGINAL COPY START ---\n{original_copy}\n--- ORIGINAL COPY END ---"
            if original_copy else ""
        )
        return (
            f"Produce a persuasive, engaging {copy_type.lower()} for the {brief['country']} market.\n"
            f"{COUNTRY_PROMPTS[brief['country']]}\n\n"
            "Trait intensities:\n" + trait_guide(traits) + "\n\n"
            "Structure exactly as:\n" + copy_structure + "\n\n"
            "Campaign Brief:\n"
            + line("Hook", brief["hook"])
            + line("Details", brief["details"])
            + line("Offer", f"Special {brief['offer_price']} (Retail {brief['retail_price']}), Term {brief['offer_term']}")
            + line("Reports", brief["reports"])
            + line("Stocks to Tease", brief["stocks_to_tease"])
            + line("Quotes/News", brief["quotes_news"])
            + f"\nDesired length: {length_choice}"
            + edit_block
            + "\n\nRespond ONLY with the "
            + copy_type.lower()
            + ", no commentary."
        ).strip()

    def aggregate_brief():
        return {
            "country": country,
            "hook": hook,
            "details": details,
            "offer_price": offer_price,
            "retail_price": retail_price,
            "offer_term": offer_term,
            "reports": reports,
            "stocks_to_tease": stocks_to_tease,
            "quotes_news": quotes_news,
        }

    # ---------- Generate & update ----------
    def do_generate():
        st.session_state.brief = aggregate_brief()
        st.session_state.last_traits = trait_scores.copy()
        with st.spinner("Generating copy…"):
            resp = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_BASE},
                    {"role": "system", "content": COUNTRY_PROMPTS[country]},
                    {"role": "assistant", "content": "Output ONLY the final copy; no meta explanations."},
                    {"role": "user", "content": build_prompt(trait_scores, st.session_state.brief)},
                ],
            )
        st.session_state.generated_copy = resp.choices[0].message.content.strip()

    def do_update():
        if not st.session_state.generated_copy:
            st.error("Generate copy first.")
            return
        st.session_state.brief = aggregate_brief()
        st.session_state.last_traits = trait_scores.copy()
        with st.spinner("Updating copy…"):
            resp = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_BASE},
                    {"role": "system", "content": COUNTRY_PROMPTS[country]},
                    {"role": "assistant", "content": "Adjust wording to match new trait intensities and inputs exactly."},
                    {
                        "role": "user",
                        "content": build_prompt(
                            trait_scores,
                            st.session_state.brief,
                            st.session_state.generated_copy,
                        ),
                    },
                ],
            )
        st.session_state.generated_copy = resp.choices[0].message.content.strip()
        st.success("✅ Copy updated!")

    # ---------- Buttons & display ----------
    if st.button("✨ Generate Marketing Copy"):
        do_generate()
    if trait_submit:
        do_update()

    if st.session_state.generated_copy:
        st.subheader("📝 Current Copy")
        st.markdown(st.session_state.generated_copy)

        g1, g2 = st.columns(2)
        if g1.button("💾 Save as DOCX"):
            doc = Document()
            doc.add_paragraph(st.session_state.generated_copy)
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button("📥 Download DOCX", buf, "motley_fool_copy.docx")
        if g2.button("🗑️ Clear / Reset"):
            for key in ("generated_copy", "brief", "last_traits"):
                st.session_state.pop(key, None)
            st.experimental_rerun()

# ============================================================
#  TAB 2 — Adapt Copy
# ============================================================
with tab_adapt:
    st.markdown("### Paste the original copy and select a **target country**.")
    original_text = st.text_area("Original Copy", height=250)

    colA, colB = st.columns(2)
    source_c = colA.selectbox("Original Country", list(COUNTRY_PROMPTS))
    target_c = colB.selectbox(
        "Target Country",
        [c for c in COUNTRY_PROMPTS if c != source_c]
    )

    if st.button("🌐 Adapt Copy"):
        if not original_text.strip():
            st.warning("Please paste the original copy.")
        else:
            with st.spinner("Adapting copy…"):
                resp = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_BASE},
                        {"role": "assistant", "content": "Output ONLY the adapted copy; no meta explanations."},
                        {
                            "role": "user",
                            "content": (
                                f"Adapt the following marketing copy from {source_c} for a {target_c} audience.\n"
                                "Update spelling, currency, and market references to match the target country. "
                                "Preserve tone, structure, and persuasive elements.\n\n"
                                "--- ORIGINAL COPY START ---\n"
                                f"{original_text}\n"
                                "--- ORIGINAL COPY END ---"
                            ),
                        },
                    ],
                )
            st.session_state.adapted_copy = resp.choices[0].message.content.strip()

    if st.session_state.adapted_copy:
        st.subheader("🌐 Adapted Copy")
        st.markdown(st.session_state.adapted_copy)

        a1, a2 = st.columns(2)
        if a1.button("💾 Save Adapted DOCX"):
            doc = Document()
            doc.add_paragraph(st.session_state.adapted_copy)
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button("📥 Download DOCX", buf, "mf_adapted_copy.docx")
        if a2.button("🗑️ Clear Adapted"):
            st.session_state.adapted_copy = ""
