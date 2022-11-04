import os
from pstats import Stats
from sqlite3 import dbapi2
import time
import ast
import re
from cs50 import SQL
from flask import Flask, jsonify, message_flashed, render_template, request, session, redirect, flash
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from search import login_required, currentuser, checkdic, tempuser, temp_password_generator, admin_required, recently_added_CVEs, search_all, format_date, search_status_all, search_status_name, past_due, calculate_TotalCVEs, getnv
from flask_wtf import FlaskForm
from wtforms import SelectField
from datetime import date
import jinja2
import secrets
import string
from flask_mail import Mail, Message
import json
import string







# Configure application
app = Flask(__name__)

# Requires that "Less secure app access" be on
# https://support.google.com/accounts/answer/6010255
app.config["MAIL_DEFAULT_SENDER"] = 'leuldessalegn@gmail.com'
app.config["MAIL_PASSWORD"] = ''
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = 'leuldessalegn@gmail.com'
mail = Mail(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "secret"

Session(app)


db = SQL('sqlite:///tracker.db')


#Drop down for Type of User account
class Form(FlaskForm):
    account_type = SelectField('Account Type', choices=[('Admin', 'Administrator'), ('Read', 'Read-Only'),('Engineer','Implementation-Engineer')])
    status = SelectField('Status', choices=[('In-Progress', 'In-Progress'), ('Resolved', 'Resolved'), ('Past_Due', 'Past_Due'),('Recently Added', 'Recently Added')])
    admin_status = SelectField('Status', choices=[('In-Progress', 'In-Progress'), ('Resolved', 'Resolved'), ('Past_Due', 'Past_Due'),('Recently Added', 'Recently Added'),('Unassigned', 'Unassigned')])
    ticket_status = SelectField('Status', choices=[('In-Progress', 'In-Progress'), ('Resolved', 'Resolved')])
    Sys_log = SelectField('sys_log_type', choices=[('Search', 'Look-ups'), ('Account Registration', 'Account Registrations'),('Failed Login', 'Login Attempts'), ('Successful Login', 'Successful Login')])
    data_type = SelectField('engineer', choices=[('vulnerabilities', 'Vulnerabilities'), ('System Logs', 'System Logs')])


class Form_2(FlaskForm):
    system_type = SelectField('System Type', choices=[('H', 'Hardware'), ('S', 'Software'), ('N', 'Network'), ('O', 'Other')])
    vendor = SelectField('Vendor', choices=[])
    model = SelectField('Product', choices=[])
    engineer = SelectField('engineer', choices=[])





@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def home():
    account_type = session["Account_type"]
    cve_status = Form()
    form_2=Form_2()
    form_2.engineer.choices = [(engineer["Employee_Name"], engineer["Employee_Name"]) for engineer in db.execute("SELECT * FROM Users WHERE Company_id = ?", session["Company_id"])]
    form_2.engineer.choices.append(['All', 'All'])
    return render_template("dashboard.html", account_type=account_type, form_2=form_2,cve_status=cve_status, )


@app.route("/index")
@login_required
def index():
    return render_template("add_user.html")

@app.route("/list")
@admin_required
#function displays all current CVEs ready to be assigned
def added_list():
    company = session["Company_id"]
    account_type = session["Account_type"]
    inventory= db.execute("SELECT * FROM added_CVE WHERE Company_id = ?",company)
    return render_template("list.html", inventory=inventory, account_type=account_type)

@app.route("/model/<vendor>")
def model(vendor):
    print(vendor.upper())
    company_id = session["Company_id"]
    models=db.execute("SELECT Symbol,product FROM Product WHERE Symbol = ? AND Company_id = ?", vendor[0:2].upper(), company_id)
    print(models)
    modelsArray=[]
    for model in models:
        modelObj = {}
        modelObj["Vendor"] = model["Symbol"]
        modelObj["Model"] = model["product"]
        modelsArray.append(modelObj)

    return jsonify({'models':modelsArray})


@app.route("/add_user", methods=["GET", "POST"])
@admin_required
def add_user():
    user=session["user_name"]
    account_type = session["Account_type"]
    form_2 = Form_2() # Calls Form for Vendor drop down
    form = Form()      # Drop choice down for all User Account Type
    Company_id=session["Company_id"]
    # Queries all engineers in the database for the current company profile
    form_2.engineer.choices = [(engineer["id"], engineer["Employee_Name"]) for engineer in db.execute("SELECT * FROM Users WHERE Company_id = ?", Company_id)]
    if request.method == "POST":
            #Uses get to get all information filled out in the Add user Form
            account = form.account_type.data
            first_name = request.form.get("fname")
            last_name = request.form.get("lname")
            user_id = request.form.get("user_id")
            email= request.form.get("E-mail")
            if not request.form.get("fname"):
                #check if first name is in form
                error1 = "Please Enter First Name"
                return render_template("add_user.html", user=user, form=form,form_2=form_2, error1=error1, account_type= account_type)
            #check if last name is in form
            if not request.form.get("lname"):
                error2 = "Please Enter Last Name"
                return render_template("add_user.html", user=user,form=form,form_2=form_2, error2=error2, account_type= account_type)

            if not request.form.get("E-mail"):
                error2 = "Please Enter your E-mail"
                return render_template("add_user.html", user=user,form=form,form_2=form_2, error2=error2, account_type= account_type)

            #Check if user id is in form
            elif not request.form.get("user_id"):
                error3='Please Enter A User ID'
                return render_template("add_user.html", user=user, form=form,form_2=form_2, error3=error3, account_type= account_type)
            else:
                username = last_name + ", " + first_name
                #Check to see if the account being created exists in temp DB or user profile database
                check_temp_db = db.execute("SELECT Company_id, Employee_Name, User_id, Account_Type FROM temp_account WHERE Company_id = ? AND Employee_Name = ? AND User_id = ? AND Account_Type = ?", Company_id,username, user_id, account)
                check_account_db = db.execute("SELECT Company_id, Employee_Name, User_id, Account_Type FROM users WHERE Company_id = ? AND Employee_Name = ? AND User_id = ? AND Account_Type = ?", Company_id,username, user_id, account)
                check_duplicate_id= db.execute("SELECT User_id FROM users WHERE User_id = ? AND Company_id = ?", user_id, Company_id)

                #check to see if user id is already taken
                print(check_temp_db)
                print(check_account_db)
                print(check_duplicate_id)
                if check_temp_db or check_account_db:
                    error4="Account already exists. Please use a different name and ID"
                    return render_template("add_user.html",user=user, form=form, form_2=form_2, error4=error4, account_type= account_type)
                if check_duplicate_id:
                    error5="User ID unavailable. Please ENTER a different user id"
                    return render_template("add_user.html",user=user, form=form, form_2=form_2, error5=error5, account_type= account_type)
                else:
                    pwd = temp_password_generator()

                    #Create an account with a temporary password and store it in a temp database folder until user logs in for the first time and changes password
                    db.execute("INSERT INTO temp_account(Company_id, Employee_Name, User_id, hash, Account_Type, Email) VALUES(?,?,?,?,?,?)",Company_id, username, user_id, pwd, account, email)
                     # Send email
                    message = Message(recipients= [request.form.get("E-mail")], subject= "You are registered!", body="Welcome to the CVSS Database. You have been registered as " + account + "Please use the following as your Temporary Password " + pwd)
                    mail.send(message)
                    error5="User Successfully Added"
                    return render_template("add_user.html",user=user, form=form,form_2=form_2, error5=error5, account_type= account_type)

    return render_template("add_user.html",user=user,form=form,list=list, form_2=form_2, account_type= account_type)



@app.route("/Assign_cve", methods=["GET", "POST"])
@admin_required
def Assign_cve():
    account_type = session["Account_type"]
    form = Form() # Drop choice down for all User Account Type
    form_2 = Form_2() # Calls Form for Vendor drop down
    res = request.form.get("list") #return all CVE vulnerabilities added to current company profile enviroment
    description = request.form.get("description")
    print(res)
    print(description)
    list={"CVE_id":res}
    user=session["user_name"]
    Company_id=session["Company_id"]
    form_2.vendor.choices = [(vendor["Vendor"], vendor["Vendor"]) for vendor in db.execute("SELECT * FROM Vendor WHERE Company_id = ?", Company_id)]
    time.sleep(4)
    form_2.model.choices = [(model["product"], model["product"]) for model in db.execute("SELECT * FROM Product WHERE Symbol = ? AND Company_id = ?", form_2.vendor.choices[0][0], Company_id)]
    form_2.engineer.choices = [(engineer["id"], engineer["Employee_Name"]) for engineer in db.execute("SELECT * FROM Users WHERE Company_id = ? AND Account_Type = ?", Company_id, 'Engineer')]
    return render_template("Assign_cve.html", description=description, user=user,list=list["CVE_id"],form=form, form_2=form_2, account_type= account_type)

@app.route("/Assign", methods=["GET", "POST"])
@admin_required
def Assign():
    if request.method == "POST":
        account_type = session["Account_type"]
        form = Form() # Drop choice down for all User Account Type
        form_2 = Form_2() # Calls Form for Vendor drop down
        res = request.form.get("list") #return all CVE vulnerabilities added to current company profile enviroment  aka
        list={"CVE_id":res}
        get_description = request.form.get("description")
        description={"description":get_description}
        print(description)
        user=session["user_name"]
        Company_id=session["Company_id"]
        form_2.vendor.choices = [(vendor["Vendor"], vendor["Vendor"]) for vendor in db.execute("SELECT * FROM Vendor WHERE Company_id = ?", Company_id)]
        time.sleep(4)
        form_2.model.choices = [(model["product"], model["product"]) for model in db.execute("SELECT * FROM Product WHERE Symbol = ? AND Company_id = ?", form_2.vendor.choices[0][0], Company_id)]
        form_2.engineer.choices = [(engineer["id"], engineer["Employee_Name"]) for engineer in db.execute("SELECT * FROM Users WHERE Company_id = ? AND Account_Type = ?", Company_id, 'Engineer')]
        #returns all the user selected data from the FLASK form
        vendor = request.form.get("vendor")
        model=request.form.get("model")
        date= request.form.get("ddate")
        print("TEST")
        print(model)
        engineer= form_2.engineer.data
        print(date)
        if not date or model=='<select id=':
            error1 = "Please select a Due Date"
            return render_template("Assign_cve.html", user=user, error1=error1,list=list["CVE_id"],form=form, form_2=form_2, account_type= account_type)
        else:
            #Query the name of engineer that is being assigned a CVE
            user_id = db.execute("SELECT Employee_Name, User_id, Account_Type FROM users WHERE id=? AND Company_id = ?",engineer, Company_id)
            check = db.execute("SELECT cve_id FROM cve_recored WHERE cve_id = ?", list["CVE_id"])
            assigned = db.execute("SELECT cve_id FROM Work_log WHERE cve_id = ? AND Company_id = ?", list["CVE_id"], Company_id)
            if assigned:
                error2 = list["CVE_id"] + " " + "is already assigned"
                return render_template("Assign_cve.html",error2=error2, user=user, list=list["CVE_id"], form=form, form_2=form_2, account_type= account_type)
            if check:
                #Assign a CVE to the engineer and store it in the work log database
                db.execute("INSERT INTO Work_log(Company_id, CVE_id, User_id, Vendor, Model, Implementation_due_date, Status) VALUES(?,?,?,?,?,?,?)",Company_id, list["CVE_id"],user_id[0]["User_id"], vendor, model, date, "In-Progress")
                error2 = list["CVE_id"] + " " + "Sucessfully Assigned"
                db.execute("DELETE FROM added_CVE WHERE CVE_id = ?", list["CVE_id"])
                return render_template("Assign_cve.html",error2=error2, user=user, list=list["CVE_id"], form=form, form_2=form_2, account_type= account_type)
            else:
                db.execute("INSERT INTO cve_recored(cve_id, description) VALUES(?,?)", list["CVE_id"], description["description"])
                 #Assign a CVE to the engineer and store it in the work log database
                db.execute("INSERT INTO Work_log(Company_id, CVE_id, User_id, Vendor, Model, Implementation_due_date, Status) VALUES(?,?,?,?,?,?,?)",Company_id, list["CVE_id"],user_id[0]["User_id"], vendor, model, date, "In-Progress")
                error2 = list["CVE_id"] + " " + "Sucessfully Assigned"
                db.execute("DELETE FROM added_CVE WHERE CVE_id = ?", list["CVE_id"])
                return render_template("Assign_cve.html",error2=error2, user=user, list=list["CVE_id"], form=form, form_2=form_2, account_type= account_type)

    return render_template("Assign_cve.html", user=user,list=list["CVE_id"],form=form, form_2=form_2, account_type= account_type)


@app.route("/change_password", methods=["GET","POST"])
def change_password():
    user = session["user_account"]
    if request.method == "POST":
        new_password=request.form.get("npass")
        password_again=request.form.get("npass2")
        username=request.form.get("username")
        if not request.form.get("npass"):
            error1 = "Please Enter Passord"
            return render_template("login.html", error1=error1)
        #check if user name is in form
        if not request.form.get("npass2"):
            error2 = "Please Enter Password Again"
            return render_template("login.html", error2=error2)
        if new_password == password_again and len(new_password) > 7 and (bool(re.match('^[a-zA-Z0-9@$#&]*$',new_password))==True):
            #create hash for password
            hash = generate_password_hash(new_password,method='pbkdf2:sha256',salt_length=16)
            check=tempuser(user)
            check2= currentuser(user)
            if check2:
                db.execute("UPDATE users SET hash = ? WHERE User_id = ?", user, hash)
            if check:
                db.execute("INSERT INTO users(Company_id, Employee_name, user_id, hash, Account_Type) VALUES(?, ?, ?, ?, ?)", check[0]["Company_id"], check[0]["Employee_Name"], check[0]["User_id"], hash, check[0]["Account_Type"])
                session_profile = db.execute("SELECT * FROM users WHERE user_id = ?", check[0]["User_id"])
                session["user_id"] = session_profile[0]["id"]
                session["Company_id"] = session_profile[0]["Company_id"]
                session["user_name"] = session_profile[0]["Employee_Name"]
                session["user_account"] = session_profile[0]["User_id"]
                session["Account_type"] = session_profile[0]["Account_Type"]
                db.execute("DELETE FROM temp_account WHERE User_id = ?", user)
                return render_template("index.html")


    return render_template("login.html")

@app.route("/add", methods=["GET", "POST"])
@admin_required
def add():
    if request.method == "POST":
       Company_id = session["Company_id"]
       result = request.form.get("list")
       res = ast.literal_eval(result)
       select = session["select"]
       user_id = session["user_id"]
       user_name =session["user_name"]
       account_type = session["Account_type"]
    if result:
            check_unassigned= db.execute("SELECT cve_id FROM added_CVE WHERE cve_id = ? AND Company_id = ?", res["cve_id"], Company_id)
            check_work_log = db.execute("SELECT CVE_id FROM Work_log WHERE CVE_id =? AND Company_id = ?", res["cve_id"], Company_id)
            if check_unassigned or check_work_log:
                error = "Unable to add " + res["cve_id"] + ". CVE already exists in Record"
                return render_template("search.html",select=select, error=error, user= user_name, account_type= account_type)

            else:
                check_user = db.execute("SELECT Company_id FROM users WHERE id = ?", user_id)
                print(check_user)
                db.execute("INSERT INTO added_CVE(Company_id, cve_id, description) VALUES(?,?,?)",check_user[0]["Company_id"], res["cve_id"], res["description"])
                error =  res["cve_id"] + " added!"
                return render_template("search.html", select=select, error=error, user= user_name, account_type= account_type)
    else:
           return render_template("search.html", user= user_name, account_type= account_type)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    user= session["user_account"]
    account_type = session["Account_type"]
    company_id = session["Company_id"]
    if request.method == "POST":
        search = request.form.get("search")
        if 'STARTDATE' and 'ENDDATE' in search.upper():
            select = getnv(search.replace(" ",""), search)
            session["select"] = select
            search_count = len(select)
            return render_template("search.html", search_count=search_count, select=select, account_type=account_type)
        if 'Year' and 'System' in search:
            select = db.execute("SELECT * FROM cve_recored WHERE cve_id LIKE ? AND Description LIKE ? LIMIT 35", "%" + search[5:10].replace(" ","") + "%", "%" + search[19:] + "%")
            print(select)
        else:
            select = db.execute("SELECT * FROM cve_recored WHERE cve_id LIKE ? LIMIT 35", "%" + search + "%")
            db.execute("INSERT INTO System_log(Company_ID, Log_type, Person_id, Action) VALUES(?,?,?,?)", company_id, "Search", user, user +  "searched for: "+ search)
            session["select"] = select
    else:
        select = []
    return render_template("search.html", select=select, account_type=account_type)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        company = request.form.get("company")
        email= request.form.get("E-mail")
        username = request.form.get("username")
        password = request.form.get("password")
        password_again = request.form.get("password_again")
        #check company name is in form
        if not request.form.get("company"):
            error = "Company Name Required"
            return render_template("register.html", error=error)
        if not request.form.get("E-mail"):
            error = "Email Required"
            return render_template("register.html", error=error)
        #check if user name is in form
        if not request.form.get("username"):
            error_2 = "User Name Required"
            return render_template("register.html", error_2=error_2)
        # Ensure password was submitted
        elif not request.form.get("password"):
            error_3='Username and/or Password required'
            return render_template("register.html", error_3=error_3)
        #check to see if company name already exists in the database
        rows = db.execute("SELECT Company_Name FROM Company WHERE Company_Name = ?", company)
        if rows:
           error_4 = "Company is already registered"
           return render_template("register.html", error_4=error_4)
        #check to see if user id has been taken
        check_user = db.execute("SELECT Company_id, User_id FROM users WHERE Company_id = (SELECT id FROM Company WHERE Company_Name = ?) AND User_id = ?", company, username)
        if len(rows) == 1 and check_user[0]["Company_id"] == company and check_user[0]["User_id"] == username:
            error_5 = "User Name is not available"
            return render_template("register.html", error_5=error_5)
        #check to see if password was typed twice correctly and matches password criteria
        if password == password_again and len(password) > 7 and (bool(re.match('^[a-zA-Z0-9$@]*$',password))==True):
            #create hash for password
            hash = generate_password_hash(password,method='pbkdf2:sha256',salt_length=16)
            #create an account for new company and make the creater of account the administrator
            db.execute("Insert INTO Company(Company_name, Systems) VALUES(?, ?)", company, "Windows")
            time.sleep(2)
            c_id = db.execute("SELECT id FROM Company WHERE Company_name = ?", company)
            e_name = last_name + ", "+ first_name
            db.execute("INSERT INTO users(Company_id, Employee_name, user_id, hash, Account_Type, Email) VALUES(?, ?, ?, ?, ?, ?)", c_id[0]["id"], e_name, username, hash, "Admin", email)
            time.sleep(2)
            get_user_info = db.execute("SELECT * FROM users WHERE user_id = ?",username)
            db.execute("INSERT INTO System_log(Company_ID, Log_type, Person_id, Action) VALUES(?,?,?,?)", get_user_info[0]["Company_id"], "Account Registration", get_user_info[0]["user_id"], "Admin Account Created For New Company" )
            return render_template("homepage.html")
        else:
           error_6='Invalid Password'
           return render_template("register.html", error_6=error_6)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username=request.form.get("username")
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # check to see if the password is a temporary password due to an account creation or a password reset
        if request.form.get("password"):
            print("true")
            print(request.form.get("password"))
            # Query temporary username used for password resets and new accounts for username
            tempname = tempuser(request.form.get("username"))
            if tempname:
                session["user_account"] = tempname[0]["User_id"]
                session["Company_id"] = tempname[0]["Company_id"]
                return render_template("login.html", temp = tempname)
            currentname = currentuser(request.form.get("username"))
            print(currentname)
            if currentname == 'false':
                 error1= "invalid username and/or password"
                 currentname = username
                 return render_template("login.html", error1 = error1)
            else:
                check_password_hash(currentname[0]["hash"], request.form.get("password"))


        # Remember which user has logged in
        session["user_id"] = currentname[0]["id"]
        session["Company_id"] = currentname[0]["Company_id"]
        session["user_name"] = currentname[0]["Employee_Name"]
        session["user_account"] = currentname[0]["User_id"]
        session["Account_type"] = currentname[0]["Account_Type"]
        db.execute("INSERT INTO System_log(Company_ID, Log_type, Person_id, Action) VALUES(?,?,?,?)", currentname[0]["Company_id"], "Successful Login", currentname[0]["User_id"], currentname[0]["User_id"] + " Succesfully logged in")
        # Redirect user to home page
        cve_status = Form()
        form_2=Form_2()
        form_2.engineer.choices = [(engineer["Employee_Name"], engineer["Employee_Name"]) for engineer in db.execute("SELECT * FROM Users WHERE Company_id = ?", session["Company_id"])]
        form_2.engineer.choices.append(['All', 'All'])
        return render_template("dashboard.html", form_2=form_2,cve_status=cve_status, account_type = session["Account_type"])
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def assigned_cve():
    cve_status = Form()
    form_2 = Form_2()
    account_type = session["Account_type"]
    company_id = session["Company_id"]
    user = session["user_name"]
    form_2.engineer.choices = [(engineer["Employee_Name"], engineer["Employee_Name"]) for engineer in db.execute("SELECT * FROM Users WHERE Company_id = ?", company_id)]
    form_2.engineer.choices.append(['All', 'All'])
    status_choice = {}
    recently_added = []
    status = []
    print(account_type)
    past_due_cves = search_status_all(company_id, "In-Progress")

    q = request.args.get("q")

    for row in past_due_cves:
        if past_due(row["Implementation_due_date"]) == "Past_Due":
            db.execute("UPDATE work_log SET Status = 'Past_Due' WHERE company_id = ? and CVE_id = ?", company_id, row['CVE_id'])
    #Loads the available Dashboard for Engineer Accounts
    if account_type == 'Engineer':
        total_cve = calculate_TotalCVEs(user, company_id)
        q = request.args.get("q")
        print(q)
        if q in ["In-Progress", "Resolved", "Past_Due"]:

            status_choice = db.execute("SELECT Work_log.*, users.Employee_Name FROM work_log INNER JOIN users ON users.User_id=Work_log.User_id WHERE Work_log.Status= ? AND Work_log.Company_id = ? AND Work_log.user_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ? )", q, company_id, user, company_id)
            print(status_choice)
            return jsonify(status_choice,total_cve)
        elif q == "Recently Added":
            status_choice = recently_added_CVEs(search_status_name(company_id, "In-Progress", user))
            print(status_choice)
            return jsonify(status_choice,total_cve)
    #Loads the available Dashboard for Administrator accounts
    if account_type == 'Admin':
        if request.method == "POST":
           q = request.get_json("body")
           if q["Name"] != 'NULL':
               total_cve = calculate_TotalCVEs(q["Name"], company_id)
           print("qqname")
           print(q)
           if q["Status"] == "Recently Added":
            if q['Name'] == "All":
                #Query all  CVEs required for current user(engineer)
                status_choice= search_all(company_id)
                status_choice = recently_added_CVEs(status_choice)
            else:
                status_choice = recently_added_CVEs(search_status_name(company_id, 'In-Progress', q["Name"]))
            #Calculate total CVEs assigned
            status = recently_added_CVEs(status_choice)
            status = format_date(status)
            total_cve = calculate_TotalCVEs(q["Name"], company_id)
            return jsonify(status, total_cve)

        if not q:
            q = {'Status': 'In-Progress', 'Name': 'All'}
            print("qname")
            status_choice = format_date(search_status_all(company_id, q["Status"]))
            total_cve = calculate_TotalCVEs(q["Name"], company_id)
            return render_template("dashboard.html", form_2=form_2,cve_status=cve_status, account_type = session["Account_type"], total_cve=total_cve, user=user)

        if q["Name"] == "All" and q["Status"] != 'Unassigned':
            print(q)
            status= format_date(search_status_all(company_id, q["Status"]))
            total_cve = calculate_TotalCVEs(q["Name"], company_id)
            return jsonify(status, total_cve)

        if q["Status"] == 'Unassigned':
            total_cve = calculate_TotalCVEs('ALL', company_id)
            status = db.execute("SELECT * FROM added_CVE WHERE Company_id = ?",company_id)
            check = db.execute("SELECT * FROM Product WHERE Company_id = ?", company_id)
            print(check)
            if not check:
                stat="None"
                return jsonify(status, total_cve, stat)
            else:
                stat = "something"
                return jsonify(status, total_cve,stat)

        if q["Status"]  == 'System Logs':
            print(q)
            status = db.execute("SELECT * FROM System_log WHERE Company_id = ?", company_id)
            print(status)
            return jsonify(status)
        else:
            status_choice = format_date(search_status_name(company_id, q["Status"], q["Name"] ))
            print("qname")
            print(q["Name"])
            total_cve = calculate_TotalCVEs(q["Name"], company_id)
            return jsonify(status_choice, total_cve)


    return  render_template("dashboard.html", data = json.dumps(account_type), cve_status=cve_status, form_2=form_2, recently_added=recently_added, account_type = account_type, user=user)

@app.route("/open_ticket", methods=["GET", "POST"])
@login_required
def open_ticket():
    cve_status = Form()
    user = session["user_name"]
    account_type = session["Account_type"]
    cve_number = request.form.get("list")
    if account_type == 'Admin':
        status = format_date(db.execute("SELECT Work_log.*, users.Employee_Name FROM work_log INNER JOIN users ON users.User_id=Work_log.User_id WHERE Work_log.CVE_id= ? AND Work_log.Company_id = ? ",cve_number , session["Company_id"]))
        comments = db.execute("SELECT * FROM comments WHERE cve_id = ? AND Company_id = ?", cve_number, session["Company_id"])

    else:
        status = format_date(db.execute("SELECT Work_log.*, users.Employee_Name FROM work_log INNER JOIN users ON users.User_id=Work_log.User_id WHERE Work_log.CVE_id= ? AND Work_log.Company_id = ? AND Work_log.user_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ? )",cve_number , session["Company_id"], user, session["Company_id"]))
        comments = db.execute("SELECT * FROM comments WHERE cve_id = ? AND Company_id = ?", cve_number, session["Company_id"])

    return render_template("cve_form.html", status=status, comments=comments, cve_status=cve_status, account_type = account_type)

@app.route("/add_comment", methods=["GET", "POST"])
@login_required
def add_comment():
    user = session["user_account"]
    company_id = session["Company_id"]
    if request.method == "POST":
       form = request.get_json("body")
       if form["current"] != form["change"]:
        db.execute("UPDATE Work_log SET Status = ? WHERE CVE_id = ? AND Company_id = ?", form["change"], form["cve_id"][1:], company_id)
        db.execute("INSERT INTO System_log(Company_ID, Log_type, Person_id, Action) VALUES(?,?,?,?)", company_id, "Ticket Status Change", user, "A ticket associated with" + form["cve_id"] +  "was updated with a new Status")

       if not form["form"]:
        comments = db.execute("SELECT * FROM comments WHERE CVE_id = ? AND Company_id = ?",  form["cve_id"][1:], company_id)
        return jsonify(comments)
       else:
        db.execute("INSERT INTO comments(Company_id, cve_id, User_id, comment) VALUES(?,?,?,?)", company_id, form["cve_id"][1:], user, form["form"])
        db.execute("INSERT INTO System_log(Company_ID, Log_type, Person_id, Action) VALUES(?,?,?,?)", company_id, "Ticket Log", user, "A ticket associated with" + form["cve_id"] +  "was updated with a new log" )
        comments = db.execute("SELECT * FROM comments WHERE CVE_id = ? AND Company_id = ?",  form["cve_id"][1:], company_id)

    return jsonify(comments)

@app.route("/add_system",methods=["GET", "POST"])
@login_required
def add_system():
        user = session["user_account"]
        company_id = session["Company_id"]
        account_type = session["Account_type"]
        check_current = db.execute("SELECT Vendor FROM vendor WHERE Company_id = ?", company_id)
        check_product = db.execute("SELECT product FROM Product WHERE Company_id = ?", company_id)
        if not check_current:
            check_current = {'Stat': "None"}
        if request.method == "POST":
            form = request.get_json("body")
            if form:
                if str(form["company"]).upper() in str(check_current).upper() and str(form["System"]).upper() not in str(check_product).upper():
                    db.execute("INSERT into Product(company_id, Symbol, product) VALUES(?,?,?)", company_id, str(form["company"])[0:2].upper(), str(form["System"]).title())
                    return jsonify("True")
                if str(form["System"]).upper() in str(check_product).upper():
                     print("test")
                     return jsonify("False")
                else:
                        db.execute("INSERT INTO Vendor(company_id,Symbol, vendor) VALUES(?,?,?)", company_id, str(form["company"])[0:2].upper(), str(form["company"]).title())
                        db.execute("INSERT into Product(company_id, Symbol, product) VALUES(?,?,?)", company_id, str(form["company"])[0:2].upper(), str(form["System"]).title())
                        return jsonify("True")
            else:
                return jsonify("Please fill out form")

        return render_template("add_system.html", account_type = account_type)
