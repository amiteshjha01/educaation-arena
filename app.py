from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import os
from dotenv import load_dotenv
from functools import wraps
import stripe
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from io import BytesIO
import qrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Use strong secret in production

# MongoDB connection
MONGO_URI = "mongodb+srv://amiteshaptechdwarka123:KYjFyRJO4U43i7Mh@educaation-arena.4nyuro1.mongodb.net/?retryWrites=true&w=majority&appName=Educaation-Arena"
client = MongoClient(MONGO_URI)
db = client['elearning_db']
# Default admin user
default_admin = {
    'name': 'Admin',
    'email': 'admin@example.com',
    'password': generate_password_hash('admin123', method='pbkdf2:sha256'),
    'role': 'admin',
    'created_at': datetime.now()
}

# Insert admin if none exists
if db.users.count_documents({'role': 'admin'}) == 0:
    db.users.insert_one(default_admin)
    print("✅ Default admin user created!")
# Stripe setup
stripe.api_key = 'sk_test_51RLlmnQPDPzjhh2APABaoulnZU3c2dwBY5NrLsfByeqjURQcZsU3W8pkY8lXTSyquCmxhnHx9A19bGtvI33GMzvn00GMRWTnRP'
STRIPE_PUBLIC_KEY = 'pk_test_51RLlmnQPDPzjhh2A97sZh4EClj862vDFKRuWg4zrwOp0lxlLwqaOmieLoWDBueu2dYgSDdjKKTIVTTRz3eaJpeyS00XPa6ytTM'

# Add these constants at the top with other configurations
UPLOAD_FOLDER = 'static/course_materials'
ALLOWED_EXTENSIONS = {
    'video': {'mp4', 'webm', 'mov'},
    'document': {'pdf', 'doc', 'docx'},
    'notes': {'txt', 'md', 'rtf'}
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, file_type):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[file_type]

# Role-based access control decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user or user.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def instructor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user or user.get('role') != 'instructor':
            flash('Access denied. Instructor privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Sample courses data with extended information
courses = [
    {
        'id': 1,
        'title': 'Python Programming Fundamentals',
        'category': 'Programming',
        'description': 'Learn the basics of Python programming language',
        'image': 'static/images/python.jpg',
        'duration': '8 weeks',
        'price': 3500,
        'instructor_id': None,
        'syllabus': [
            {
                'week': 1,
                'title': 'Introduction to Python',
                'topics': ['Python setup', 'Basic syntax', 'Variables and data types']
            },
            {
                'week': 2,
                'title': 'Control Flow',
                'topics': ['Conditional statements', 'Loops', 'Functions']
            }
        ],
        'prerequisites': ['Basic computer knowledge', 'No prior programming experience required'],
        'includes_certificate': True,
        'learning_objectives': [
            'Understand Python fundamentals',
            'Write basic Python programs',
            'Work with Python data structures'
        ]
    },
    {
        'id': 2,
        'title': 'Data Structures and Algorithms',
        'category': 'DSA',
        'description': 'Master the fundamentals of Data Structures and Algorithms. This comprehensive course covers essential data structures, algorithm design techniques, and problem-solving strategies used in technical interviews and real-world software development. Learn to analyze algorithm complexity and optimize code performance.',
        'image': 'static/images/dsa.jpg',
        'duration': '12 weeks',
        'price': 8500,
        'instructor_id': None,
        'syllabus': [
            {
                'week': 1,
                'title': 'Introduction to Data Structures',
                'topics': ['Algorithm Analysis', 'Big O Notation', 'Arrays and Dynamic Arrays', 'Time & Space Complexity']
            },
            {
                'week': 2,
                'title': 'Linear Data Structures',
                'topics': ['Linked Lists (Singly & Doubly)', 'Stacks & Applications', 'Queues & Priority Queues', 'Implementation Techniques']
            }
        ],
        'prerequisites': [
            'Basic programming knowledge in any language',
            'Understanding of functions and loops',
            'Basic mathematical concepts',
            'Problem-solving aptitude'
        ],
        'includes_certificate': True,
        'learning_objectives': [
            'Master fundamental data structures and their implementations',
            'Analyze algorithm complexity and performance',
            'Implement efficient sorting and searching algorithms',
            'Solve complex programming problems using appropriate data structures',
            'Apply graph algorithms to real-world problems',
            'Optimize code using advanced algorithmic techniques'
        ]
    },
    {
        'id': 3,
        'title': 'Full Stack Web Development',
        'category': 'Web Development',
        'description': 'Become a complete web developer by mastering both frontend and backend technologies. This comprehensive course covers modern web development stack including HTML5, CSS3, JavaScript, React.js for frontend, and Node.js with Express for backend. Learn to build scalable, responsive web applications with industry best practices.',
        'image': 'static/images/web.jpg',
        'duration': '16 weeks',
        'price': 15000,
        'instructor_id': None,
        'syllabus': [
            {
                'week': 1,
                'title': 'HTML5 & CSS3 Fundamentals',
                'topics': ['HTML5 Semantic Elements', 'CSS3 Layouts', 'Flexbox & Grid', 'Responsive Design']
            },
            {
                'week': 2,
                'title': 'Advanced CSS & Sass',
                'topics': ['CSS Animations', 'Sass Preprocessing', 'CSS Architecture', 'Modern CSS Features']
            }
        ],
        'prerequisites': [
            'Basic understanding of HTML and CSS',
            'Familiarity with JavaScript fundamentals',
            'Understanding of web technologies',
            'Basic command line knowledge'
        ],
        'includes_certificate': True,
        'learning_objectives': [
            'Build responsive and dynamic web applications',
            'Master modern JavaScript and React.js',
            'Develop secure and scalable backend services',
            'Work with databases and API integration',
            'Deploy applications to production',
            'Implement real-time features and optimizations'
        ]
    },
    {
        'id': 4,
        'title': 'Mobile App Development with React Native',
        'category': 'Mobile Development',
        'description': 'Learn to build native mobile applications for both iOS and Android using React Native. This course covers everything from setup to deployment, including UI development, native device features, state management, and app store submission. Create professional, cross-platform mobile apps using a single codebase.',
        'image': 'static/images/mobile.jpg',
        'duration': '10 weeks',
        'price': 4000,
        'instructor_id': None,
        'syllabus': [
            {
                'week': 1,
                'title': 'React Native Fundamentals',
                'topics': ['Development Environment Setup', 'React Native CLI', 'Components & JSX', 'Props & State']
            },
            {
                'week': 2,
                'title': 'Mobile UI Development',
                'topics': ['Flexbox Layout', 'Styling Components', 'Core Components', 'Custom Components']
            }
        ],
        'prerequisites': [
            'Strong JavaScript knowledge',
            'Understanding of React.js concepts',
            'Familiarity with ES6+ features',
            'Basic understanding of mobile app development concepts'
        ],
        'includes_certificate': True,
        'learning_objectives': [
            'Build cross-platform mobile applications',
            'Implement native device features',
            'Create engaging mobile user interfaces',
            'Manage application state effectively',
            'Deploy apps to App Store and Play Store',
            'Optimize app performance and user experience'
        ]
    }
]

# Initialize database with courses if empty
if db.courses.count_documents({}) == 0:
    db.courses.insert_many(courses)

# Add this after the app initialization and before the routes
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = db.users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            return {'current_user': user}
    return {'current_user': None}

# Routes
@app.route('/')
def home():
    courses = list(db.courses.find())
    return render_template('index.html', courses=courses)

@app.route('/courses')
def courses():
    courses = list(db.courses.find())
    categories = list(db.categories.find().sort('name', 1))
    return render_template('courses.html', courses=courses, categories=categories)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = db.courses.find_one({'id': course_id})
    if course:
        instructor = None
        if course.get('instructor_id'):
            instructor = db.users.find_one({'_id': ObjectId(course['instructor_id'])})
        return render_template('course_detail.html', course=course, instructor=instructor)
    return redirect(url_for('home'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get all users
    users = list(db.users.find())
    
    # Get all courses
    courses = list(db.courses.find())
    
    # Calculate total enrollments
    enrollments = db.enrollments.count_documents({})
    
    # Calculate total revenue
    total_revenue = sum(course.get('price', 0) for course in courses)
    
    # Get all categories
    categories = list(db.categories.find().sort('name', 1))
    
    return render_template('admin/dashboard.html', 
                         users=users, 
                         courses=courses, 
                         enrollments=enrollments,
                         total_revenue=total_revenue,
                         categories=categories)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = list(db.users.find())
    return render_template('admin/users.html', users=users)

@app.route('/admin/courses')
@admin_required
def admin_courses():
    courses = list(db.courses.find())
    # Calculate enrollment counts for each course
    for course in courses:
        course['enrollment_count'] = db.enrollments.count_documents({'course_id': course['id']})
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_course(course_id):
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            description = request.form.get('description')
            duration = request.form.get('duration')
            price = float(request.form.get('price'))
            prerequisites = request.form.get('prerequisites', '').split(',')
            learning_objectives = request.form.get('learning_objectives', '').split(',')
            
            # Update course data
            update_data = {
                'title': title,
                'category': category,
                'description': description,
                'duration': f"{duration} weeks",
                'price': price,
                'image': f'static/images/{category.lower().replace(" ", "_")}.jpg',
                'prerequisites': [p.strip() for p in prerequisites if p.strip()],
                'learning_objectives': [o.strip() for o in learning_objectives if o.strip()]
            }
            
            # Update course
            result = db.courses.update_one(
                {'id': course_id},
                {'$set': update_data}
            )
            
            if result.modified_count > 0:
                flash('Course updated successfully!', 'success')
            else:
                flash('No changes made', 'info')
                
        except Exception as e:
            flash(f'Error updating course: {str(e)}', 'error')
            
        return redirect(url_for('admin_courses'))
        
    # GET request - fetch course data
    course = db.courses.find_one({'id': course_id})
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('admin_courses'))
        
    # Get all categories for the form
    categories = list(db.categories.find().sort('name', 1))
    
    # Extract duration number from "X weeks" format
    duration = course['duration'].split()[0] if 'duration' in course else ''
    
    return render_template('admin/edit_course.html', 
                         course=course, 
                         categories=categories,
                         duration=duration)

@app.route('/admin/add_course', methods=['POST'])
@admin_required
def admin_add_course():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            description = request.form.get('description')
            duration = request.form.get('duration')
            price = float(request.form.get('price'))
            prerequisites = request.form.get('prerequisites', '').split(',')
            learning_objectives = request.form.get('learning_objectives', '').split(',')
            
            # Get the next available course ID
            max_course = db.courses.find_one(sort=[("id", -1)])
            next_id = (max_course['id'] + 1) if max_course else 1
            
            course = {
                'id': next_id,
                'title': title,
                'category': category,
                'description': description,
                'duration': f"{duration} weeks",
                'price': price,
                'image': f'static/images/{category.lower().replace(" ", "_")}.jpg',
                'prerequisites': [p.strip() for p in prerequisites if p.strip()],
                'learning_objectives': [o.strip() for o in learning_objectives if o.strip()],
                'includes_certificate': True,
                'created_at': datetime.now()
            }
            
            db.courses.insert_one(course)
            flash('Course added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/courses/<course_id>/delete', methods=['POST'])
@admin_required
def admin_delete_course(course_id):
    try:
        db.courses.delete_one({'id': int(course_id)})
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting course', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/courses/<int:course_id>/materials')
@admin_required
def admin_course_materials(course_id):
    course = db.courses.find_one({'id': course_id})
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('admin_courses'))
    
    # Get all materials for this course
    materials = list(db.course_materials.find({'course_id': course_id}))
    return render_template('admin/course_materials.html', course=course, materials=materials)

@app.route('/admin/courses/<int:course_id>/materials/upload', methods=['POST'])
@admin_required
def admin_upload_material(course_id):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('admin_course_materials', course_id=course_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin_course_materials', course_id=course_id))
    
    material_type = request.form.get('type')
    if material_type not in ALLOWED_EXTENSIONS:
        flash('Invalid material type', 'error')
        return redirect(url_for('admin_course_materials', course_id=course_id))
    
    if file and allowed_file(file.filename, material_type):
        filename = secure_filename(file.filename)
        # Create a unique filename
        unique_filename = f"{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Save material info to database
        material = {
            'course_id': course_id,
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'type': material_type,
            'file_path': file_path,
            'original_filename': filename,
            'uploaded_by': ObjectId(session['user_id']),
            'uploaded_at': datetime.now()
        }
        db.course_materials.insert_one(material)
        
        flash('Material uploaded successfully!', 'success')
    else:
        flash('Invalid file type', 'error')
    
    return redirect(url_for('admin_course_materials', course_id=course_id))

@app.route('/admin/courses/<int:course_id>/materials/<material_id>/delete', methods=['POST'])
@admin_required
def admin_delete_material(course_id, material_id):
    material = db.course_materials.find_one({
        '_id': ObjectId(material_id),
        'course_id': course_id
    })
    
    if material:
        # Delete file from filesystem
        try:
            os.remove(material['file_path'])
        except OSError:
            pass  # File might not exist
        
        # Delete from database
        db.course_materials.delete_one({'_id': ObjectId(material_id)})
        flash('Material deleted successfully!', 'success')
    else:
        flash('Material not found', 'error')
    
    return redirect(url_for('admin_course_materials', course_id=course_id))

# Instructor routes
@app.route('/instructor/dashboard')
@instructor_required
def instructor_dashboard():
    # Get instructor's courses
    courses = list(db.courses.find({'instructor_id': ObjectId(session['user_id'])}))
    
    # Calculate total students
    total_students = sum(course.get('enrolled_students', 0) for course in courses)
    
    # Calculate average rating
    ratings = [course.get('rating', 0) for course in courses if course.get('rating')]
    average_rating = sum(ratings) / len(ratings) if ratings else 0
    
    # Get recent activities
    recent_activities = list(db.activities.find(
        {'course_id': {'$in': [course['id'] for course in courses]}}
    ).sort('timestamp', -1).limit(5))
    
    # Get all categories
    categories = list(db.categories.find().sort('name', 1))
    
    return render_template('instructor/dashboard.html',
                         courses=courses,
                         total_students=total_students,
                         average_rating=average_rating,
                         recent_activities=recent_activities,
                         categories=categories)

@app.route('/instructor/course/<course_id>')
@instructor_required
def instructor_course(course_id):
    course = db.courses.find_one({'id': int(course_id), 'instructor_id': ObjectId(session['user_id'])})
    if not course:
        flash('Course not found or access denied', 'error')
        return redirect(url_for('instructor_dashboard'))
    
    # Get enrolled students with their user data
    enrolled_students = []
    for enrollment in db.enrollments.find({'course_id': int(course_id)}):
        user = db.users.find_one({'_id': enrollment['student_id']})
        if user:
            enrolled_students.append({
                'name': user['name'],
                'email': user['email'],
                'enrollment_date': enrollment.get('enrollment_date')
            })
    
    # Fetch uploaded materials for this course
    materials = list(db.course_materials.find({'course_id': int(course_id)}))
    return render_template('instructor/course.html', course=course, enrolled_students=enrolled_students, materials=materials)

@app.route('/instructor/add_course', methods=['POST'])
@instructor_required
def instructor_add_course():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category = request.form.get('category')
            description = request.form.get('description')
            duration = request.form.get('duration')
            price = float(request.form.get('price', 0))
            prerequisites = request.form.get('prerequisites', '').split(',')
            learning_objectives = request.form.get('learning_objectives', '').split(',')
            
            # Get the next available course ID
            max_course = db.courses.find_one(sort=[("id", -1)])
            next_id = (max_course['id'] + 1) if max_course else 1
            
            course = {
                'id': next_id,
                'title': title,
                'category': category,
                'description': description,
                'duration': f"{duration} weeks",
                'price': price,
                'image': f'static/images/{category.lower().replace(" ", "_")}.jpg',
                'prerequisites': [p.strip() for p in prerequisites if p.strip()],
                'learning_objectives': [o.strip() for o in learning_objectives if o.strip()],
                'includes_certificate': True,
                'instructor_id': ObjectId(session['user_id']),
                'created_at': datetime.now(),
                'syllabus': []
            }
            
            # Add syllabus if provided
            syllabus_weeks = int(request.form.get('syllabus_weeks', 0))
            syllabus = []
            for week in range(1, syllabus_weeks + 1):
                week_title = request.form.get(f'week_{week}_title')
                week_topics = request.form.get(f'week_{week}_topics', '').split(',')
                if week_title:
                    syllabus.append({
                        'week': week,
                        'title': week_title,
                        'topics': [topic.strip() for topic in week_topics if topic.strip()]
                    })
            course['syllabus'] = syllabus
            
            db.courses.insert_one(course)
            flash('Course added successfully!', 'success')
            return redirect(url_for('instructor_dashboard'))
            
        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
            return redirect(url_for('instructor_dashboard'))
            
    return redirect(url_for('instructor_dashboard'))

@app.route('/instructor/course/<course_id>/content/add', methods=['POST'])
@instructor_required
def instructor_add_content(course_id):
    instructor_id = ObjectId(session['user_id'])
    course = db.courses.find_one({'id': int(course_id), 'instructor_id': instructor_id})
    if not course:
        flash('Course not found or access denied', 'error')
        return redirect(url_for('instructor_course', course_id=course_id))

    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('instructor_course', course_id=course_id))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('instructor_course', course_id=course_id))

    material_type = request.form.get('type')
    if material_type not in ALLOWED_EXTENSIONS:
        flash('Invalid content type', 'error')
        return redirect(url_for('instructor_course', course_id=course_id))

    if file and allowed_file(file.filename, material_type):
        filename = secure_filename(file.filename)
        unique_filename = f"{course_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        material = {
            'course_id': int(course_id),
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'type': material_type,
            'file_path': file_path,
            'original_filename': filename,
            'uploaded_by': instructor_id,
            'uploaded_at': datetime.now()
        }
        db.course_materials.insert_one(material)
        flash('Content uploaded successfully!', 'success')
    else:
        flash('Invalid file type', 'error')

    return redirect(url_for('instructor_course', course_id=course_id))

@app.route('/instructor/course/<course_id>/quiz/add', methods=['GET', 'POST'])
@instructor_required
def instructor_add_quiz(course_id):
    instructor_id = ObjectId(session['user_id'])
    course = db.courses.find_one({'id': int(course_id), 'instructor_id': instructor_id})
    if not course:
        flash('Course not found or access denied', 'error')
        return redirect(url_for('instructor_dashboard'))

    if request.method == 'POST':
        module_id = int(request.form.get('module_id'))
        questions = []
        for i in range(1, 6):  # Assume up to 5 questions per quiz for simplicity
            q = request.form.get(f'question_{i}')
            if not q:
                continue
            options = [request.form.get(f'option_{i}_a'), request.form.get(f'option_{i}_b'), request.form.get(f'option_{i}_c'), request.form.get(f'option_{i}_d')]
            correct = request.form.get(f'correct_{i}')
            questions.append({
                'id': i,
                'question': q,
                'options': options,
                'correct_answer': correct
            })
        if questions:
            db.quizzes.update_one(
                {'course_id': int(course_id), 'module_id': module_id},
                {'$set': {'questions': questions}},
                upsert=True
            )
            flash('Quiz added/updated successfully!', 'success')
        else:
            flash('No questions provided.', 'error')
        return redirect(url_for('instructor_course', course_id=course_id))

    # GET: Render a form (handled in template)
    return render_template('instructor/add_quiz.html', course=course)

# Certificate generation functions
def generate_certificate(student_name, course_name, completion_date, average_score, certificate_id):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add background
    c.setFillColor(colors.lightgrey)
    c.rect(0, 0, width, height, fill=1)
    
    # Add border
    c.setStrokeColor(colors.gold)
    c.setLineWidth(5)
    c.rect(20, 20, width-40, height-40)
    
    # Add header
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.darkblue)
    c.drawCentredString(width/2, height-100, "Certificate of Completion")
    
    # Add content
    c.setFont("Helvetica", 16)
    c.setFillColor(colors.black)
    c.drawCentredString(width/2, height-200, f"This is to certify that")
    
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-250, student_name)
    
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height-300, f"has successfully completed the course")
    
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-350, course_name)
    
    c.setFont("Helvetica", 16)
    c.drawCentredString(width/2, height-400, f"with an average score of {average_score}%")
    
    # Add date
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height-450, f"Date: {completion_date.strftime('%B %d, %Y')}")
    
    # Add certificate ID
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height-500, f"Certificate ID: {certificate_id}")
    
    # Add QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"Certificate ID: {certificate_id}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to buffer
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_buffer.seek(0)
    
    # Add QR code to PDF
    c.drawImage(qr_buffer, width-150, 50, width=100, height=100)
    
    c.save()
    buffer.seek(0)
    return buffer

def calculate_course_average(student_id, course_id):
    enrollment = db.enrollments.find_one({
        'student_id': ObjectId(student_id),
        'course_id': course_id
    })
    
    if not enrollment or 'quiz_scores' not in enrollment:
        return 0
    
    quiz_scores = enrollment['quiz_scores'].values()
    if not quiz_scores:
        return 0
    
    return sum(quiz_scores) / len(quiz_scores)

def is_course_completed(student_id, course_id):
    enrollment = db.enrollments.find_one({
        'student_id': ObjectId(student_id),
        'course_id': course_id
    })
    
    if not enrollment:
        return False
    
    # Check if all modules are completed
    course = db.courses.find_one({'id': course_id})
    if not course:
        return False
    
    total_modules = len(course.get('syllabus', []))
    completed_modules = len(enrollment.get('completed_modules', []))
    
    return completed_modules == total_modules

# Certificate routes
@app.route('/certificate/<course_id>')
def view_certificate(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    course = db.courses.find_one({'id': int(course_id)})
    
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Check if course is completed
    if not is_course_completed(student_id, int(course_id)):
        flash('Course not completed yet', 'error')
        return redirect(url_for('student_dashboard'))
    
    # Get or create certificate
    certificate = db.certificates.find_one({
        'student_id': ObjectId(student_id),
        'course_id': int(course_id)
    })
    
    if not certificate:
        # Calculate average score
        average_score = calculate_course_average(student_id, int(course_id))
        
        # Generate certificate
        student = db.users.find_one({'_id': ObjectId(student_id)})
        certificate_id = str(ObjectId())
        
        certificate = {
            'student_id': ObjectId(student_id),
            'course_id': int(course_id),
            'certificate_id': certificate_id,
            'average_score': average_score,
            'issue_date': datetime.now(),
            'student_name': student['name'],
            'course_name': course['title']
        }
        
        db.certificates.insert_one(certificate)
    
    # Generate PDF
    pdf_buffer = generate_certificate(
        certificate['student_name'],
        certificate['course_name'],
        certificate['issue_date'],
        certificate['average_score'],
        certificate['certificate_id']
    )
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"certificate_{course_id}.pdf",
        mimetype='application/pdf'
    )

@app.route('/student/certificates')
def student_certificates():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    student_id = ObjectId(session['user_id'])
    certificates = list(db.certificates.find({'student_id': student_id}))
    
    # Get course details for each certificate
    for cert in certificates:
        course = db.courses.find_one({'id': cert['course_id']})
        cert['course'] = course
    
    return render_template('student/certificates.html', certificates=certificates)

# Update the student dashboard to show certificate status
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    student_id = ObjectId(session['user_id'])
    enrollments = list(db.enrollments.find({'student_id': student_id}))
    enrolled_courses = []
    
    for enrollment in enrollments:
        course = db.courses.find_one({'id': enrollment['course_id']})
        if course:
            # Convert all ObjectId fields to strings
            course['_id'] = str(course['_id'])
            if 'instructor_id' in course:
                course['instructor_id'] = str(course['instructor_id'])
            course['progress'] = enrollment.get('progress', 0)
            course['completed_modules'] = enrollment.get('completed_modules', [])
            
            # Check if course is completed
            course['is_completed'] = is_course_completed(str(student_id), course['id'])
            
            # Check if certificate exists
            certificate = db.certificates.find_one({
                'student_id': student_id,
                'course_id': course['id']
            })
            course['has_certificate'] = bool(certificate)
            
            enrolled_courses.append(course)
    
    return render_template('student/dashboard.html', courses=enrolled_courses)

@app.route('/config')
def get_stripe_config():
    return jsonify({'publicKey': STRIPE_PUBLIC_KEY})

@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    course = db.courses.find_one({'id': course_id})
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    # Check if already enrolled
    existing_enrollment = db.enrollments.find_one({
        'student_id': ObjectId(session['user_id']),
        'course_id': course_id
    })
    
    if existing_enrollment:
        return jsonify({'error': 'Already enrolled in this course'}), 400
    
    # Create Stripe checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': int(course['price'] * 100),  # Convert to cents
                    'product_data': {
                        'name': course['title'],
                        'description': course['description'],
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + f'payment/success/{course_id}',
            cancel_url=request.host_url + f'payment/cancel/{course_id}',
        )
        return jsonify({'sessionId': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/payment/success/<int:course_id>')
def payment_success(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Create enrollment record
    enrollment = {
        'student_id': ObjectId(session['user_id']),
        'course_id': course_id,
        'enrollment_date': datetime.now(),
        'progress': 0,
        'completed_modules': [],
        'quiz_scores': {}
    }
    db.enrollments.insert_one(enrollment)
    
    flash('Successfully enrolled in the course!', 'success')
    return redirect(url_for('student_dashboard'))

@app.route('/payment/cancel/<int:course_id>')
def payment_cancel(course_id):
    flash('Payment cancelled', 'error')
    return redirect(url_for('course_detail', course_id=course_id))

# Quiz routes
@app.route('/quiz/<int:course_id>/<int:module_id>')
def take_quiz(course_id, module_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    course = db.courses.find_one({'id': course_id})
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('student_dashboard'))
    
    quiz = db.quizzes.find_one({'course_id': course_id, 'module_id': module_id})
    return render_template('student/quiz.html', course=course, quiz=quiz)

@app.route('/quiz/<int:course_id>/<int:module_id>/submit', methods=['POST'])
def submit_quiz(course_id, module_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    answers = request.form.to_dict()
    quiz = db.quizzes.find_one({'course_id': course_id, 'module_id': module_id})
    
    score = 0
    total_questions = len(quiz['questions'])
    
    for question in quiz['questions']:
        if answers.get(str(question['id'])) == question['correct_answer']:
            score += 1
    
    percentage = (score / total_questions) * 100
    
    # Update student's quiz score
    db.enrollments.update_one(
        {
            'student_id': ObjectId(session['user_id']),
            'course_id': course_id
        },
        {
            '$set': {
                f'quiz_scores.{module_id}': percentage
            }
        }
    )
    
    flash(f'Quiz submitted! Your score: {percentage}%', 'success')
    return redirect(url_for('student_dashboard'))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = db.users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            
            # Redirect based on user role
            if user.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.get('role') == 'instructor':
                return redirect(url_for('instructor_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
                
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')  # Default role is student
        
        if db.users.find_one({'email': email}):
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Specify the hashing method
        db.users.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.now()
        })
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/contact_submit', methods=['POST'])
def contact_submit():
    try:
        data = request.get_json()
        
        # Create new message
        new_message = {
            'name': data['name'],
            'email': data['email'],
            'subject': data['subject'],
            'message': data['message'],
            'created_at': datetime.now(),
            'is_read': False
        }
        
        # Save to database
        result = db.contact_messages.insert_one(new_message)
        
        if result.inserted_id:
            return jsonify({'success': True, 'message': 'Message sent successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send message. Please try again.'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/messages')
@admin_required
def admin_messages():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    # Get total count for pagination
    total_messages = db.contact_messages.count_documents({})
    total_pages = (total_messages + per_page - 1) // per_page
    
    messages = list(db.contact_messages.find().sort('created_at', -1).skip(skip).limit(per_page))
    return render_template('admin/messages.html', messages=messages, page=page, total_pages=total_pages)

@app.route('/admin/messages/<message_id>')
@admin_required
def view_message(message_id):
    try:
        message = db.contact_messages.find_one({'_id': ObjectId(message_id)})
        if message:
            if not message.get('is_read'):
                db.contact_messages.update_one(
                    {'_id': ObjectId(message_id)}, 
                    {'$set': {'is_read': True}}
                )
            return render_template('admin/view_message.html', message=message)
        else:
            flash('Message not found', 'error')
            return redirect(url_for('admin_messages'))
    except Exception as e:
        flash('Error viewing message: ' + str(e), 'error')
        return redirect(url_for('admin_messages'))

@app.route('/admin/messages/<message_id>/delete', methods=['POST'])
@admin_required
def delete_message(message_id):
    try:
        result = db.contact_messages.delete_one({'_id': ObjectId(message_id)})
        if result.deleted_count > 0:
            flash('Message deleted successfully', 'success')
        else:
            flash('Message not found', 'error')
    except Exception as e:
        flash('Error deleting message: ' + str(e), 'error')
    return redirect(url_for('admin_messages'))

@app.route('/course/<int:course_id>/materials')
def view_course_materials(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    course = db.courses.find_one({'id': course_id})
    if not course:
        flash('Course not found', 'error')
        return redirect(url_for('home'))
    
    # Check if user is enrolled in the course
    enrollment = db.enrollments.find_one({
        'student_id': ObjectId(session['user_id']),
        'course_id': course_id
    })
    
    if not enrollment and session.get('role') not in ['admin', 'instructor']:
        flash('You must be enrolled in this course to view materials', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    
    # Get all materials for this course
    materials = list(db.course_materials.find({'course_id': course_id}))
    return render_template('student/course_materials.html', course=course, materials=materials)

@app.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'student')
            
            # Check if email already exists
            if db.users.find_one({'email': email}):
                flash('Email already exists', 'error')
                return redirect(url_for('admin_users'))
            
            # Create new user
            user = {
                'name': name,
                'email': email,
                'password': generate_password_hash(password, method='pbkdf2:sha256'),
                'role': role,
                'created_at': datetime.now()
            }
            
            db.users.insert_one(user)
            flash('User added successfully!', 'success')
            
        except Exception as e:
            flash(f'Error adding user: {str(e)}', 'error')
            
    return redirect(url_for('admin_users'))

@app.route('/student/quiz-results')
def student_quiz_results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    student_id = ObjectId(session['user_id'])
    enrollments = list(db.enrollments.find({'student_id': student_id}))
    quiz_results = []
    
    for enrollment in enrollments:
        course = db.courses.find_one({'id': enrollment['course_id']})
        if course and 'quiz_scores' in enrollment:
            for module_id, score in enrollment['quiz_scores'].items():
                module = next((m for m in course.get('syllabus', []) if m['week'] == int(module_id)), None)
                quiz_results.append({
                    'course_title': course['title'],
                    'module_title': module['title'] if module else f'Module {module_id}',
                    'score': score,
                    'date': enrollment.get('last_quiz_date', {}).get(str(module_id)),
                    'course_id': course['id'],
                    'module_id': module_id
                })
    
    # Sort by date, most recent first
    quiz_results.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
    
    return render_template('student/quiz_results.html', quiz_results=quiz_results)

@app.route('/admin/categories')
@admin_required
def admin_categories():
    categories = list(db.categories.find().sort('name', 1))
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
@admin_required
def admin_add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Check if category already exists
        if db.categories.find_one({'name': name}):
            flash('Category already exists', 'error')
            return redirect(url_for('admin_categories'))
        
        # Create new category
        category = {
            'name': name,
            'description': description,
            'created_at': datetime.now()
        }
        
        db.categories.insert_one(category)
        flash('Category added successfully!', 'success')
        
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<category_id>/delete', methods=['POST'])
@admin_required
def admin_delete_category(category_id):
    try:
        # Check if category is in use
        if db.courses.count_documents({'category': db.categories.find_one({'_id': ObjectId(category_id)})['name']}) > 0:
            flash('Cannot delete category that is in use by courses', 'error')
            return redirect(url_for('admin_categories'))
            
        result = db.categories.delete_one({'_id': ObjectId(category_id)})
        if result.deleted_count > 0:
            flash('Category deleted successfully', 'success')
        else:
            flash('Category not found', 'error')
    except Exception as e:
        flash('Error deleting category: ' + str(e), 'error')
    return redirect(url_for('admin_categories'))

# Update the instructor routes to include category management
@app.route('/instructor/categories')
@instructor_required
def instructor_categories():
    categories = list(db.categories.find().sort('name', 1))
    return render_template('instructor/categories.html', categories=categories)

@app.route('/instructor/categories/add', methods=['POST'])
@instructor_required
def instructor_add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Check if category already exists
        if db.categories.find_one({'name': name}):
            flash('Category already exists', 'error')
            return redirect(url_for('instructor_categories'))
        
        # Create new category
        category = {
            'name': name,
            'description': description,
            'created_at': datetime.now()
        }
        
        db.categories.insert_one(category)
        flash('Category added successfully!', 'success')
        
    return redirect(url_for('instructor_categories'))

if __name__ == '__main__':
    app.run(debug=True) 
