from flask import Flask, render_template, request, url_for
import requests
from werkzeug.utils import secure_filename, redirect

app = Flask(__name__)

# Define BunnyCDN settings
REGION = 'jh'
STORAGE_ZONE_NAME = 'argon'
ACCESS_KEY = 'be2d7e90-3c7c-44c1-aea2f2288f88-391a-4ad1'
BASE_URL = f"https://{REGION}.storage.bunnycdn.com/{STORAGE_ZONE_NAME}/"

@app.route("/", methods=["GET"])
def render_upload_page():
    print(" i am in the first page ")
    return render_template("upload.html")

# Route for handling file upload and redirection
@app.route("/upload_video", methods=["POST"])
def upload_video():
    file = request.files["file"]
    filename_extension = secure_filename(file.filename)
    url = BASE_URL + filename_extension
    headers = {
        "AccessKey": ACCESS_KEY,
        "Content-Type": "application/octet-stream"
    }
    print(" iam tring to upload  it  ")
    response = requests.put(url, headers=headers, data=file.read())
    if response:
        video_url = "https://argon.b-cdn.net/"+filename_extension
        print(f"the vedio url is {video_url}")
        return redirect(url_for("render_success_page", video_url=video_url))
    else:
        return f"Failed to upload file: {response.text}"

# Route for rendering the success page
@app.route("/success", methods=["GET"])
def render_success_page():
    video_url = request.args.get("video_url")
    return render_template("success.html", video_url=video_url)

if __name__ == "__main__":
    app.run(debug=True)
