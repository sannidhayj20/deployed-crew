api_key = "AIzaSyAz2ebIcVe9EN_SU-CB-n3wTstCqg-R4t8"
import google.generativeai as genai
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content("How does AI work?")
print(response.text)