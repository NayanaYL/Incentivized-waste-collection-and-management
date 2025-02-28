from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection setup
client = MongoClient('mongodb://localhost:27017')
db = client['waste_management']
users_collection = db['users']

waste_types = [{"type": "Plastic"}, {"type": "Paper"}, {"type": "Glass"}]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"username": username, "password": password})

        if user:
            return redirect(url_for('info', username=username))  # Redirect to info page after login
        else:
            return 'Invalid credentials. Please try again.'
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        existing_user = users_collection.find_one({"username": username})
        
        if existing_user:
            return 'Username already exists. Please choose another one.'
        
        # Create a new user
        users_collection.insert_one({
            "username": username,
            "password": password,
            "points": 0  # New users start with 0 points
        })
        
        return redirect(url_for('login'))  # Redirect to login page after successful registration
    
    return render_template('regi.html')

@app.route('/info', methods=['GET', 'POST'])
def info():
    username = request.args.get('username')
    if request.method == 'POST':
        waste_type = request.form['waste_type']
        weight = float(request.form['weight'])
        reward_points = weight * 5
        user = users_collection.find_one({"username": username})

        if user:
            new_points = user['points'] + reward_points
            users_collection.update_one({"username": username}, {"$set": {"points": new_points}})

        return render_template('result.html', status="Waste submission successful!", cost=reward_points, updated_points=new_points, username=username)

    return render_template('info.html', waste_types=waste_types, username=username)

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/dashboard/<username>', methods=['GET'])
def dashboard(username):
    user = users_collection.find_one({"username": username})
    if user:
        points = user.get('points', 0)
        return render_template('dashboard.html', username=username, points=points)
    else:
        return 'User not found.'
        
@app.route('/redeem/<username>', methods=['GET', 'POST'])
def redeem(username):
    user = users_collection.find_one({"username": username})
    if user:
        if request.method == 'POST':
            redeem_points = int(request.form['redeem_points'])  # Points user wants to redeem
            option = request.form['option']  # The selected option (bank_transfer or collect_cash)

            # Check if the user has enough points to redeem
            if redeem_points <= user['points']:
                if option == 'bank_transfer':
                    # Pass the redeem_points in the query parameter
                    return redirect(url_for('bank_transfer', username=username, redeem_points=redeem_points))
                elif option == 'collect_cash':
                    return redirect(url_for('collect_cash', username=username))
            else:
                # If points are insufficient, show an error message
                error_message = "Insufficient points to redeem."
                return render_template('redeem.html', username=username, points=user['points'], error=error_message)
        
        return render_template('redeem.html', username=username, points=user['points'])
    else:
        return 'User not found.'

@app.route('/bank_transfer/<username>', methods=['GET', 'POST'])
def bank_transfer(username):
    user = users_collection.find_one({"username": username})
    if user:
        # Get the redeem_points passed from the previous page
        redeem_points = request.args.get('redeem_points', type=int, default=0)  # Fetch redeem points from query param

        if request.method == 'POST':
            # Process the form and save the bank details
            bank_details = {
                "account_name": request.form['account_name'],
                "account_number": request.form['account_number'],
                "ifsc": request.form['ifsc'],
                "bank_name": request.form['bank_name']
            }

            # Save the bank details to the database
            users_collection.update_one({"username": username}, {"$set": {"bank_details": bank_details}})

            # Optionally subtract the redeemed points from the user's balance
            new_balance = user['points'] - redeem_points
            users_collection.update_one({"username": username}, {"$set": {"points": new_balance}})

            # Provide confirmation and pass success flag and redeemed points to template
            return render_template('bank_transfer.html', username=username, bank_details=user.get('bank_details', {}), redeem_points=redeem_points, success=True)

        return render_template('bank_transfer.html', username=username, bank_details=user.get('bank_details', {}), redeem_points=redeem_points)

    else:
        return 'User not found.'

@app.route('/collect_cash/<username>')
def collect_cash(username):
    user = users_collection.find_one({"username": username})
    if user:
        return render_template('collect_cash.html', username=username)
    else:
        return 'User not found.'

@app.route('/donate', methods=['GET' , 'POST'])
def donate():
    username = request.form['username']
    points_to_donate = int(request.form['donate_points'])
    user = users_collection.find_one({"username": username})

    if user and user['points'] >= points_to_donate:
        users_collection.update_one({"username": username}, {"$inc": {"points": -points_to_donate}})
        return f"{points_to_donate} points donated for road construction! Thank you for your generosity."
    return "Insufficient points."

if __name__ == '__main__':
    app.run(debug=True)
