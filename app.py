import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, send_from_directory, url_for, flash 
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


import threading
import sys

from werkzeug.utils import secure_filename
#
import subprocess 
from subprocess import Popen
from subprocess import PIPE
from itertools import islice
from threading import Thread
from queue import Queue, Empty


WORKERS=1
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

JOB_LOG=""
#app = Flask(__name__)



app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.JOB_LOG=""
app.COMMANDS=""
    
csrf = CSRFProtect(app)

# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize the database connection
db = SQLAlchemy(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Person, Company

@app.route('/', methods=['GET'])
def index():
    print('Request for index page received')
    all_records = Company.query.all()
    return render_template('index.html', records=all_records)

@app.route('/<int:id>', methods=['GET'])
def details(id):
    master = Company.query.where(Company.id == id).first()
    detail_rows = Person.query.where(Person.company_id == id)
    return render_template('details.html', master=master, detail_rows=detail_rows)

@app.route('/create', methods=['GET'])
def create_master():
    print('Request for add master record page received')
    return render_template('create_master.html')

@app.route('/add', methods=['POST'])
@csrf.exempt
def add_master():
    try:
        name = request.values.get('name')
        street_address = request.values.get('street_address')
        description = request.values.get('description')        
                
    except (KeyError):
        # Redisplay the question voting form.
        return render_template('create_master.html', {
            'error_message': "You must include all fields",
        })
    else:
        record  = Company()
        record.name = name
        record.street_address=street_address 
        record.description = description 
        
        db.session.add(record)
        db.session.commit()
        return redirect(url_for('details', id= record.id  ))

@app.route('/editdetails/<int:id>', methods=['GET','POST' ])
@csrf.exempt
def edit_details(id):
    row_details=""
    if request.method == 'POST':
        try:
            name = request.values.get('name')
            email = request.values.get('email')
            street_address = request.values.get('street_address')
            phone = request.values.get('phone')
            company_id = request.values.get('company_id')                      
        except (KeyError):
            #Redisplay the question voting form.
            return render_template('add_details.html', {
                'error_message': "Error adding record",
            })
        else:
            record = Person.query.filter_by(id=id).one()
            
            record.name = name 
            record.email = email
            record.street_address=street_address 
            record.phone = phone         
            record.modification_date=datetime.now()     
            record.company_id=company_id
            
            db.session.add(record)
            db.session.commit()
            return redirect(url_for('details', id=company_id))
    else:
            row_details  = Person.query.filter_by(id=id).one()
    return render_template('edit_details.html', row_details=row_details)

@app.route('/deletedetails/<int:id>', methods=['GET'])
@csrf.exempt
def delete_details(id):
    try:
        person = Person.query.filter_by(id=id).one()
        print(person)
        company_id=person.company_id 
        print("company_id:")
        print(company_id)
        db.session.delete(person)
        db.session.commit()
    except (KeyError):
        #Redisplay the question voting form.
        return render_template('add_details.html', {
            'error_message': "Error adding record",
        })
    return redirect(url_for('details', id=company_id))

@app.route('/details/<int:id>', methods=['POST'])
@csrf.exempt
def add_details(id):
    try:
        name = request.values.get('name')
        email = request.values.get('email')
        street_address = request.values.get('street_address')
        phone = request.values.get('phone')        
    except (KeyError):
        #Redisplay the question voting form.
        return render_template('add_details.html', {
            'error_message': "Error adding record",
        })
    else:
        record = Person()
        record.company_id = id
        record.name = name 
        record.email = email
        record.street_address=street_address 
        record.phone = phone         
        record.modification_date=datetime.now()        
        
        db.session.add(record)
        db.session.commit()

    return redirect(url_for('details', id=id))

@app.context_processor
def utility_processor():
    def star_rating(id):
        reviews = Measure.query.where(Measure.cm_id == id)

        ratings = []
        review_count = 0
        for review in reviews:
            ratings += [review.rating]
            review_count += 1

        avg_rating=0
        stars_percent=0
        #avg_rating = sum(ratings) / len(ratings) if ratings else 0
        #stars_percent = round((avg_rating / 5.0) * 100) if review_count > 0 else 0
        return {'avg_rating': avg_rating, 'review_count': review_count, 'stars_percent': stars_percent}

    return dict(star_rating=star_rating)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
                               
####
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@csrf.exempt
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #f = request.files['file'] puts the uploaded file (in the request) to a var ("f"). Then 
            content=file.read()
            return content #redirect(url_for('download_file', name=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

from flask import send_from_directory

@app.route('/uploads/<name>')
@csrf.exempt
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)    
                               

if __name__ == '__main__':
    app.run()
