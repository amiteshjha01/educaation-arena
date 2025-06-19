from pymongo import MongoClient
from pprint import pprint
from bson import ObjectId

def view_database():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['elearning_db']
    
    while True:
        print("\nE-Learning Database Viewer")
        print("1. View all users")
        print("2. View all courses")
        print("3. View all enrollments")
        print("4. View all messages")
        print("5. Search user by email")
        print("6. Search course by title")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-6): ")
        
        if choice == '1':
            print("\nAll Users:")
            for user in db.users.find():
                print("\nUser ID:", user['_id'])
                print("Name:", user['name'])
                print("Email:", user['email'])
                print("Role:", user.get('role', 'student'))
                print("-" * 50)
                
        elif choice == '2':
            print("\nAll Courses:")
            for course in db.courses.find():
                print("\nCourse ID:", course['id'])
                print("Title:", course['title'])
                print("Category:", course['category'])
                print("Price:", course['price'])
                print("Duration:", course['duration'])
                print("-" * 50)
                
        elif choice == '3':
            print("\nAll Enrollments:")
            for enrollment in db.enrollments.find():
                student = db.users.find_one({'_id': enrollment['student_id']})
                course = db.courses.find_one({'id': enrollment['course_id']})
                print("\nEnrollment ID:", enrollment['_id'])
                print("Student:", student['name'] if student else "Unknown")
                print("Course:", course['title'] if course else "Unknown")
                print("Date:", enrollment['enrollment_date'])
                print("Progress:", enrollment.get('progress', 0), "%")
                print("-" * 50)
                
        elif choice == '4':
            print("\nAll Messages:")
            for message in db.contact_messages.find():
                print("\nMessage ID:", message['_id'])
                print("From:", message['name'])
                print("Email:", message['email'])
                print("Subject:", message['subject'])
                print("Date:", message['created_at'])
                print("Message:", message['message'])
                print("Status:", "Read" if message.get('is_read') else "Unread")
                print("-" * 50)
                
        elif choice == '5':
            email = input("\nEnter email to search: ")
            user = db.users.find_one({'email': email})
            if user:
                print("\nUser found:")
                print("User ID:", user['_id'])
                print("Name:", user['name'])
                print("Email:", user['email'])
                print("Role:", user.get('role', 'student'))
            else:
                print("\nUser not found")
                
        elif choice == '6':
            title = input("\nEnter course title to search: ")
            course = db.courses.find_one({'title': {'$regex': title, '$options': 'i'}})
            if course:
                print("\nCourse found:")
                print("Course ID:", course['id'])
                print("Title:", course['title'])
                print("Category:", course['category'])
                print("Price:", course['price'])
                print("Duration:", course['duration'])
            else:
                print("\nCourse not found")
                
        elif choice == '0':
            break
        else:
            print("\nInvalid choice. Please try again.")
    
    client.close()

if __name__ == "__main__":
    view_database() 