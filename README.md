# SLOOTH
#### Video Demo:  https://youtu.be/Bc-pdPVGrOw
#### Description: Slooth is a Security vulnerabiltiy search application and management system specifically developed for organizations that want to stay ahead on the latest security vulnerabilties. It takes advantage of the the python NVD API wrapper utilizing the REST API to perform queries. The Application queries specifically for CVEs. The Common Vulnerabilities and Exposures (CVE)  is a dictionary or glossary of vulnerabilities that have been identified for specific code bases, such as software applications or open libraries. A unique identifier known as the CVE ID allows stakeholders a common means of discussing and researching a specific, unique exploit.

### **Overview**
Slooth is a web application written in Python 3. The web server is implemented using Flask, while the front-end part of the application, which is the dynamic page is written in HTML, CSS and relies heavily on JavaScript.
Slooth relies on OpenCVE's REST API for querying CVEs(https://docs.opencve.io/api/), and takes advantage of the many ways the API wrapper allows querying.  
### SLOOTH has 9 Tables for its Database:
**Company Table**- Records Registering organization’s information
 
**System Log Table**- Records all activities performed by users
 
**Vendor Table**- Records Vendor names added to Company’s inventory
 
**Product Table**- Records Vendor System added to Company’s inventory
 
**Work_log Table** – Records vulnerabilities assigned to engineer
 
**Added_CVE Table**- Records Vulnerabilities added to inventory
 
**Comments Table** – Records engineering notes for CVE
 
**Temp_account Table**- Records new accounts creation with a temporary password or accounts whose passwords have been reset. Record is deleted once password is either reset or created by user
 
**Users Table** – Records all user accounts
 
### Python Libraries:
 
 -*Nvdlib*(Python API wrapper utilizing the REST API provided by NIST for the National Vulnerability Database (NVD)
 
 -*datetime*
 
 -*secrets*
 
 -*RE(regular expressions)*
 
 -*flask_session*
 
 -*flask_wtf* 
 
 -*json* 
 
 -*string*
 
 -*Datetime*
 
 -*Jinja2*
 
 -*Functools*


### **Starting**
Once an account is created, it is highly recommended to also  create an engineer account for all IT security users who will be working on fixing the vulnerability if you want to utilize the built-in management system. A randomly generated temporary password will be emailed to the user once an account is created. An administrator will not be able to assign a CVE to an engineer until they have completed their account creation by logging in with their temp password and changing it. The next recommended step is to ADD all the systems in the client's enivorment by vendor and product into the account since each CVE that will be assigned to an engineer will be associated to a system. Example of a system is (Ex. Vendor: Linux Product: Ubuntu version 2.1).

### **Searching**
There are multiple ways a user can execute a search for CVEs.
 The simpliest way is to just type in the CVE number *(EX: CVE-1999-0001)*. If the cve number is typed in the correct format and a cve exists, it will return just one CVE
If the intent is to just search any CVEs, using the following format it is possible to search for a cve that was released within a certain time window. Typing the following *(Ex. Startdate: 01/10/2022 Enddate:03/01/2022)* will yield a result of all CVEs released within that time period. User must use the following format for dates(MM/DD/YYYY). Any other format will be rejected. 120 days is the maximum time window for searching by dates. A user can also add keywords in order to search for a specific type of vulnerability or a vulnerability affecting a certain application/system.*(Ex: SQL injection Startdate: 01/10/2022 Enddate:03/01/2022)*. Keywords must be typed before startdate or it will be ignored. Once a user finds a CVE that is relevant to their organization's systems and has an administrator level priviledge they can add it for tracking.

### **Adding your Organization's systems**

Slooth is also a ticketing/tracking type of system that allows an organization to assign the CVEs to security engineers within their organization. Each Ticket can be thought of as a task tracker. A ticket tracks the date it was assigned, the due date given for fixing vulnerability and a comment section for inputting daily work_logs or comment. An administrator account can check all the vulnerabilities added to account by navigating to the dashboard page and clicking on the filter by Status and selecting unassigned. A list of all vulnerabilities will populate the dashboard. Click on assign and select all the applicable options. Once it is assigned to an engineer, the engineer will be able to see it on their dashboard page. They have the option of adding work logs and closing the CVE ticket once work on fixing it has been completed.

### **Dashboard**

The interactive dashboard gives your organization an overall view of the number of CVEs that you have added, assigned, and completed. You can filter your dashboard by user and/or status in order to gain a better understanding of the workload. A recently added drop down option shows CVEs that were recently(7 days) assigned to an engineer. CVEs are automatically assigned a past_due date once they pass the assigned due date. There is also a system log avaialbe for an administrator account. A system log dropdown option will log and display all logins, Searches being conducted, and also any status changes of CVE tickets.


**Future Updates**

-Ability for Admins to reset passwords

-A news feed dashboard that shows all recently released CVEs relevent to Client based on their System

-Ability to send email/text notification of CVEs to a group or email

-Revamp ticket assignement to include groups and not just individuals

-Switch to none CS50 SQL of SQL Alchemey

-Deploy on a server

-Create an app as an alternative frontend

-Expand on ticketing form to allow uploads of work files and expand user input

-Revamp dashboard to include other stastical details that is helpful to the organiziation(average time to resolution, create scorecard based on severity of CVE among other variables to weigh score, breakdown of CVEs based on severity)

-Better search alograthim for more accurate search results

-"Bypassing" API Date range limitations






