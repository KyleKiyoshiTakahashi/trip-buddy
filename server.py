from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from datetime import datetime
import re
from flask_bcrypt import Bcrypt
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = "eatmyshorts!"
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def register():
    # validations
    error = False
    # checks to make sure the first name is more than 2 chars
    if len(request.form['first_name']) < 2:
        flash("WRONG! FIRST NAME MUST BE 2 OR MORE CHARACTERS")
        error = True
    # checks to see if the last name is grtr than 2 chars
    if len(request.form['last_name']) < 2:
        flash("LOLOL! LAST NAME MUST BE 2 OR MORE CHARACTERS")
        error = True
    # checks to see that the password is longer than 7 chars
    if len(request.form['password']) < 8:
        flash("WTF IS WRONG WITH YOU! PASSWORD MUST BE LONGER THAN 7 CHARACTERS")
        error = True
    # checks that the PW and CPW match
    if request.form['password'] != request.form['c_password']:
        flash("PASSWORDS MUST MATCH, IDIOT")
        error = True
    # checks that only alphabet letters were entered
    if not request.form['first_name'].isalpha():
        flash("NO BOTS OR PEOPLE WHO IDENTIFY AS BOTS WELCOME")
        error = True
    # checks that only alphabet letters were entered
    if not request.form['last_name'].isalpha():
        flash("NO BOTS ALLOWED HERE, BOT-MAN")
        error = True
    # makes sure that only email syntax was entered
    if not EMAIL_REGEX.match(request.form['email']):
        flash("BOTS NOT WELCOME, TRY twitter.com INSTEAD")
        error = True
    # query to make sure there are no mathcing emails in the db
    data = {
        "email" : request.form['email']
    }
    query = "SELECT * FROM users WHERE email = %(email)s"
    mysql = connectToMySQL('tripbud')
    matching_email_users = mysql.query_db(query,data)
    if len(matching_email_users) > 0:
        flash("Identity theft is funny...JK, IT IS NOT FUNNY...GO AWAY")
        error = True
    if error:
        return redirect('/')

    # query to create a new user and add them to db
    data = {
        "first_name" : request.form['first_name'],
        "last_name"  : request.form['last_name'],
        "email"      : request.form['email'],
        "password"   : bcrypt.generate_password_hash(request.form['password'])
    }
    query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, NOW(), NOW());"
    mysql = connectToMySQL('tripbud')
    user_id = mysql.query_db(query, data)
    session['user_id'] = user_id
    return redirect('/')
    print(user_id)

@app.route('/login', methods=['POST'])
def login():
    # query to compare the email entered into the form vs what's in the DB
    data = {
        "email" : request.form['email']
    }
    query = "SELECT * FROM users WHERE email = %(email)s"
    mysql = connectToMySQL('tripbud')
    matching_email_users = mysql.query_db(query,data)
    # checks to see if the email already exists in the DB
    if len(matching_email_users) == 0:
        flash("Nice try Wise-Guy")
        print("bad email")
        return redirect('/')
    user = matching_email_users[0]
    # if the stored PW is the same as the password entered, continue to next page
    if bcrypt.check_password_hash(user['password'], request.form['password']):
        session['user_id'] = user['id']
        return redirect('/travels')
    flash("Invalid credentials...admins have alerted the FBI")
    print("bad pw")
    return redirect('/')

@app.route('/travels')
def travels():
    # if the user_id is not the one in session but viewing the page
    if not 'user_id' in session:
        flash("Get out!")
        return redirect('/')
       
    # query that will display logged in  users first name
    data={
        "user_id": session['user_id']
    }
    query="SELECT * FROM users WHERE id = %(user_id)s;"
    mysql=connectToMySQL('tripbud')
    user=mysql.query_db(query,data)


    # query to get the trips the logged in user created
    mysql=connectToMySQL('tripbud')
    data={
        "user_id": session['user_id']
    }
    query="SELECT * FROM trips WHERE creator_id= %(user_id)s;"
    created_trips= mysql.query_db(query, data)
    
    # query to get the trip the user joined 
    mysql=connectToMySQL('tripbud')
    query="SELECT * FROM trips JOIN trip_joins ON trips.id=trip_joins.trip_id WHERE trip_joins.user_id = %(user_id)s;"
    joined_trips= mysql.query_db(query, data)

    # query to get all the trips user didnt create or join
    mysql=connectToMySQL('tripbud')
    query="SELECT * FROM trips WHERE creator_id != %(user_id)s;"
    other_trips= mysql.query_db(query, data)

    return render_template("travels.html", user= user[0], created_trips= created_trips, joined_trips= joined_trips, other_trips= other_trips)


@app.route('/addtrip')
def addtrip():
    return render_template('add.html')

@app.route('/add', methods=["POST"])
def add():
    # validations
    error= False
    # if there is nothing in the destination form
    if len(request.form['destination']) < 1:
        flash("We need to go somewhere")
        error= True
    # if there is nothing in the description form
    if len(request.form['description']) < 1:
        flash('We need to do something')
        error= True
    # if there is something in the start date form
    if len(request.form['start_date']) > 0:
        # sets a variable start_date and uses the datetime.strptime() class method.
        # class method datetime.strptime(date_string, format) Returns a datetime corresponding to date_string, parsed according to format.
        start_date=datetime.strptime(request.form['start_date'],'%Y-%m-%d')
        # if the start date is before todays date
        # classmethod datetime.today() Returns the current local datetime
        if start_date < datetime.today():
            flash('Date cannot be in the past')
            error= True
    # if there is nothing in the form 
    else:
        flash("enter a start date")
        error=True
    # if there is nothing in the end date form
    if len(request.form['end_date']) > 0:
        end_date=datetime.strptime(request.form['end_date'],'%Y-%m-%d')
        # if the end date starts before the start date
        if end_date < start_date:
            flash("you cannot start before the END or end before the start or...?!?")
            error= True
    else:
        flash("enter an end date")
        error=True
    if error:
        print("there was an error")
        return redirect('/addtrip')

    # query to add a new trip
    mysql= connectToMySQL('tripbud')
    data={
        "destination": request.form['destination'],
        "description": request.form['description'],
        "start_date" : request.form['start_date'],
        "end_date"   : request.form['end_date'],
        "user_id"    : session['user_id']
    }
    query="INSERT INTO trips(destination, description, start_date, end_date, created_at, updated_at, creator_id) VALUES (%(destination)s, %(description)s, %(start_date)s, %(end_date)s, NOW(), NOW(), %(user_id)s);"
    mysql.query_db(query, data)
    return redirect('/travels')

@app.route('/join/<int:trip_id>')
def join(trip_id):
    # is this person already on the trip
    data={
        "user_id": session['user_id'],
        "trip_id": trip_id
    }
    mysql=connectToMySQL('tripbud')
    query="SELECT * FROM trip_joins WHERE user_id=%(user_id)s AND trip_id=%(trip_id)s"
    matching_joins = mysql.query_db(query, data)

    # if they are not already added to the trip, add them
    if len(matching_joins) == 0:
        mysql=connectToMySQL('tripbud')
        query=" INSERT INTO trip_joins VALUES(%(user_id)s, %(trip_id)s);"
        mysql.query_db(query, data)
    return redirect('/travels')

@app.route('/cancel/<int:trip_id>')
def cancel(trip_id):
    # cancels the trip
    mysql=connectToMySQL('tripbud')
    data={
        "user_id": session['user_id'],
        "trip_id": trip_id
    }
    query="DELETE FROM trip_joins WHERE user_id=%(user_id)s AND trip_id=%(trip_id)s"
    mysql.query_db(query, data)
    return redirect('/travels')

@app.route('/delete/<int:trip_id>')
def delete(trip_id):
    # delete all trip_joins for this trip first!
    # must be done first or else you will get a FK error
    mysql=connectToMySQL('tripbud')
    data={
        "user_id": session['user_id'],
        "trip_id": trip_id
    }
    query="DELETE FROM trip_joins WHERE trip_id=%(trip_id)s"
    mysql.query_db(query, data)
    return redirect('/travles')

    # delete from trips
    mysql=connectToMySQL('tripbud')
    query="DELETE FROM trips WHERE user_id=%(user_id)s AND id=%(trip_id)s"
    mysql.query_db(query, data)
    return redirect('/travels')

@app.route('/view/<int:trip_id>')
def trip(trip_id):
    # displays the trip information based off of the trips id.
    mysql=connectToMySQL('tripbud')
    data={
        "trip_id": trip_id
    }
    query="SELECT * FROM trips JOIN users ON users.id = trips.creator_id WHERE trips.id =%(trip_id)s"
    the_trip=mysql.query_db(query, data)
   
    # query displays all others joining that specific trip 
    mysql=connectToMySQL('tripbud')
    query="SELECT * FROM trip_joins JOIN users ON trip_joins.user_id = users.id WHERE trip_id= %(trip_id)s "
    users_joining= mysql.query_db(query, data)
    return render_template('trip.html', the_trip=the_trip[0], users_joining=users_joining)

#takes you back to travels-main page
@app.route('/back')
def back():
    return redirect('/travels')

# logs the user out by clearing session
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)