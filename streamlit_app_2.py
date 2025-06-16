import streamlit as st
from openai import OpenAI
from io import BytesIO
from docx import Document


# API client setup
client = OpenAI(api_key=st.secrets.openai_api_key)

st.set_page_config(page_title="🚀 Motley Fool AI Copywriter")

st.title("🚀 Motley Fool AI Copywriter")

# Custom CSS to set consistent button width
st.markdown("""
<style>
div.stButton > button {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# Sidebar - Trait Intensity Controls
st.sidebar.header("🎚️ Trait Intensity")
trait_scores = {
    "Urgency": st.sidebar.slider("Urgency & Time Sensitivity", 1, 10, 8, key="urgency"),
    "Data-Richness": st.sidebar.slider("Data-Richness & Numerical Emphasis", 1, 10, 7, key="data_richness"),
    "Social Proof": st.sidebar.slider("Social Proof & Testimonials", 1, 10, 6, key="social_proof"),
    "Comparative Framing": st.sidebar.slider("Comparative Framing", 1, 10, 6, key="comparative_framing"),
    "Imagery": st.sidebar.slider("Imagery & Metaphors", 1, 10, 7, key="imagery"),
    "Conversational Tone": st.sidebar.slider("Conversational Tone", 1, 10, 8, key="conversational_tone"),
    "FOMO": st.sidebar.slider("FOMO (Fear of Missing Out)", 1, 10, 7, key="fomo"),
    "Repetition": st.sidebar.slider("Repetition for Emphasis", 1, 10, 5, key="repetition")
}

# Main App Controls
copy_type = st.selectbox("Select the type of marketing copy:", ["📧 Email", "📝 Sales Page"], key="copy_type")

length_choice = st.selectbox(
    "Select desired copy length:",
    ["📏 Short (100-200 words)", "📐 Medium (200-500 words)", "📖 Long (500-1500 words)", "📚 Extra Long (1500-5000 words)", "Scrolling Monster (5000+ words)"],
    key="length_choice"
)

st.subheader("Campaign Brief")
hook = st.text_area("🪝 Campaign Hook", placeholder="What's the main angle or hook of this campaign?", key="hook")
details = st.text_area("📦 Product/Offer Details", placeholder="What specifically is being sold/offered?", key="details")
reports = st.text_area("📑 Included Reports (if any)", placeholder="Are there any special reports or items included?", key="reports")

# Conditional instructions based on selected copy type
if copy_type == "📧 Email":
    copy_structure = """
    - Subject Line
    - Greeting
    - Body (persuasive content, urgency, clear benefits)
    - Clear call-to-action
    - Sign-off
    """
else:  # Sales Page
    copy_structure = """
    - Attention-grabbing Headline
    - Engaging Introduction
    - Bullet points listing key benefits/features
    - Detailed Body clearly explaining the offer, urgency, and benefits
    - Strong call-to-action
    """

# Initialize session state for generated copy
if 'generated_copy' not in st.session_state:
    st.session_state.generated_copy = ""

# Function to create prompt
def create_prompt(original_copy=None, editing=False):
    edit_instruction = f"\n\nYou are editing the existing copy below to reflect updated trait intensities. Keep the original structure but clearly incorporate the updated traits.\n\nOriginal copy:\n{original_copy}" if editing else ""

    prompt = f"""
You are an expert Motley Fool Australia copywriter. Write a complete, persuasive, engaging {copy_type.lower()} structured clearly with these explicitly defined linguistic traits. Follow the trait intensity (1-10 scale):

1. Urgency & Time Sensitivity ({trait_scores['Urgency']}/10):
- Example: "This isn't a drill — once midnight hits, your chance to secure these savings is gone forever."

2. Data-Richness & Numerical Emphasis ({trait_scores['Data-Richness']}/10):
- Example: "Last year alone, our recommendations averaged returns 220% higher than the market average."

3. Social Proof & Testimonials ({trait_scores['Social Proof']}/10):
- Example: "Thousands of investors trust Motley Fool’s recommendations each year to transform their financial future."

4. Comparative Framing ({trait_scores['Comparative Framing']}/10):
- Example: "Think back to those who seized early opportunities in the smartphone revolution. Today, you're looking at a similar transformative moment."

5. Imagery & Metaphors ({trait_scores['Imagery']}/10):
- Example: "When that switch flips, the next phase could accelerate even faster."

6. Conversational Tone ({trait_scores['Conversational Tone']}/10):
- Example: "Look — I know investing can feel complicated, but what if it didn't have to be? Let’s simplify it together."

7. Fear of Missing Out (FOMO) ({trait_scores['FOMO']}/10):
- Example: "Opportunities like these pass quickly — and regret can last forever. Will you seize this moment or risk missing out again?"

8. Repetition for Emphasis ({trait_scores['Repetition']}/10):
- Example: "This offer is for today only. Today only means exactly that: today only."

Additionally, explicitly channel legendary copywriting principles:
- David Ogilvy (clarity, simplicity, elegance)
- Joseph Sugarman (emotional storytelling, curiosity)
- Gary Halbert (direct-response persuasion, emotional triggers)
- Robert Cialdini (psychological persuasion: scarcity, authority, social proof)

Clearly structure your {copy_type.lower()} with these components: {copy_structure}

User's Campaign Brief explicitly provided:
- Campaign Hook: {hook}
- Product/Offer Details: {details}
- Included Reports: {reports}

Requested Length: {length_choice}{edit_instruction}

Provide ONLY the explicitly requested {copy_type.lower()} clearly structured as instructed, without repeating these instructions or using specific examples provided above verbatim.
"""
    return prompt

# Generate or update copy
if st.button("✨ Generate Marketing Copy"):
    with st.spinner('Generating persuasive Motley Fool marketing copy...'):
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": create_prompt()}]
        )
        st.session_state.generated_copy = response.choices[0].message.content.strip()

if st.session_state.generated_copy:
    st.subheader("✅ Generated Copy")
    st.markdown(st.session_state.generated_copy)

    col1, col2, col3 = st.columns(3)

    if col1.button("🔄 Update Copy with Adjusted Traits"):
        with st.spinner('Updating copy with adjusted traits...'):
            updated_response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": create_prompt(original_copy=st.session_state.generated_copy, editing=True)}]
            )
            st.session_state.generated_copy = updated_response.choices[0].message.content.strip()
            st.success("✅ Copy updated successfully!")

    if col2.button("💾 Save/Export as DOCX"):
        doc = Document()
        doc.add_paragraph(st.session_state.generated_copy)
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button(
            label="📥 Download DOCX",
            data=buffer,
            file_name="generated_copy.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    if col3.button("🗑️ Clear/Reset"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
