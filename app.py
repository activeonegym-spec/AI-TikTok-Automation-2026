
import os
import secrets
import requests
from flask import Flask, redirect, request, session

app = Flask(__name__)
app.secret_key = os.environ["SESSION_SECRET"]

CLIENT_KEY = os.environ["TIKTOK_CLIENT_KEY"]
CLIENT_SECRET = os.environ["TIKTOK_CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]

@app.route("/")
def home():
    return '<h2>StoryFlow AI</h2><a href="/oauth">Connect TikTok</a>'

@app.route("/oauth")
def oauth():
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    params = {
        "client_key": CLIENT_KEY,
        "response_type": "code",
        "scope": "user.info.basic",
        "redirect_uri": REDIRECT_URI,
        "state": state
    }

    from urllib.parse import urlencode
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urlencode(params)
    return redirect(url)

@app.route("/auth/callback")
def callback():
    if request.args.get("error"):
        return "TikTok authorization failed: " + request.args.get("error_description", "")

    state = request.args.get("state")
    if not state or state != session.get("oauth_state"):
        return "Security check failed. Please try again."

    code = request.args.get("code")
    if not code:
        return "Authorization code missing."

    response = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        return "Token exchange failed. Please check server settings."

    data = response.json()
    if "access_token" not in data:
        return "TikTok did not return an access token."

    return "TikTok connected successfully! Token received securely by server."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
