# This code is designed to be run in a Streamlit environment.
# If you're running in a different environment, you may not have 'streamlit' available.
# To test logic without Streamlit, consider commenting out the Streamlit-specific lines.

import pandas as pd
from datetime import datetime
from typing import Dict

try:
    import streamlit as st

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
        if st.button("Generate Emails") and prompt:
            current_date = datetime(2025, 6, 6)
            results = []

            for _, row in users_df.iterrows():
                # Parse attributes
                org = row.get("Organization Name", "their organization")
                dept = row.get("Department", "their department")
                role = "Manager" if str(row.get("Manager", "")).strip().lower() == "yes" else "Individual Contributor"
                start_date = pd.to_datetime(row.get("Start Date", ""), errors='coerce')
                tenure = (current_date.year - start_date.year) * 12 + current_date.month - start_date.month if pd.notnull(start_date) else "N/A"

                # Simple generation logic (replace with GPT call or template matching as needed)
                subject = f"Explore {prompt} with your Bravely coach"
                preview = f"Coaching on {prompt} tailored to your role in {dept}"
                headline = f"Let's talk about {prompt}"
                body = (
                    f"At {org}, your role in {dept} as a {role} gives you unique opportunities and challenges."
                    f" With {tenure} months of experience, now is the perfect time to explore {prompt} in a coaching session."
                    "\n\n[BOOK A SESSION]\n\nA Bravely coach can help you navigate this topic with confidence and clarity."
                )

                results.append({
                    "Subject Line": subject,
                    "Preview Text": preview,
                    "Headline": headline,
                    "Body": body
                })

            emails_df = pd.DataFrame(results)
            st.write("Generated Emails:", emails_df)

            # Download option
            csv = emails_df.to_csv(index=False)
            st.download_button("Download Emails as CSV", data=csv, file_name="generated_emails.csv", mime="text/csv")
    else:
        st.info("Please upload a CSV file with user data to begin.")

except ModuleNotFoundError as e:
    print("Error: Streamlit is not installed. Please install it using 'pip install streamlit' and run this script with 'streamlit run filename.py'")

