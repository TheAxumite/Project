import os
import requests
import urllib.parse
from jinja2 import Environment, FileSystemLoader
from flask import redirect, render_template, request, session
from functools import wraps
import re
import nvdlib
from cs50 import SQL
import ast
import secrets
import string
import datetime
from datetime import date
db = SQL("sqlite:///tracker.db")

def getnv(CVE,search):

   
    r = nvdlib.searchCVE(keyword = search.split('Startdate', 1)[0], pubStartDate= datetime.datetime.strptime(' '.join([CVE[CVE.rfind("Startdate") + 10:CVE.rfind("Startdate") + 10+10],'01:01']),'%m/%d/%Y %H:%M'),
        pubEndDate = datetime.datetime.strptime(" ".join([CVE[CVE.rfind("Enddate") + 8:CVE.rfind("Enddate") + 8+10],'01:01']),'%m/%d/%Y %H:%M'),  exactMatch = True, key = '684ad781-5909-4349-85ed-8891c2ced5bd')
    cv2 = []
    for eachCVE in r:
        cve ={}
        cve['cve_id'] = eachCVE.id
        cve['description'] = eachCVE.cve.description.description_data[0].value
        cv2.append(cve)

    return(cv2)

def render(template):
    env = Environment(loader=FileSystemLoader("/finance/templates/"))
    jinja_template = env.get_template(template)
    jinja_template.globals.update(func_dict)
    template_string = jinja_template.render()
    return template_string

def check(string):

    special_char = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    # check string contains special characters or not
    if special_char.search(string) == None:
        return false
    else:
        return true

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("Account_type") != 'Admin':
            return redirect("/Access_denied")
        return f(*args, **kwargs)
    return decorated_function


def check(string):

    special_char = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
    # check string contains special characters or not
    if special_char.search(string) == None:
        return false
    else:
        return true

# Query the User database for user and return all fields
def currentuser(userid):
    check_user = db.execute("SELECT * FROM users WHERE user_id =?", userid)
    if check_user:
        return check_user
    else:
        return 'false'

def tempuser(userid):
    check_temp_2 = db.execute("SELECT * FROM temp_account WHERE User_id =?", userid)
    return check_temp_2


def checkdic(res):
      di={}
      di=res
      if isinstance(res, str):
            list = ast.literal_eval(res)
            return list
      else:
        return di

def temp_password_generator():
    letters = string.ascii_letters
    digits = string.digits
    special_chars = '@$#&'

    alphabet = letters + digits + special_chars

    # fix password length
    pwd_length = 12

    # generate a password string
    pwd = ''
    for i in range(pwd_length):
        pwd += ''.join(secrets.choice(alphabet))

    # generate password meeting constraints
    while True:
        pwd = ''
        for i in range(pwd_length):
            pwd += ''.join(secrets.choice(alphabet))
        if (any(char in special_chars for char in pwd) and
            sum(char in digits for char in pwd)>=2):
                break
    return pwd

def recently_added_CVEs(status_choice):
     status= status_choice
     recently_added = []
     for row in status:
        cve_time = row["Time_Stamp"]
        #Get today's time
        today = date.today()
        #format time to day/month/year
        current_time = today.strftime("%d/%m/%Y")
        calculate_month_day = [int(current_time[0:2]) - int(cve_time[8:10]), int(current_time[3:5]) - int(cve_time[5:7])]
        if row["Status"] == 'In-Progress' and  calculate_month_day[0] < 8 and calculate_month_day[1] == 0 :
         print("Stay")
         print(row)
         recently_added.append(row)
     return  recently_added

def search_all(company_id):
    search = db.execute("SELECT Work_log.*, users.Employee_Name FROM work_log INNER JOIN users ON users.User_id=Work_log.User_id WHERE Work_log.Company_id = ?", company_id)
    print(search)
    return search

def search_status_all(company_id, status):
    search = db.execute("SELECT Work_log.*, users.Employee_Name FROM work_log INNER JOIN users ON users.User_id=Work_log.User_id WHERE Work_log.Company_id = ? AND Work_log.Status = ? ",company_id, status)
    print("second")
    print(search)
    return search

def search_status_name(company_id, status, name):
    search = db.execute("SELECT Work_log.*, users.Employee_Name FROM work_log INNER JOIN users ON users.User_id=Work_log.User_id WHERE Work_log.Company_id = ? AND Work_log.Status = ? AND Work_log.user_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ? )",company_id, status, name, company_id)
    print(search)
    return search

def format_date(status_choice):
    formated_date = status_choice
    for row in formated_date:
        row["Implementation_due_date"] = row["Implementation_due_date"][5:7] + "-" + row["Implementation_due_date"][8:10] + "-" + row["Implementation_due_date"][0:4]
        row["Time_Stamp"] = row["Time_Stamp"][5:7] + "-" + row["Time_Stamp"][8:10] + "-" + row["Time_Stamp"][0:4]
    return formated_date

def format_date_list(date):
    formated_date = date
    formated_date["Implementation_due_date"] = formated_date["Implementation_due_date"][5:7] + "-" + formated_date["Implementation_due_date"][8:10] + "-" + formated_date["Implementation_due_date"][0:4]
    return formated_date

def calculate_TotalCVEs(name, company_id):
    if 'All' not in name:
        cve_dashboard = {'Total_CVE': db.execute("SELECT COUNT(CVE_id) as TotalCVEassigned FROM work_log WHERE User_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ? ) AND Company_id = ?", name, company_id, company_id),
                        'Total_in_progress': db.execute("SELECT COUNT(CVE_id) as TotalCVE_In_Progress FROM work_log WHERE User_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ?) AND Company_id = ? AND Status = 'In-Progress'", name, company_id, company_id),
                        'Total_Past_Due': db.execute("SELECT COUNT(CVE_id) as TotalCVE_Past_Due FROM work_log WHERE User_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ? ) AND Company_id = ? AND Status = 'Past_Due'", name, company_id,company_id),
                        'Total_Resolved': db.execute("SELECT COUNT(CVE_id) as Total_Resolved FROM work_log WHERE User_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ? ) AND Company_id = ? AND Status = 'Resolved'", name, company_id, company_id),
                        'Total_Recently_Added':len(recently_added_CVEs(db.execute("SELECT * FROM work_log WHERE User_id = (SELECT User_id FROM users where Employee_Name = ? AND Company_id = ?) AND Company_id = ? AND Status = 'In-Progress'", name, company_id, company_id))),
                        'Total_Unassigned':db.execute("SELECT COUNT(cve_id) as Total_Unassigned FROM added_CVE WHERE Company_id = ?",company_id)}


    else:


        cve_dashboard = {'Total_CVE': db.execute("SELECT COUNT(CVE_id) as TotalCVEassigned FROM work_log WHERE Company_id = ?",  company_id),
                        'Total_in_progress': db.execute("SELECT COUNT(CVE_id) as TotalCVE_In_Progress FROM work_log WHERE Company_id = ? AND Status = 'In-Progress'", company_id),
                        'Total_Past_Due': db.execute("SELECT COUNT(CVE_id) as TotalCVE_Past_Due FROM work_log WHERE Company_id = ? AND Status = 'Past_Due'", company_id),
                        'Total_Resolved': db.execute("SELECT COUNT(CVE_id) as Total_Resolved FROM work_log WHERE Company_id = ? AND Status = 'Resolved'", company_id),
                        'Total_Recently_Added':len(recently_added_CVEs(db.execute("SELECT * FROM work_log WHERE Company_id = ?",company_id))),
                        'Total_Unassigned':db.execute("SELECT COUNT(cve_id) as Total_Unassigned FROM added_CVE WHERE Company_id = ?",company_id)}

    print(cve_dashboard)
    return cve_dashboard

def past_due(Due_date):
    today = date.today()
    current_time = today.strftime("%m/%d/%Y")
    Due_dates = format_date_list({"Implementation_due_date": str(Due_date)})
    print(Due_dates['Implementation_due_date'])
    print(current_time)
    if int(Due_dates['Implementation_due_date'][6:10])- int(current_time[6:10]) <  0:
        print("year")
        return ("Past_Due")
    if int(Due_dates['Implementation_due_date'][6:10])- int(current_time[6:10]) >  0:
        return("In-Progress")
    elif int(Due_dates['Implementation_due_date'][0:2])- int(current_time[0:2]) < 0:
        print("month")
        return ("Past_Due")
    elif int(Due_dates['Implementation_due_date'][3:5])- int(current_time[3:5]) < 0 and int(Due_dates['Implementation_due_date'][0:2])- int(current_time[0:2]) == 0 and int(Due_dates['Implementation_due_date'][6:10])- int(current_time[6:10]) <  0:
        print("day")
        return ("Past_Due")
    else:
        return("In-Progress")

