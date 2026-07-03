import google.generativeai as genai

# Configure Gemini API
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Load Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")


def evaluate_answers(questions, answers):

    prompt = """
You are a professional HR Interview Evaluator.

Evaluate the candidate professionally.

For EACH question:

1. Question
2. Candidate Answer
3. Score (out of 10)
4. Strengths
5. Areas for Improvement
6. Better Sample Answer

After evaluating all 10 answers provide:

Overall Score (out of 100)

Overall Performance:
- Communication
- Confidence
- Technical Understanding
- Professionalism

Final Suggestions:
Give 5 bullet-point suggestions for improving interview performance.

Return the response in proper HTML using:
<h2>, <h3>, <p>, <ul>, <li>, <strong>, <hr>

Do NOT use markdown symbols like ** or ###.
"""

    for i in range(len(questions)):
        prompt += f"""

<hr>

<h3>Question {i+1}</h3>

<p><strong>Question:</strong> {questions[i]}</p>

<p><strong>Candidate Answer:</strong> {answers[i]}</p>

"""

    response = model.generate_content(prompt)

    return {
        "score": "AI Evaluated",
        "feedback": response.text
    }