import google.generativeai as genai

# Configure Gemini API
from dotenv import load_dotenv
import os

load_dotenv()

import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")


def evaluate_answers(questions, answers):

    prompt = """
You are a professional HR Interview Evaluator.

Evaluate the candidate professionally.

For EACH question provide:

1. Question
2. Candidate Answer
3. Score (out of 10)
4. Strengths
5. Areas for Improvement
6. Better Sample Answer

Finally provide:

Overall Score (out of 100)

Overall Performance:
- Communication
- Confidence
- Technical Understanding
- Professionalism

Final Suggestions:
Give 5 bullet-point suggestions.

Return ONLY plain text.

Do NOT use HTML.
Do NOT use CSS.
Do NOT use Markdown.
Do NOT use tags like:
<html>
<body>
<style>
<h1>
<h2>
<p>
<hr>
<strong>

Use this exact format:

==================================================
HR INTERVIEW EVALUATION REPORT
==================================================

Question 1

Question:
Candidate Answer:
Score:
Strengths:
Areas for Improvement:
Better Sample Answer:

--------------------------------------------------

Question 2

...

Overall Score:

Communication:

Confidence:

Technical Understanding:

Professionalism:

Final Suggestions:

• Suggestion 1
• Suggestion 2
• Suggestion 3
• Suggestion 4
• Suggestion 5

Evaluate ONLY the candidate answers provided.
Do NOT invent answers.
"""

    for i in range(len(questions)):

        if answers[i] == "NO_ANSWER":

            prompt += f"""

<hr>

<h3>Question {i+1}</h3>

<p><strong>Question:</strong> {questions[i]}</p>

<p><strong>Candidate Answer:</strong> No answer submitted.</p>

"""

        else:

            prompt += f"""

<hr>

<h3>Question {i+1}</h3>

<p><strong>Question:</strong> {questions[i]}</p>

<p><strong>Candidate Answer:</strong> {answers[i]}</p>

"""

    response = model.generate_content(prompt)

    import re

    response = model.generate_content(prompt)

    feedback = response.text

    match = re.search(r'Overall Score[:\s]*([0-9]+)', feedback)

    if match:
        score = match.group(1)
    else:
        score = "0"

    return {
        "score": score,
        "feedback": feedback
    }