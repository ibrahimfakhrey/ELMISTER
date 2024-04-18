import os
import uuid
from datetime import datetime

import requests
from flask import Flask, render_template, request, redirect, current_app, flash, url_for, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship

from werkzeug.security import generate_password_hash, check_password_hash

from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_babel import Babel
from datetime import date, datetime

from werkzeug.utils import secure_filename


app = Flask(__name__)

babel = Babel(app)


login_manager = LoginManager()
login_manager.init_app(app)

import os

# Define the path to the upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploadedfiles')

# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Set the configuration variable
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@login_manager.user_loader
def load_user(user_id):
    # Check if user is in paid_user table
    user = User.query.get(int(user_id))
    if user:
        return user
    return None


# Define BunnyCDN settings
REGION = 'jh'
STORAGE_ZONE_NAME = 'argon'
ACCESS_KEY = 'be2d7e90-3c7c-44c1-aea2f2288f88-391a-4ad1'
BASE_URL = f"https://{REGION}.storage.bunnycdn.com/{STORAGE_ZONE_NAME}/"

app.config['BABEL_DEFAULT_LOCALE'] = 'en'

app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    purchases = db.Table(
        'purchases',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
        db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
    )


    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100), unique=True)
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))
        email = db.Column(db.String(100))
        country = db.Column(db.String(100))
        subscription = db.Column(db.String(100))
        credit = db.Column(db.Integer)
        role = db.Column(db.String(100), default="user")
        pay = db.Column(db.Boolean(), default=False)
        message = db.Column(db.String(1000))
        starting_day = db.Column(db.DateTime)
        due_date = db.Column(db.DateTime)
        delegate = db.Column(db.DateTime)
        photo_filename = db.Column(db.String(1000))
        courses = db.relationship('Course', secondary=purchases, backref='purchasers', lazy='dynamic')
        purchased_courses = db.relationship('Course', secondary=purchases, backref='purchased_by_users', lazy='dynamic')
        purchase_history = db.relationship('PurchaseHistory', backref='user', lazy=True)


    class PurchaseHistory(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
        purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
        price = db.Column(db.Float)


    class TB(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100), unique=True)
        name = db.Column(db.String(1000))
        email = db.Column(db.String(100))
        description = db.Column(db.String(1000))
        sample = db.Column(db.String(100))
        approved = db.Column(db.Boolean(), default=False)
        teacher_photo = db.Column(db.String(255))

        def save_profile_photo(self, photo_file):
            filename = secure_filename(photo_file.filename)
            uploads_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(uploads_folder):
                os.makedirs(uploads_folder)
            unique_filename = str(uuid.uuid4()) + '_' + filename
            photo_path = os.path.join(uploads_folder, unique_filename)
            photo_file.save(photo_path)
            self.teacher_photo = unique_filename
            db.session.commit()


    class Teacher(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        phone = db.Column(db.String(100), unique=True)
        password = db.Column(db.String(100))
        name = db.Column(db.String(1000))
        email = db.Column(db.String(100))
        rating = db.Column(db.Integer)
        teacher_photo = db.Column(db.String(255))
        courses = db.relationship('Course', back_populates='teacher', lazy=True)
        videos = db.relationship('Video', backref='teacher', lazy=True)
        credit = db.Column(db.Integer, default=0)
        credit_taken = db.Column(db.Integer, default=0)

        def save_profile_photo(self, photo_file):
            filename = secure_filename(photo_file.filename)
            uploads_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(uploads_folder):
                os.makedirs(uploads_folder)
            unique_filename = str(uuid.uuid4()) + '_' + filename
            photo_path = os.path.join(uploads_folder, unique_filename)
            photo_file.save(photo_path)
            self.teacher_photo = unique_filename
            db.session.commit()


    class Course(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        price = db.Column(db.Float)
        discount = db.Column(db.Integer)
        teacher_name = db.Column(db.String(100))
        description = db.Column(db.String(1000))
        sample = db.Column(db.String(100))
        grade = db.Column(db.String(100))
        section = db.Column(db.String(100))
        type = db.Column(db.String(100))
        country = db.Column(db.String(100))
        name = db.Column(db.String(100), nullable=False)
        course_image = db.Column(db.String(255))
        approved = db.Column(db.Boolean(), default=False)
        online_start_time = db.Column(DateTime)  # Added column for online start time
        online_end_time = db.Column(DateTime)  # Added column for online end time
        online_date = db.Column(db.Date)  # Added column for online date
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
        teacher = db.relationship('Teacher', back_populates='courses', lazy=True)
        lessons = relationship('Lesson', backref='course', lazy=True)

        def __init__(self, name, teacher_name, description, grade, discount, sample, course_image, teacher_id, section,
                     type,
                     online_start_time=None):
            self.name = name
            self.teacher_name = teacher_name
            self.description = description
            self.grade = grade
            self.discount = discount
            self.sample = sample
            self.course_image = course_image
            self.teacher_id = teacher_id
            self.type = type
            self.section = section
            self.online_start_time = online_start_time

        def save_profile_photo(self, photo_file):
            filename = secure_filename(photo_file.filename)
            uploads_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(uploads_folder):
                os.makedirs(uploads_folder)
            unique_filename = str(uuid.uuid4()) + '_' + filename
            photo_path = os.path.join(uploads_folder, unique_filename)
            photo_file.save(photo_path)
            self.course_image = unique_filename
            db.session.commit()


    class LessonFileAssociation(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
        file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)

        lesson = db.relationship('Lesson', backref='file_associations')
        file = db.relationship('File', backref='lesson_associations')

        def __init__(self, lesson_id, file_id):
            self.lesson_id = lesson_id
            self.file_id = file_id


    class Lesson(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100))
        content = db.Column(db.String(1000))
        course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))

        # Define the relationship with the video table
        videos = db.relationship('Video', secondary='lesson_video_association', lazy='subquery',
                                 backref=db.backref('lessons', lazy=True))

        # Define the relationship with the file table
        files = db.relationship('File', secondary='lesson_file_association', lazy='subquery',
                                backref=db.backref('lessons', lazy=True))

        def __init__(self, title, content, course_id, teacher_id):
            self.title = title
            self.content = content
            self.course_id = course_id
            self.teacher_id = teacher_id


    class File(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100))
        description = db.Column(db.String(1000))
        path = db.Column(db.String(255))
        is_free = db.Column(db.Boolean, default=True)
        price = db.Column(db.Float)
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
        teacher = db.relationship('Teacher', backref='files')

        def __init__(self, name, description, teacher_id, path, is_free=True, price=None, teacher=None):
            self.name = name
            self.description = description
            self.path = path
            self.teacher_id = teacher_id
            self.is_free = is_free
            self.price = price
            if teacher:
                self.teacher = teacher


    class Video(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=True)
        link = db.Column(db.String(1000))
        teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
        unit_test = db.Column(db.String(100))

        def __init__(self, title, link, teacher_id, unit_test=None):
            self.title = title
            self.link = link
            self.teacher_id = teacher_id
            self.unit_test = unit_test


    # Define the association table after defining the Lesson and Video classes
    class LessonVideoAssociation(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
        video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

        lesson = db.relationship('Lesson', backref='video_associations')
        video = db.relationship('Video', backref='lesson_associations')

        def __init__(self, lesson_id, video_id):
            self.lesson_id = lesson_id
            self.video_id = video_id


    db.create_all()


class MyModelView(ModelView):
    def is_accessible(self):
        return True


admin = Admin(app)
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Course, db.session))
admin.add_view(MyModelView(Teacher, db.session))
admin.add_view(MyModelView(Video, db.session))
admin.add_view(MyModelView(TB, db.session))
admin.add_view(MyModelView(Lesson, db.session))
admin.add_view(MyModelView(File, db.session))



today = datetime.today()


@app.route("/")
def start():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        email = request.form.get("email")
        user = User.query.filter_by(phone=phone).first()
        if user:
            return "you are regitserd with us "
        new_user = User(phone=phone, name=name, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()
        return "user created "
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        phone = request.form.get("phone")
        password = request.form.get('password')

        email = request.form.get("email")
        if phone:
            user = User.query.filter_by(phone=phone).first()
        else:
            user = User.query.filter_by(email=email).first()

        if not user:
            return render_template("login.html", message=" you are not registered ")

        if not check_password_hash(user.password, password):
            return render_template("login.html", message=" password is incorrect ")

        else:
            login_user(user)

            return redirect("/dash")

    return render_template("login.html")


@app.route("/dash")
def dash():
    if current_user.is_authenticated and current_user.role == "user":
        today_date = date.today().strftime("%B, %d")
        return render_template("dash.html", date=today_date)
    if current_user.is_authenticated and current_user.role == "teacher":
        teacher = Teacher.query.filter_by(phone=current_user.phone).first()

        teacher_courses = Course.query.filter_by(teacher_id=teacher.id).all()

        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/dash.html", teacher_courses=teacher_courses, teacher=teacher)
    else:
        return "somthing went wrong"


@app.route("/quizes")
def quizes():
    if current_user.is_authenticated and current_user.role == "teacher":
        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/projects.html")


@app.route("/students")
def students():
    if current_user.is_authenticated and current_user.role == "teacher":
        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/friends.html")


@app.route("/all_courses")
def all_courses():
    if current_user.is_authenticated and current_user.role == "user":
        today_date = date.today().strftime("%B, %d")
        return render_template("courses.html", date=today_date)
    if current_user.is_authenticated and current_user.role == "teacher":
        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/courses.html", date=today_date)
    else:
        return "somthing went wrong"


@app.route("/profile")
def profile():
    if current_user.is_authenticated and current_user.role == "user":
        today_date = date.today().strftime("%B, %d")
        return render_template("profile.html", date=today_date)
    if current_user.is_authenticated and current_user.role == "teacher":
        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/profile.html", date=today_date)


@app.route("/setting")
def setting():
    if current_user.is_authenticated and current_user.role == "user":
        today_date = date.today().strftime("%B, %d")
        return render_template("settings.html", date=today_date)
    if current_user.is_authenticated and current_user.role == "teacher":
        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/settings.html", date=today_date)


@app.route("/course")
def course():
    return render_template("course_description.html")


@app.route("/creat_course", methods=["GET", "POST"])
def creat_course():
    if current_user.is_authenticated and current_user.role == "teacher":
        if request.method == "POST":
            course_name = request.form.get("name")
            course_grade = request.form.get("grade")
            section = request.form.get("section")
            description = request.form.get("description")
            course_type = request.form.get("type")
            online_start_time = None
            online_end_time = None
            online_date = None
            photo_file = request.files['image']

            # Default values for discount and sample
            default_discount = 0  # Set to your desired default value
            default_sample = "Sample text"  # Set to your desired default value

            # Validate file upload
            if photo_file:
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                filename = secure_filename(photo_file.filename)
                if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Create a new teacher
                    teacher = Teacher.query.filter_by(phone=current_user.phone).first()

                    # Create a new course with default values for discount and sample
                    new_course = Course(
                        name=course_name,
                        teacher_name=teacher.name,
                        description=description,
                        grade=course_grade,
                        section=section,
                        discount=default_discount,
                        sample=default_sample,
                        course_image=None,
                        teacher_id=teacher.id,
                        type=course_type,
                        online_start_time=online_start_time
                    )

                    # Add the new course to the database
                    db.session.add(new_course)
                    db.session.commit()

                    # Call the method to save the course image
                    new_course.save_profile_photo(photo_file)

                    flash("Course created successfully")
                    return redirect(url_for("dash"))

                else:
                    flash("Invalid file format for course photo")
                    return redirect(url_for("creat_course"))

        return render_template("teacher/creat_course.html")
    else:
        return "you are not a teacher"


@app.route("/creat_quiz")
def creat_quiz():
    if current_user.is_authenticated and current_user.role == "teacher":
        today_date = date.today().strftime("%B, %d")
        return render_template("teacher/quiz.html")
    else:
        return "you are not teacher"


@app.route("/maketeacher/<int:teacher_phone>")
def make_teacher(teacher_phone):
    t = User.query.filter_by(phone=teacher_phone).first()
    if t:
        new_teacher = Teacher(
            name=t.name, phone=t.phone, email=t.email
        )
        db.session.add(new_teacher)
        db.session.commit()
        return "done"
    else:
        return "not found"


@app.route("/add_lesson")
def add_lesson():
    teacher = Teacher.query.filter_by(phone=current_user.phone).first()

    return render_template("teacher/redirecting.html", teacher=teacher)


@app.route("/upload", methods=["POST", "GET"])
def upload():
    if request.method == "POST":
        lesson_id = request.form.get('lesson-select')
        lesson_name = request.form.get('lesson_name')
        type = request.form.get('type')
        if type == "v":
            print(f"iam in d  upload{lesson_name}")
            return redirect(url_for('add_video', lesson_id=lesson_id,lesson_name=lesson_name))
        if type == "f":
            print(f"iam in d  upload file {lesson_name}")
            return redirect(url_for('upload_file', lesson_id=lesson_id,lesson_name=lesson_name))
        return "done"


@app.route("/add_video")
def add_video():
    lesson_id = request.args.get('lesson_id')
    lesson_name = request.args.get('lesson_name')
    print(f"iam in e upload{lesson_name}")
    return render_template("upload.html", lesson_id=lesson_id,lesson_name=lesson_name)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=["GET","POST"])
def upload_file():
    lesson_id = request.args.get('lesson_id')
    lesson_name = request.args.get('lesson_name')
    course=Course.query.filter_by(id=lesson_id).first()
    print(f"iam in e upload file {lesson_name}")

    # Check if the post request has the file part
    if request.method=="POST":

        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']

        # If user does not select file, browser also submit an empty part without filename
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Create a new File instance and add it to the database
            new_file = File(
                name=request.form.get('name'),
                description=request.form.get('description'),
                path=os.path.join(app.config['UPLOAD_FOLDER'], filename),
                teacher_id=request.form.get('teacher_id')
            )
            db.session.add(new_file)
            db.session.commit()

            # Associate the file with the specified lesson
            lesson_id = request.form.get('lesson_id')
            lesson = Lesson.query.get(lesson_id)
            if lesson:
                lesson_file_association = LessonFileAssociation(lesson_id=lesson.id, file_id=new_file.id)
                db.session.add(lesson_file_association)
                db.session.commit()

            return jsonify({'message': 'File uploaded successfully'}), 200

        return jsonify({'error': 'Invalid file format'}), 400
    return render_template("teacher/upload_file.html",course=course)

# Route for handling file upload and redirection




@app.route("/upload_video/<lesson_id>/<lesson_name>", methods=["POST"])
def upload_video(lesson_id,lesson_name):
    file = request.files["file"]
    print(f"iam in dd  upload{lesson_name}")

    # Get the course/lesson by its ID
    course = Course.query.filter_by(id=lesson_id).first()

    if course:
        # Upload the video file and get the video URL
        filename_extension = secure_filename(file.filename)
        url = BASE_URL + filename_extension
        headers = {
            "AccessKey": ACCESS_KEY,
            "Content-Type": "application/octet-stream"
        }
        print("I am trying to upload it ")

        # Dummy response for testing
        response = requests.put(url, headers=headers, data=file.read())

        if response:
            video_url = "https://argon.b-cdn.net/" + filename_extension
            print(f"The video URL is {video_url}")

            # Create a new video and add it to the database
            new_video = Video(
                title=lesson_name,  # Provide a title for the new video
                link=video_url,  # Provide a link for the new video
                teacher_id=course.teacher_id,  # Use the same teacher as the course
                unit_test="New Video Unit Test"  # Provide unit test information if available
            )
            db.session.add(new_video)

            # Create a new lesson
            new_lesson = Lesson(
                title=lesson_name,  # Provide a title for the new lesson
                content="New Lesson Content",  # Provide content for the new lesson
                course_id=course.id,  # Associate the lesson with the course
                teacher_id=course.teacher_id  # Use the same teacher as the course
            )
            db.session.add(new_lesson)

            # Commit here to ensure lesson_id and video_id are generated
            db.session.commit()

            # Associate the video with the new lesson
            association = LessonVideoAssociation(lesson_id=new_lesson.id, video_id=new_video.id)
            db.session.add(association)
            db.session.commit()

            return redirect(video_url)
        else:
            return f"Failed to upload file: {response.text}"

    else:
        return "Course/lesson not found"  # Handle the case where the course/lesson ID is invalid



# Route for rendering the success page
@app.route("/success", methods=["GET"])
def render_success_page():
    video_url = request.args.get("video_url")
    return f"We have received your video. Video URL: {video_url}"


@app.route("/s/<int:d>")
def s(d):
    course=Course.query.filter_by(id=d).first()
    course_lessons = course.lessons

    # Print or iterate over the lessons
    for lesson in course_lessons:
        print(f"Lesson ID: {lesson.id}, Title: {lesson.title}, Content: {lesson.content}")
    print(lesson.files[0].path)
    return "dddddd"


if __name__ == "__main__":
    app.run(debug=True)
