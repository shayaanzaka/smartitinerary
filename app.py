from flask import Flask, render_template, request, jsonify, redirect, url_for
from pyspark.sql import SparkSession
import bcrypt
import os

# Initialize Flask App
app = Flask(__name__)

# Initialize PySpark Session
spark = SparkSession.builder.appName("UserLoginApp").getOrCreate()

# Define Parquet File Path for User Data
USER_DATA_FILE = "users_data.parquet"


# ** Route to Serve Home/Login Page **
@app.route('/')
def home():
    return render_template('index.html')


# ** Route to Serve Registration Page **
@app.route('/register')
def register():
    return render_template('register.html')


# ** Route to Serve Dashboard Page **
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# ** API to Register a New User **
@app.route('/api/register', methods=['POST'])
def register_user():
    try:
        # Get form data from request
        data = request.json
        first_name = data['firstName']
        last_name = data['lastName']
        email = data['email']
        password = data['password']
        address = data['address']
        pin_code = data['pinCode']

        # Validate all fields
        if not all([first_name, last_name, email, password, address, pin_code]):
            return jsonify({"error": "All fields are required!"}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create DataFrame for new user
        new_user_data = [{
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "address": address,
            "pin_code": pin_code
        }]
        new_df = spark.createDataFrame(new_user_data)

        # Check if file exists and append data
        if os.path.exists(USER_DATA_FILE):
            existing_df = spark.read.parquet(USER_DATA_FILE)
            combined_df = existing_df.union(new_df)
        else:
            combined_df = new_df

        # Save updated data
        combined_df.write.mode("overwrite").parquet(USER_DATA_FILE)

        return jsonify({"message": "User registered successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ** API to Log In a User **
@app.route('/api/login', methods=['POST'])
def login_user():
    try:
        # Get login credentials
        data = request.json
        email = data['email']
        password = data['password']

        # Validate incoming data
        if not email or not password:
            return jsonify({"error": "Email and password are required!"}), 400

        # Check if Parquet file exists
        if not os.path.exists(USER_DATA_FILE):
            return jsonify({"error": "No users found!"}), 404

        # Load the user data
        df = spark.read.parquet(USER_DATA_FILE)
        user = df.filter(df.email == email).collect()

        # If user is not found
        if not user:
            return jsonify({"error": "Invalid email or password!"}), 401

        # Compare the password using bcrypt
        stored_password = user[0]['password']
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return jsonify({"error": "Invalid email or password!"}), 401

        # Successful login
        return jsonify({
            "message": "Login successful!",
            "user": {
                "firstName": user[0]['first_name'],
                "lastName": user[0]['last_name'],
                "email": user[0]['email'],
                "address": user[0]['address'],
                "pinCode": user[0]['pin_code'],
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ** API to Fetch Logged-in User Data (Dashboard) **
@app.route('/api/getUserData', methods=['GET'])
def get_user_data():
    try:
        # Simulate logged-in user (this should come from a real session)
        user_email = "test@example.com"

        # Check if Parquet file exists
        if not os.path.exists(USER_DATA_FILE):
            return jsonify({"error": "No users found!"}), 404

        # Load user data from Parquet file
        df = spark.read.parquet(USER_DATA_FILE)
        user = df.filter(df.email == user_email).collect()

        if not user:
            return jsonify({"error": "User not found!"}), 404

        # Return user data
        return jsonify({
            "firstName": user[0]['first_name'],
            "lastName": user[0]['last_name'],
            "email": user[0]['email'],
            "address": user[0]['address'],
            "pinCode": user[0]['pin_code'],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ** API to Save User Preferences (Dashboard) **
@app.route('/api/savePreferences', methods=['POST'])
def save_preferences():
    try:
        # Get selected preferences
        data = request.json
        preferences = data['preferences']

        if not preferences:
            return jsonify({"error": "No preferences selected!"}), 400

        # Log preferences (for demo)
        print(f"Saved Preferences: {preferences}")

        return jsonify({"message": "Preferences saved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Run the Flask App
if __name__ == '__main__':
    app.run(port=5000, debug=True)
