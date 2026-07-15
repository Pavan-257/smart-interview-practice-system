import google.generativeai as genai

from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(
    api_key=os.getenv("AQ.Ab8RN6IipCplWa_EltcRMUlrjuzegmsbaqOYJ5WrGOA1Njcttw")
)

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content("Say Hello")

print(response.text)