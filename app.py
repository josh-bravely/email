
import pandas as pd
from datetime import datetime
import time
from typing import Dict

try:
    import streamlit as st
    import openai

    # Simulate initial loading progress
    st.title("Bravely Personalized Email Generator")
    loading_bar = st.progress(0)
    status_text = st.empty()
    for i in range(20):
        time.sleep(0.05)
        loading_bar.progress((i + 1) / 20)
        status_text.text(f"Loading app... {int((i + 1) / 20 * 100)}%")
    loading_bar.empty()
    status_text.empty()

    # Set OpenAI API Key securely via Streamlit secrets
    if "openai_api_key" not in st.secrets:
        st.warning("OpenAI API key not found. Please add it to Streamlit secrets.")
    else:
        client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

        # Prompt input
        prompt = st.text_input("Enter an email topic (e.g., 'career growth', 'burnout', 'giving feedback')")

        # File upload
        uploaded_file = st.file_uploader("Upload a CSV of user data", type="csv")

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

                    coaching_themes = {
                        "New IC": "how to make a strong first impression, navigate early ambiguity, or start building relationships with the right people",
                        "Established IC": "giving and receiving feedback, managing up with more impact, or identifying growth opportunities aligned to your current goals",
                        "Veteran IC": "long-term career direction, navigating change at your org, or reclaiming motivation if things feel stagnant",
                        "New Manager": "building trust quickly with your new team, setting clear expectations, or aligning your leadership style to the company culture",
                        "Established Manager": "navigating feedback conversations, developing your team’s skills, or balancing strategic and reactive work",
                        "Veteran Manager": "scaling your leadership, supporting your team’s long-term growth, or staying energized as responsibilities increase"
                    }

                    with st.spinner("Generating emails..."):
                        for i, (_, row) in enumerate(users_df.iterrows()):
                            dept = row.get("Department", "their department")
                            role = "Manager" if str(row.get("Manager", "")).strip().lower() == "yes" else "Individual Contributor"
                            start_date = pd.to_datetime(row.get("Start Date", ""), errors='coerce')
                            tenure = (current_date.year - start_date.year) * 12 + current_date.month - start_date.month if pd.notnull(start_date) else 0
                            persona = get_persona(role, tenure)
                            themes = coaching_themes[persona]

                            user_context = (
                                f"Department: {dept}\n"
                                f"Role: {role}\n"
                                f"Tenure (months): {tenure}\n"
                                f"Persona: {persona}\n"
                                f"Their coaching needs may include: {themes}\n"
                                f"Topic: {prompt}"
                            )

                            system_prompt = (
                                "You are an expert email copywriter for Bravely, a coaching company."
                                " Your goal is to write a warm, empowering onboarding email for a user based on their role, tenure, department, and coaching topic."
                                " Structure the email in four parts:"
                                "\n1. Subject Line (short and impactful)"
                                "\n2. Preview Text (1 sentence that acts like an email teaser)"
                                "\n3. Headline (a punchy 3-6 word phrase)"
                                "\n4. Body (3 short paragraphs):"
                                "\n   - Start with a personalized intro about the user’s context"
                                "\n   - In the second paragraph, include a 3-bullet list of coaching suggestions with a varied lead-in like 'Partner with a coach to:', 'Your coach can help you:', etc."
                                "\n   - End with a sentence that begins with a phrase like “Book a session to…”, “Schedule a session to…”, or similar, followed by the [BOOK A SESSION] CTA on its own line"
                                " Tailor the tone based on whether the user is a manager or individual contributor."
                                " The tone should always be supportive, confidential, and helpful."
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

                                parsed = {}
                                current_section = None
                                buffer = []

                                for line in text.split("\n"):
                                    if ":" in line and line.index(":") < 40:
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

except ModuleNotFoundError as e:
    print("Error: Required module not found. Please run this in a Streamlit environment and ensure packages are installed.")
