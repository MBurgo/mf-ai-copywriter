import streamlit as st
from openai import OpenAI
from io import BytesIO
from docx import Document

# ====== OpenAI client setup ======
client = OpenAI(api_key=st.secrets.openai_api_key)

# ====== Page setup ======
st.set_page_config(page_title="✍️ Motley Fool AI Copywriter")
st.title("✍️ Motley Fool AI Copywriter")

st.markdown("""
<style>
div.stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# ====== Session state initialization ======
def _init_state(**kwargs):
    for k, v in kwargs.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state(generated_copy="", brief=None, last_traits=None)

# ====== Rich System Prompt ======
SYSTEM_PROMPT = """
You are an expert Motley Fool Australia copywriter.

Voice: plain-English, transparent, optimistic, conversational, engaging, inclusive. Always use Australian spelling.

Incorporate proven copywriting principles when appropriate:
• David Ogilvy – clarity, simplicity, elegance
• Joseph Sugarman – emotional storytelling, curiosity
• Gary Halbert – direct-response persuasion, emotional triggers
• Robert Cialdini – scarcity, authority, social proof
"""

# ====== Sidebar Trait Intensity Controls ======
with st.sidebar.form(key="trait_form"):
    st.header("🎚️ Linguistic Trait Intensity")

    trait_scores = {
        "Urgency": st.slider("Urgency & Time Sensitivity", 1, 10, 8),
        "Data_Richness": st.slider("Data-Richness & Numerical Emphasis", 1, 10, 7),
        "Social_Proof": st.slider("Social Proof & Testimonials", 1, 10, 6),
        "Comparative_Framing": st.slider("Comparative Framing", 1, 10, 6),
        "Imagery": st.slider("Imagery & Metaphors", 1, 10, 7),
        "Conversational_Tone": st.slider("Conversational Tone", 1, 10, 8),
        "FOMO": st.slider("FOMO (Fear of Missing Out)", 1, 10, 7),
        "Repetition": st.slider("Repetition for Emphasis", 1, 10, 5),
    }

    trait_submit = st.form_submit_button("🔄 Update Copy with Adjusted Traits")

# ====== Main-panel inputs ======
copy_type = st.selectbox("Select the type of marketing copy:", ["📧 Email", "📝 Sales Page"])

length_choice = st.selectbox("Select desired copy length:", [
    "📏 Short (100-200 words)",
    "📐 Medium (200-500 words)",
    "📖 Long (500-1500 words)",
    "📚 Extra Long (1500-3000 words)",
    "📜 Scrolling Monster (3000+ words)",
])

st.subheader("Campaign Brief")
hook = st.text_area("🪝 Campaign Hook")
details = st.text_area("📦 Product/Offer Details")
reports = st.text_area("📑 Included Reports (if any)")

# ====== Copy structure templates ======
email_structure = """
- Subject Line
- Greeting
- Body (persuasive content, urgency, clear benefits)
- Clear call-to-action
- Sign-off
"""

sales_structure = """
- Attention-grabbing Headline
- Engaging Introduction
- Bullet points listing key benefits/features
- Detailed Body clearly explaining offer, urgency, benefits
- Strong call-to-action
"""

copy_structure = email_structure if copy_type == "📧 Email" else sales_structure

# ====== Trait definitions with examples ======
def build_trait_guide(traits):
    return f"""
1. Urgency ({traits['Urgency']}/10) — e.g., "This isn't a drill — once midnight hits, your chance to secure these savings is gone forever."
2. Data-Richness ({traits['Data_Richness']}/10) — e.g., "Last year alone, our recommendations averaged returns 220% higher than the market average."
3. Social Proof ({traits['Social_Proof']}/10) — e.g., "Thousands of investors trust Motley Fool’s recommendations each year to transform their financial future."
4. Comparative Framing ({traits['Comparative_Framing']}/10) — e.g., "Think back to those who seized early opportunities in the smartphone revolution. Today, you're looking at a similar transformative moment."
5. Imagery ({traits['Imagery']}/10) — e.g., "When that switch flips, the next phase could accelerate even faster."
6. Conversational Tone ({traits['Conversational_Tone']}/10) — e.g., "Look — I know investing can feel complicated, but what if it didn't have to be? Let’s simplify it together."
7. FOMO ({traits['FOMO']}/10) — e.g., "Opportunities like these pass quickly — and regret can last forever. Will you seize this moment or risk missing out again?"
8. Repetition ({traits['Repetition']}/10) — e.g., "This offer is for today only. Today only means exactly that: today only."
"""

# ====== Prompt builder ======
def build_prompt(traits, brief, original_copy=None):
    edit_instruction = ""
    if original_copy:
        edit_instruction = (
            "\n\nYou are editing the existing copy below to reflect the UPDATED trait intensities. "
            "Maintain structure, enhance traits clearly.\n\n"
            f"--- ORIGINAL COPY START ---\n{original_copy}\n--- ORIGINAL COPY END ---"
        )

    return f"""
Produce a persuasive, engaging {copy_type.lower()}.

Trait intensities:
{build_trait_guide(traits)}

Structure exactly as follows:
{copy_structure}

Campaign Brief:
- Hook: {brief['hook']}
- Details: {brief['details']}
- Reports: {brief['reports']}

Desired length: {length_choice}{edit_instruction}

Respond ONLY with the requested {copy_type.lower()}, no commentary.
""".strip()

# ====== Generate Copy function ======
def do_generate():
    st.session_state.brief = {"hook": hook, "details": details, "reports": reports}
    st.session_state.last_traits = trait_scores.copy()

    with st.spinner("Generating copy..."):
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "Output ONLY the final copy; no meta explanations."},
                {"role": "user", "content": build_prompt(trait_scores, st.session_state.brief)},
            ],
        )
    st.session_state.generated_copy = resp.choices[0].message.content.strip()

if st.button("✨ Generate Marketing Copy"):
    do_generate()

# ====== Update Copy function ======
def do_update():
    if not st.session_state.brief or not st.session_state.generated_copy:
        st.error("Generate copy first, then update traits.")
        return

    if trait_scores == st.session_state.last_traits:
        st.warning("Traits unchanged since last update.")
        return

    st.session_state.last_traits = trait_scores.copy()

    with st.spinner("Updating copy with adjusted traits..."):
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "Adjust wording to match new trait intensities exactly."},
                {"role": "user", "content": build_prompt(trait_scores, st.session_state.brief, st.session_state.generated_copy)},
            ],
        )
    st.session_state.generated_copy = resp.choices[0].message.content.strip()
    st.success("✅ Copy updated!")

if trait_submit:
    do_update()

# ====== Display and action buttons ======
if st.session_state.generated_copy:
    st.subheader("📝 Current Copy")
    st.markdown(st.session_state.generated_copy)

    col1, col2 = st.columns(2)

    if col1.button("💾 Save as DOCX"):
        doc = Document()
        doc.add_paragraph(st.session_state.generated_copy)
        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        st.download_button("📥 Download DOCX", buf, "motley_fool_copy.docx")

    if col2.button("🗑️ Clear / Reset"):
        for k in ("generated_copy", "brief", "last_traits"):
            st.session_state.pop(k, None)
        st.experimental_rerun()
