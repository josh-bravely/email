
import pandas as pd
from datetime import datetime
import time
import streamlit as st
import openai

# Set OpenAI API Key securely via Streamlit secrets
if "openai_api_key" not in st.secrets:
    st.warning("OpenAI API key not found. Please add it to Streamlit secrets.")
else:
    client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

    # UI: Title, prompt input, and file upload
    st.title("Bravely Personalized Email Generator")
    prompt = st.text_input("Enter an email topic (e.g., 'career growth', 'burnout', 'giving feedback')")
    uploaded_file = st.file_uploader("Upload a CSV of user data", type="csv")

    # Department-specific context map
    department_context_map = {
        "Sales": "In Sales, people often face pressure to perform, meet shifting targets, and lead persuasive conversations under time constraints.",
        "Engineering": "In Engineering, challenges often include solving complex problems, working through unclear requirements, and communicating across technical boundaries.",
        "Marketing": "In Marketing, priorities shift quickly, requiring clarity, creativity, and alignment across stakeholders.",
        "HR": "In HR, balancing empathy with accountability, managing sensitive conversations, and supporting others is a constant responsibility.",
        "Customer Success": "In Customer Success, success often hinges on balancing client relationships, solving unexpected issues, and staying proactive.",
        "Product": "In Product, it’s about aligning diverse needs, making tradeoffs, and navigating strategic ambiguity."
    }

    # Persona logic
    def get_persona(role: str, tenure: int) -> str:
        if role == "Manager":
            if tenure < 6:
                return "New Manager"
            elif tenure < 24:
                return "Established Manager"
            else:
                return "Veteran Manager"
        else:
            if tenure < 6:
                return "New IC"
            elif tenure < 24:
                return "Established IC"
            else:
                return "Veteran IC"

    # Coaching themes by persona
    coaching_themes = {
        "New IC": "how to make a strong first impression, navigate early ambiguity, or start building relationships with the right people",
        "Established IC": "giving and receiving feedback, managing up with more impact, or identifying growth opportunities aligned to your current goals",
        "Veteran IC": "long-term career direction, navigating change at your org, or reclaiming motivation if things feel stagnant",
        "New Manager": "building trust quickly with your new team, setting clear expectations, or aligning your leadership style to the company culture",
        "Established Manager": "navigating feedback conversations, developing your team’s skills, or balancing strategic and reactive work",
        "Veteran Manager": "scaling your leadership, supporting your team’s long-term growth, or staying energized as responsibilities increase"
    }

    # Finalized system prompt
    system_prompt = """You are an expert email copywriter for Bravely, a coaching company.
Your goal is to write a warm, empowering onboarding email for a user based on their role, tenure, department, and coaching topic.
Structure the email in four parts:
1. Subject Line (short and impactful)
2. Preview Text (1 sentence that acts like an email teaser)
3. Headline (a punchy 3–6 word phrase)
4. Body (3 short paragraphs):
   - Start with a personalized intro that reflects the user’s department context and ambitions
   - Include a 3-bullet list of coaching suggestions with a varied lead-in (e.g., “Your coach can help you:”)
   - End with a motivating line like “Book a session to…” followed by [BOOK A SESSION] on its own line.
Do not include the user’s organization name.
Tailor the tone based on whether the user is a manager or individual contributor.
The tone should always be clear, strategic, supportive, and grounded."""

    # Email generation logic
    if uploaded_file:
        users_df = pd.read_csv(uploaded_file)
        st.write("User data preview:", users_df.head())

        if st.button("Generate Emails"):
            if not prompt.strip():
                st.warning("Please enter a topic prompt before generating emails.")
            else:
                current_date = datetime(2025, 6, 6)
                results = []
                total_users = len(users_df)
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, (_, row) in enumerate(users_df.iterrows()):
                    dept = row.get("Department", "their department")
                    role = "Manager" if str(row.get("Manager", "")).strip().lower() == "yes" else "Individual Contributor"
                    start_date = pd.to_datetime(row.get("Start Date", ""), errors='coerce')
                    tenure = (current_date.year - start_date.year) * 12 + current_date.month - start_date.month if pd.notnull(start_date) else 0
                    persona = get_persona(role, tenure)
                    themes = coaching_themes[persona]
                    dept_context = department_context_map.get(dept, "")

                    user_context = (
                        f"Department: {dept}\n"
                        f"Role: {role}\n"
                        f"Tenure (months): {tenure}\n"
                        f"Persona: {persona}\n"
                        f"Their coaching needs may include: {themes}\n"
                        f"Topic: {prompt}\n"
                        f"{dept_context}"
                    )

                    user_prompt = (
                        f"Here is the user's information:\n{user_context}\n\n"
                        "Write the personalized email."
                    )

                    try:
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ]
                        )

                        text = response.choices[0].message.content

                        # Simple section parser
                        parsed = {}
                        current_section = None
                        buffer = []
                        for line in text.split("\n"):
                            if ":" in line and any(h in line.lower() for h in ["subject line", "preview text", "headline", "body"]):
                                if current_section:
                                    parsed[current_section] = "\n".join(buffer).strip()
                                key, val = line.split(":", 1)
                                current_section = key.strip()
                                buffer = [val.strip()]
                            elif current_section:
                                buffer.append(line.strip())
                        if current_section:
                            parsed[current_section] = "\n".join(buffer).strip()

                        results.append({
                            "Subject Line": parsed.get("Subject Line", ""),
                            "Preview Text": parsed.get("Preview Text", ""),
                            "Headline": parsed.get("Headline", ""),
                            "Body": parsed.get("Body", text)
                        })

                    except Exception as e:
                        results.append({
                            "Subject Line": "ERROR",
                            "Preview Text": "ERROR",
                            "Headline": "ERROR",
                            "Body": f"Failed to generate email: {str(e)}"
                        })

                    progress_bar.progress((i + 1) / total_users)
                    status_text.text(f"Generating email {i + 1} of {total_users}...")

                progress_bar.empty()
                status_text.empty()

                if results:
                    st.success("Email generation complete.")
                    emails_df = pd.DataFrame(results)
                    st.write("Generated Emails:", emails_df)
                    csv = emails_df.to_csv(index=False)
                    st.download_button("Download Emails as CSV", data=csv, file_name="generated_emails.csv", mime="text/csv")
    else:
        st.info("Please upload a CSV file with user data to begin.")
