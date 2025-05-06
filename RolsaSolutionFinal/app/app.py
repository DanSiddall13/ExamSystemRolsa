# All of our imports

from datetime import date
import time
from os import error
from time import sleep
from flask import Flask, render_template, request, flash, get_flashed_messages, session, redirect, url_for
import re
import sqlite3
import hashlib
import json

# Flask and database initialization.
key = 'aPv7Mws0?pb$d'
app = Flask(__name__)
app.secret_key = key
#################################################################### Use sessions to allow me to decide wether someone is logged on or not and then what to show based on that.
 


############### Functions - Here we will keep all our functions ###############



# This function was made using Copilot and uses regular expressions to check if an email is formatted how it should be
def is_valid_email(email):
    email = email.lower()
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    #This checks the emal against the expression and returns whether is formatted correctly or not
    if re.match(email_regex, email):
        return True
    else:
        return False

# This function is used to check the password fits all the rules, returning a message if it dosen't
def hashncheck(password):
    special = 0
    upper = 0
    num = 0
    passtemp = []
    # A check to remove any spaces from the input password
    for i in range(len(password)):
        if password[i] != " ":
            passtemp.append(password[i])
            print(passtemp)

    password=passtemp
    password = "".join(password)
    print(password)
    # This check the length of the password
    if len(password) > 30 or len(password) < 8:
        return ("keep your password with 8-30 characters of length")

    # This logic checks there an enough numbers, uppercase and special characters.
    for i in range(len(password)):
        if password[i].isnumeric() == True:
            num = num + 1
        elif password[i].isupper() == True:
            upper = upper + 1
        elif password[i].isnumeric() == False and password[i].isalpha() == False:
            special = special + 1
     
    # These selection statements are used to determine which error message suits the user
    if special == 0:
        return ("Please have a special character in your password")
    elif upper == 0:
        return ("Please have an uppercase letter in your password")
    elif num == 0:
        return ("Please have a number in your password")
    else:
        # If the password passes all the checks then it is hashed, a fullstop is put infront of it and it is returned
        # The fullstop is there to distinguish between an error message and a hashed password.
        print(password)
        hashpass=hashlib.sha256(password.encode()).hexdigest()
        print(hashpass)
        return hashpass

# This function sanitises inputs by checking their length and then if they have any text commonly used in SQL injection
# And XSS
def inputSan(data):
    data = data.lower()
    print(data)
    print(len(data))
    inputregex=re.compile(r"^[A-Za-z0-9\s.,?()-]+$")
    if len(data) > 50 or len(data) < 2:
        print("1")
        return True
    elif inputregex.match(data):
        return False
    else:
        print("2")
        return True

def checklogin(): # this is used to check if users are logged in and updates information as so.
    try:
        if (session['loginData'] == {"loggedin":True}) or session['loginData']['loggedin'] == True:
            data=session['loginData']
            data.update(session['loginName'])
            data.update(session['loginID'])
            return data
        else:
            data={"loggedin":False}
            return data
    except:
            data={"loggedin":False}
            return data

############### These are all of our page routes which is what allows users to move throughout pages.###############

# This is a very basic one which has no function except to take users to the home page and show them that page.
@app.route('/')
@app.route('/Home')
def home():
    data=checklogin() # This is used every function in order for the navbar to know if the user is logged in or not and to show the appropriate item based on it
    return render_template("homePage.html", data=data) # data is passed through every render_template which has a navbar on it 

@app.route('/supportPage')
def support():
    data=checklogin()
    return render_template("homePage.html", data=data)

@app.route('/Booking')
def booking():
    data=checklogin() # This is the flask behind the booking page 
    if data['loggedin'] == False: # If user isnt logged in then it redirects them to login
        return redirect("/login")
    elif data['loggedin'] == True:# iF the user is logged in then it checks if they have an address linked to their account.
        conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT CAddress  FROM tblCust WHERE CustomerID = ?",(data['ID'], )) # look for the user in our database
        account = cursor.fetchone()
        conn.close()
        if account[0] == None:
            flash("Please update your account with an address","error")

        return render_template("Booking.html",data=data)
    else:
        return render_template("Booking.html",data=data)

@app.route('/bookingproc', methods=['POST'])
def bookingproc():
    flag = True
    if request.method == 'POST':
       bookingType = request.form.get('type')
       productType = request.form.get('prod')
       bookingDate = request.form.get('date')
       bookingDate = bookingDate[0:10]
       today = time.strftime("%Y-%m-%d")
       bookingDate[0:10]
       if today > bookingDate or today == bookingDate: # This is used to check the booking date and to ensure that is in the future
           flag = False
           flash("Please choose a date in the future ","error") # Add notes in the log and add flash messages on the booking page
       else:
            bookingData = []
       if flag == True:
           ID = session['loginID']['ID']
           conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
           cursor = conn.cursor()
           cursor.execute("SELECT CustomerID, CAddress FROM tblCust WHERE CustomerID = ?",(ID,)) # Selects the address and customer id from the users table
           data = cursor.fetchone()
           if data:
               bookingData.append(data[0])
               bookingData.append(productType)
               bookingData.append(bookingType)
               bookingData.append(data[1])
               bookingData.append(bookingDate)
           cursor.execute("INSERT INTO tblBookings(CustomerID,Product,BookingType,CAddress,Date) VALUES(?,?,?,?,?)", bookingData) # Puts all the booking data into the database.
           conn.commit()

           conn.close()

           return redirect('/account')
    return redirect('/Booking')

# This is our login/ register page  and contains a form which takes people who are registering to /regnew
@app.route('/login', methods=["GET","POST"])
def login():
    data = checklogin()
    if data['loggedin'] == True:
        return redirect("/Home")

    return render_template("Login.html", data=data)

# This is the logic for our logging in and it gets the email and password and hashed it.
@app.route('/loginlogic', methods=['GET','POST'])
def loginlogic():              
    flag=True
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        msg = hashncheck(password)
        if msg == False:
            flash(msg,"error")
            return render_template("login.html")
        elif type(msg) == str:
            hashpass=msg

        if is_valid_email(email) == False:
            flash("Invalid email format", "error")
            flag = False

    if flag == False:
        return render_template("login.html")
    else:         #  if all checks are completed then
        conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT CustomerID,CfirstName FROM tblCust WHERE CEmail = ? AND CPassHash = ?",(email,hashpass)) # look for the user in our database
        account = cursor.fetchone()
        conn.close()
        if type(account) != type(None): # if there is an account then log in else flash incorrect and redirect to login again.
            session['loginData'] = {'loggedin':True}
            session['loginID'] = {'ID':account[0]}
            session['loginName'] = {'fname':account[1]}
            return redirect(url_for("home"))
        else: # if no account was found it was incorrect
            flash("Incorrect email/password","error")
            return render_template("login.html")



@app.route("/register", methods=['GET','POST'])
def register():
    data = checklogin()
    if data['loggedin'] == True:
        return redirect("/Home")
    data={}
    return render_template('register.html', data=data)
# Here we get the form data from /login 
@app.route('/regnew', methods=['GET','POST'])
def regnew():
    # This flag is used to determine whether account creation was successful or not using true and false as such
    flag = True
    # if information is posted to here then it will run
    if request.method == "POST":
        #Gets all the form fields
        Fname = request.form.get("Fname")
        Lname = request.form.get("Lname")
        email = request.form.get("email")
        password = request.form.get("password")
        data = {"Fname":Fname, "Lname" :Lname, "email":email}
        #hashes and checks the password
        msg = hashncheck(password)
        print(msg)
        print(len(msg))
        #if the msg starts with a . we know its a hashed password
        if len(msg) != 64:
            msg = msg
            flag=False
            flash(msg,"error")
            return render_template("register.html", data=data)
        elif len(msg) == 64:
            hashpass=msg
        # This contains the logic for checking which field is failing the sanitisation.
        if inputSan(Fname) == True:
            flash("first name Must be within 2-50 characters long and avoid apostrophies, commas and speech marks",category="error")
            flag = False
            return render_template("register.html", data=data)
        if inputSan(Lname) == True:
            flash("Last name Must be within 2-50 characters long and avoid apostrophies, commas and speech marks",category="error")
            flag = False
            return render_template("register.html", data=data)

        if is_valid_email(email) == False:
            flash("Invalid email format please enter a valid email","error")
            flag = False
            return render_template("register.html", data=data)

            # this section of code allows us to check the accounts database to decide whether the email has been used under another account.
        conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT CEmail FROM tblCust WHERE CEmail = (?)", (email,))
        account = cursor.fetchone()
        conn.close()
        if type(account) != type(None):
            flag = False
            flash("Email is already used under an account","error")
            return render_template("register.html", data=data)

        if flag == True:
            #gets all user data into one list for easier insertion
            userData = []
            userData.append(Fname)
            userData.append(Lname)
            userData.append(email)
            userData.append(hashpass)
            # input the data into our customer table
            conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
            
            conn.execute("INSERT INTO tblCust(CfirstName,ClastName,CEmail,CPassHash) VALUES(?,?,?,?)", userData)
            #save the changes and close the database and then give a response to the user
            conn.commit()
            conn.close()
            flash("Account successfully registered","success")
            return render_template("register.html", data=data)
        else:
            return render_template("register.html", data=data)
    # if something unforeseen happens return the user back to the home page
    else:
        return render_template("homePage.html")

@app.route('/account', methods=['POST','GET']) # takes user to an account page with their information on it.
def account():
    data = checklogin()
    if data['loggedin'] == False:
        return redirect("/login")
    ID = data['ID']
    conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tblCust WHERE CustomerID = ?",(ID,))
    #save the changes and close the database and then give a response to the user
    conn.commit()
    data = cursor.fetchone()  
    cursor.execute("SELECT BookingID,Product, BookingType,Date FROM tblBookings WHERE CustomerID = ?",(ID,))  # This statement is done to allow users to see all their bookings
    bookingData = cursor.fetchall()
    
    if request.method == 'POST':# This is the code for deleting a booking which they have chosen to 
        try:
            item = request.form.get('booking')
            Bid=bookingData[int(item)][0]
            cursor.execute("DELETE FROM tblBookings WHERE BookingID = ?", (Bid,))
            conn.commit()
        except:
            return redirect('/account')
    conn.close()
    return render_template("account.html", data=data, bookingData = bookingData)

@app.route('/logOut')# logs the user out 
def logOut():

    session['loginData'] = {'loggedin':False}
    return redirect('Home')

@app.route('/changepass', methods=['POST','GET'])# logs the user out
def changepass():
    data = checklogin()
    if data['loggedin'] == True:
        if request.method == 'POST':
            password = request.form.get('password') #If the user is logged in then it will check the password hash it and then check the current password against the input password
            msg = hashncheck(password)
            if type(msg) == str:
                hashpass=msg
                Cid = data['ID']
            else:
                flash("Incorrect Password","error")
                return render_template("changepass.html")
            conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT CPassHash FROM tblCust WHERE CustomerID = ? AND CPassHash = ?",(Cid,hashpass,))
            #save the changes and close the database and then give a response to the user
            conn.commit()
            datapass = cursor.fetchone()  
            conn.close()
            if type(datapass) != type(None):  #if the input password is correct then it will update the database on the correct user.
                newPass = request.form.get('newpass')
                msg = hashncheck(newPass)
                if type(msg) == str:
                    hashpass=msg
                    conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
                    conn.execute("UPDATE tblCust SET CPassHash = ? WHERE CustomerID = ?", (hashpass,Cid))

                    #save the changes and close the database and then give a response to the user
                    conn.commit()
                    conn.close() 
                    flash("Password changed successfully","success")
                    return render_template('changepass.html')
            else:
                flash("incorrect Password account not found","error")
                return render_template('changepass.html')

        else:
             return render_template('changepass.html')
    else:
        return redirect('homePage.html')

    #Once a user enters their address it conducts a input check and if its false it redirects them home else it willput that address into their record.
@app.route('/addaddress', methods=['POST','GET'])
def addaddress():
    data = checklogin()
    if data['loggedin'] == False:
        return redirect("/Home")
    flag = False

    # if information is posted to here then it will run
    if request.method == "POST":
        custID = session['loginID']
        addr = request.form.get('addr')
        if inputSan(addr) == False:
            conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
        
            conn.execute("UPDATE tblCust SET CAddress = ? WHERE CustomerID = ?", (addr, custID['ID']))

             #save the changes and close the database and then give a response to the user
            conn.commit()
            conn.close() 
            return redirect('/account')
        else:
            return redirect('/account')
    else:

        return render_template("address.html")

    #This function simple once a user presses the delete button it checks if that user id is in the database and deletes it and it logs the user out of the account
@app.route('/deletion', methods=['POST','GET'])
def deletion():
    data = checklogin()
    if data['loggedin'] == False:
        return redirect("/Home")
    if request.method == 'POST':
        custID = session['loginID']
        conn = sqlite3.connect('Rolsa.db', check_same_thread=False)
        
        conn.execute("DELETE FROM tblCust WHERE CustomerID = ?", (custID['ID'],))
             #save the changes and close the database and then give a response to the user
        conn.commit()
        conn.close() 
        session['loginData'] = {"loggedin":False}
        return redirect('/Home')
    return render_template("deletion.html")

# All functions after this are simply navigational routes and are used for such purpose
@app.route('/SolarPanel')
def solarPanel():
    data = checklogin()
    return render_template("SolarPanel.html", data=data)


@app.route('/SolarInstall')
def solarInstall():
    data = checklogin()
    return render_template("SolarInstall.html", data=data)


@app.route('/EVpage')
def Evpage():
    data = checklogin()
    return render_template("EVpage.html", data=data)

@app.route('/EVChargers')
def Evchargers():
    data = checklogin()
    return render_template("EVchargers.html", data=data)

@app.route('/HEMPage')
def Hempage():
    data = checklogin()
    return render_template("HEMPage.html", data=data)

@app.route('/HemBat')
def HemBat():
    data = checklogin()
    return render_template("HemBat.html", data=data)

@app.route('/HeatPump')
def HeatPump():
    data = checklogin()
    return render_template("HeatPump.html", data=data)

@app.route('/GreenPage')
def GreenPage():
    data = checklogin()
    return render_template("GreenPage.html", data=data)

@app.route('/reduce')
def reduce():
    data = checklogin()
    return render_template("reduce.html", data=data)
@app.route('/CarbonCalc')
def CarbonCalc():
    data = checklogin()
    return render_template("CarbonCalc.html", data=data)



app.debug=True
app.run()
