from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017')  # Connect to local MongoDB server
db = client['waste_management']  # Name of your database (it will be created if it doesn't exist)
users_collection = db['users']  # Collection for user data

@app.route('/')
def home():
    return render_template('index.html')  # Render the home page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user data from MongoDB
        user = users_collection.find_one({"username": username, "password": password})

        if user:
            return redirect(url_for('dashboard', username=username))  # Redirect to dashboard with username
        else:
            return 'Invalid credentials. Please try again.'

    return render_template('login.html')  # Render login page

@app.route('/dashboard/<username>', methods=['GET'])
def dashboard(username):
    # Fetch user data
    user = users_collection.find_one({"username": username})
    if user:
        points = user.get('points', 0)
        return render_template('dashboard.html', username=username, points=points)
    else:
        return 'User not found.'

@app.route('/redeem', methods=['POST'])
def redeem():
    username = request.form['username']
    redeem_points = int(request.form['redeem_points'])

    # Update points in MongoDB
    user = users_collection.find_one({"username": username})
    if user and user['points'] >= redeem_points:
        users_collection.update_one({"username": username}, {"$inc": {"points": -redeem_points}})
        return f"Redeemed {redeem_points} points. Remaining points: {user['points'] - redeem_points}"
    else:
        return 'Not enough points to redeem.'

@app.route('/donate', methods=['POST'])
def donate():
    username = request.form['username']
    donate_points = int(request.form['donate_points'])

    # Update points in MongoDB
    user = users_collection.find_one({"username": username})
    if user and user['points'] >= donate_points:
        users_collection.update_one({"username": username}, {"$inc": {"points": -donate_points}})
        return f"Donated {donate_points} points for road construction. Remaining points: {user['points'] - donate_points}"
    else:
        return 'Not enough points to donate.'

if __name__ == '__main__':
    app.run(debug=True)
