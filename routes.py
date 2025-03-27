# routes.py
from flask import Blueprint, request, jsonify
import openai

# openai.api_key = "your-api-key"  # or use os.environ.get("OPENAI_API_KEY")

routes = Blueprint("routes", __name__)

@routes.route("/generate-plan", methods=["POST"])
def generate_plan():
    data = request.get_json()
    classes = data.get("classes", [])
    deadlines = data.get("deadlines", {})
    availability = data.get("availability", {})

    prompt = f"""
    Create a personalized weekly study plan for the following:
    Classes: {classes}
    Deadlines: {deadlines}
    Availability: {availability}
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify({"plan": response["choices"][0]["message"]["content"]})
