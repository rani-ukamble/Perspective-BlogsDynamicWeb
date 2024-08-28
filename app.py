from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from dotenv import load_dotenv
import os
import bcrypt

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Database configuration using environment variables
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    if 'username' in session:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT blogs.blog_id, blogs.blog_name, LEFT(blogs.blog_content, 100) AS blog_content, users.username 
            FROM blogs
            JOIN users ON blogs.user_id = users.id
        ''')
        blogs = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', blogs=blogs, username=session['username'])
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'username' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM blogs WHERE user_id = %s', (user_id,))
        blogs = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('profile.html', blogs=blogs, user={'username': session['username']})
    return redirect(url_for('login'))

@app.route('/read_blog/<int:blog_id>')
def read_blog(blog_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM blogs WHERE blog_id = %s', (blog_id,))
    blog = cursor.fetchone()
    cursor.close()
    conn.close()
    if blog:
        return render_template('read_blog.html', blog=blog)
    else:
        flash('Blog not found.')
        return redirect(url_for('index'))

@app.route('/add_blog', methods=['GET', 'POST'])
def add_blog():
    if 'username' not in session:
        flash('You need to log in to add a blog.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        blog_name = request.form['blog_name']
        blog_content = request.form['blog_content']
        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO blogs (user_id, blog_name, blog_content) VALUES (%s, %s, %s)', (user_id, blog_name, blog_content))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Blog added successfully!')
        return redirect(url_for('index'))

    return render_template('add_blog.html')

@app.route('/edit_blog/<int:blog_id>', methods=['GET', 'POST'])
def edit_blog(blog_id):
    if 'username' not in session:
        flash('You need to log in to edit a blog.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM blogs WHERE blog_id = %s', (blog_id,))
    blog = cursor.fetchone()

    if request.method == 'POST':
        new_blog_name = request.form['blog_name']
        new_blog_content = request.form['blog_content']
        cursor.execute('UPDATE blogs SET blog_name = %s, blog_content = %s WHERE blog_id = %s', (new_blog_name, new_blog_content, blog_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Blog updated successfully!')
        return redirect(url_for('index'))

    cursor.close()
    conn.close()
    return render_template('edit_blog.html', blog=blog)

@app.route('/delete_blog/<int:blog_id>', methods=['POST'])
def delete_blog(blog_id):
    if 'username' not in session:
        flash('You need to log in to delete a blog.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM blogs WHERE blog_id = %s', (blog_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Blog deleted successfully!')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            session['user_id'] = user['id']
            session['role'] = user['role']
            flash('Login successful!')
            cursor.close()
            conn.close()
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials! Please try again.')
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('role', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user:
            flash('Username already exists! Try a different one.')
            cursor.close()
            conn.close()
            return redirect(url_for('register'))

        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, hashed_password, 'user'))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
