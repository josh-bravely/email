import pandas as pd
from datetime import datetime
from typing import Dict

try:
    import streamlit as st
    import openai

    # Set OpenAI API Key securely via Streamlit secrets
    if "openai_api_key" not in st.secrets:
        st.warning("OpenAI API key not found. Please add it to Streamlit secrets.")
    else:
        client = openai.OpenAI(api_key=st.secrets["openai_api_key"])

        # Title
        st.title("Bravely Personalized Email Generator")

        # Prompt input
        prompt = st.text_input("Enter an email topic (e.g., 'career growth', 'burnout', 'giving feedback')")

        # File upload
        uploaded_file = st.file_uploader("Upload a CSV of user data", type="csv")

        # Load user data
        if uploaded_file:
            users_df = pd.read_csv(uploaded_file)
            st.write("User data preview:", users_df.head())

            # Generate emails on button click
            if st.button("Generate Emails"):
                if not prompt.strip():
                    st.warning("Please enter a topic prompt before generating emails.")
                else:
                    current_date = datetime(2025, 6, 6)
                    results = []

                    for _, row in users_df.iterrows():
                        org = row.get("Organization Name", "their organization")
                        dept = row.get("Department", "their department")
                        role = "Manager" if str(row.get("Manager", "")).strip().lower() == "yes" else "Individual Contributor"
                        start_date = pd.to_datetime(row.get("Start Date", ""), errors='coerce')
                        tenure = (current_date.year - start_date.year) * 12 + current_date.month - start_date.month if pd.notnull(start_date) else "N/A"

                        user_context = (
                            f"Organization: {org}\n"
                            f"Department: {dept}\n"
                            f"Role: {role}\n"
                            f"Tenure (months): {tenure}\n"
                            f"Topic: {prompt}"
                        )

                        system_prompt = (
                            "You are an expert email copywriter for Bravely, a coaching company."
                            " Write a professional onboarding email for a user, broken into four parts:"
                            " Subject Line, Preview Text, Headline, and Body."
                            " Make it personalized based on the user's role, organization, department, and tenure."
                            " Keep the tone supportive, clear, and aligned with Bravely’s brand."
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
                            lines = [line for line in text.split("\n") if ":" in line]

                            if not lines:
                                st.error("GPT response was malformed or empty.")
                                results.append({
                                    "Subject Line": "ERROR",
                                    "Preview Text": "ERROR",
                                    "Headline": "ERROR",
                                    "Body": text
                                })
                                continue

                            parsed = {k.strip(): v.strip() for k, v in [line.split(":", 1) for line in lines]}

                            results.append({
                                "Subject Line": parsed.get("Subject Line", ""),
                                "Preview Text": parsed.get("Preview Text", ""),
                                "Headline": parsed.get("Headline", ""),
                                "Body": parsed.get("Body", text)
                            })

                        except Exception as e:
                            st.error(f"Error generating email: {e}")
                            results.append({
                                "Subject Line": "ERROR",
                                "Preview Text": "ERROR",
                                "Headline": "ERROR",
                                "Body": f"Failed to generate email: {str(e)}"
                            })

                    if results:
                        emails_df = pd.DataFrame(results)
                        st.write("Generated Emails:", emails_df)
                        csv = emails_df.to_csv(index=False)
                        st.download_button("Download Emails as CSV", data=csv, file_name="generated_emails.csv", mime="text/csv")

        else:
            st.info("Please upload a CSV file with user data to begin.")

except ModuleNotFoundError as e:
    print("Error: Required module not found. Please run this in a Streamlit environment and ensure packages are installed.")
