import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def analyze_resume(resume_text):

    prompt = f"""
You are an expert HR recruiter.

Analyze the following resume.

Give the response exactly in this format.

Resume Score:
Strengths:
Weaknesses:
Missing Skills:
Suggestions:
Resume Summary:
Interview Questions:

Resume:

{resume_text}

"""

    response = model.generate_content(prompt)

    return response.text