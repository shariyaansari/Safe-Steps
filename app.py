

# from flask import Flask, jsonify, Blueprint, render_template, request, redirect, url_for
# from flask_login import LoginManager, current_user
# from models import db, Users
# from database import init_db
# from routes.auth import auth_bp, create_admin_if_not_exists
# from routes.home import home_bp
# from routes.admin import admin_bp
# from routes.parent import parent_bp
# import sqlite3

# app = Flask(__name__)
# init_db(app)

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "auth.login"

# @login_manager.user_loader
# def load_user(user_id):
#     return Users.query.get(int(user_id))

# # <<<<<<< HEAD
# # # Default route for the root URL

# # =======
# # @app.route('/get_reports')
# # def get_reports():
# #     reports = [
# #         {"lat": 19.075, "lng": 72.885},
# #         {"lat": 19.0755, "lng": 72.8852},
# #         {"lat": 19.085, "lng": 72.890},
# #         {"lat": 19.090, "lng": 72.885},
# #     ]
# #     return jsonify(reports)
# # >>>>>>> 470bb8e79e590cb9ea6c711203ca151d06c904b4

# # Register Blueprints
# app.register_blueprint(auth_bp, url_prefix="/auth")
# app.register_blueprint(home_bp, url_prefix="/home")
# app.register_blueprint(admin_bp, url_prefix="/admin")
# app.register_blueprint(parent_bp, url_prefix="/parent")

# # Create admin user if it doesn't exist
# with app.app_context():
#     create_admin_if_not_exists()

# # @app.route('/get_reports')
# # def get_reports():
# #     reports = [
# #         {"lat": 19.075, "lng": 72.885},
# #         {"lat": 19.0755, "lng": 72.8852},
# #         {"lat": 19.085, "lng": 72.890},
# #         {"lat": 19.090, "lng": 72.885},
# #     ]
# #     return jsonify(reports)

# # Initialize DB
# def init_db():
#     conn = sqlite3.connect('reports.db')
#     cursor = conn.cursor()
#     cursor.execute('''CREATE TABLE IF NOT EXISTS reports 
#                       (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, startTime TEXT, endTime TEXT, 
#                        description TEXT, lat REAL, lng REAL)''')
#     conn.commit()
#     conn.close()

# init_db()

# @app.route('/dashboard')
# def dashboard():
#     return render_template('parent_dashboard.html')

# @app.route('/submit_report', methods=['POST'])
# def submit_report():
#     data = request.json
#     conn = sqlite3.connect('reports.db')
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO reports (date, startTime, endTime, description, lat, lng) VALUES (?, ?, ?, ?, ?, ?)", 
#                    (data['date'], data['startTime'], data['endTime'], data['description'], data['lat'], data['lng']))
#     conn.commit()
#     conn.close()
#     return jsonify({'message': 'Report submitted successfully'})

# @app.route('/get_reports')
# def get_reports():
#     conn = sqlite3.connect('reports.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT date, startTime, endTime, description, lat, lng FROM reports")
#     reports = cursor.fetchall()
#     conn.close()
    
#     # Convert data into JSON-friendly format
#     report_list = [
#         {"date": row[0], "startTime": row[1], "endTime": row[2], 
#          "description": row[3], "lat": row[4], "lng": row[5]}
#         for row in reports
#     ]
    
#     return jsonify(report_list)

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, jsonify, Blueprint, render_template, request, redirect, url_for
from flask_login import LoginManager, current_user
from models import db, Users
from database import init_db
from routes.auth import auth_bp, create_admin_if_not_exists
from routes.home import home_bp
from routes.admin import admin_bp
from routes.parent import parent_bp
from routes.news_analysis import news_analysis_bp
import sqlite3


app = Flask(__name__)
init_db(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(home_bp, url_prefix="/home")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(parent_bp, url_prefix="/parent")
app.register_blueprint(news_analysis_bp)

# Create admin user if it doesn't exist
with app.app_context():
    create_admin_if_not_exists()

# Initialize DB
def init_db():
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reports 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, startTime TEXT, endTime TEXT, 
                       description TEXT, lat REAL, lng REAL)''')
    conn.commit()
    conn.close()


init_db()

@app.route('/dashboard')
def dashboard():
    return render_template('parent_dashboard.html')


@app.route('/submit_report', methods=['POST'])
def submit_report():
    data = request.json
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reports (date, startTime, endTime, description, lat, lng) VALUES (?, ?, ?, ?, ?, ?)", 
                   (data['date'], data['startTime'], data['endTime'], data['description'], data['lat'], data['lng']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Report submitted successfully'})


@app.route('/get_reports')
def get_reports():
    conn = sqlite3.connect('reports.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, startTime, endTime, description, lat, lng FROM reports ORDER BY date DESC, startTime DESC")

    reports = cursor.fetchall()
    conn.close()
    
    # Convert data into JSON-friendly format
    report_list = [
        {"date": row[0], "startTime": row[1], "endTime": row[2], 
         "description": row[3], "lat": row[4], "lng": row[5]}
        for row in reports
    ]
    
    return jsonify(report_list)

@app.route('/debug/routes')
def list_routes():
    output = []
    for rule in app.url_map.iter_rules():
        output.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'route': str(rule)
        })
    return {'routes': sorted(output, key=lambda x: x['endpoint'])}





if __name__ == '__main__':
    app.run(debug=True)