from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import string

db = SQLAlchemy()
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key

db_name = 'champions.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Define the correct password
SECRET_PASSWORD = "please"

class Champion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    formatted_name = db.Column(db.String(100), nullable=False, unique=True)
    checked_off = db.Column(db.Boolean, default=False)
    top_3 = db.Column(db.Boolean, default=False)

def format_name(name):
    """Removes spaces and punctuation, converts to lowercase."""
    return ''.join(char for char in name if char.isalnum()).lower()

def populate_database():
    """Reads champions from a file and adds them to the database if they don't exist."""
    file_path = "champions.txt"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
    
    with app.app_context():
        db.create_all()
        
        with open(file_path, 'r') as file:
            champions = file.read().splitlines()

        for champ in champions:
            formatted_name = format_name(champ)
            if champ == "Nunu & Willump":
                formatted_name = "Nunu"
            if champ == "Renata Glasc":
                formatted_name = "Renata"
                
            exists = Champion.query.filter_by(name=champ).first()

            if not exists:
                new_champ = Champion(name=champ, formatted_name=formatted_name)
                db.session.add(new_champ)
        
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Redirect to password page if user hasn't entered the correct password
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('password'))

    if request.method == 'POST':
        selected_champions = request.form.getlist('selected_champions')
        
        if request.form['action'] == 'first_place':
            # Update database: set checked_off=True for selected champions, False for others
            for champ in Champion.query.all():
                if not champ.checked_off:
                    if champ.formatted_name in selected_champions:
                      champ.checked_off = True
                      champ.top_3 = True

        if request.form['action'] == 'top_3':
            # Update database: set checked_off=True for selected champions, False for others
            for champ in Champion.query.all():
                if not champ.checked_off and not champ.top_3:
                  champ.top_3 = champ.formatted_name in selected_champions

        if request.form['action'] == 'remove':
           for champ in Champion.query.all():
                if champ.checked_off:
                    champ.checked_off = champ.formatted_name in selected_champions
                    champ.top_3 = champ.formatted_name in selected_champions

        db.session.commit()

        return redirect(url_for('index'))
    
    champions = Champion.query.all()
    selected_count = Champion.query.filter_by(checked_off=True).count()  # Count checked champions
    top3_count = Champion.query.filter_by(top_3=True).count()

    return render_template('index.html', champions=champions, selected_count=selected_count, top3_count=top3_count)

@app.route('/password', methods=['GET', 'POST'])
def password():
    error = None
    if request.method == 'POST':
        entered_password = request.form.get('password')

        if entered_password == SECRET_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            error = "Incorrect password. Try again."

    return render_template('password.html', error=error)

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('password'))

if __name__ == '__main__':
    with app.app_context():
        populate_database()
    app.run(debug=True)
