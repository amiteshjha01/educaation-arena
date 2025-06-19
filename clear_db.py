from pymongo import MongoClient

def clear_users():
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['elearning_db']
        
        # Delete all users
        result = db.users.delete_many({})
        print(f"Successfully deleted {result.deleted_count} users")
        
        # Close the connection
        client.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    clear_users() 