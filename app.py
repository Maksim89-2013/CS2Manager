from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'halva-cs2-secret-key-2024'

USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Сначала войдите в систему', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        users = load_users()
        
        if not username or not email or not password:
            flash('Заполните все поля', 'error')
            return redirect(url_for('register'))
        
        if len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 4:
            flash('Пароль должен содержать минимум 4 символа', 'error')
            return redirect(url_for('register'))
        
        if username in users:
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
        
        users[username] = {
            'email': email,
            'password': password,
            'stats': {
                'matches': [],
                'total_kills': 0,
                'total_deaths': 0,
                'total_assists': 0,
                'wins': 0,
                'losses': 0,
                'total_matches': 0
            }
        }
        save_users(users)
        
        flash('Регистрация прошла успешно! Теперь войдите в аккаунт', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        users = load_users()
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            flash(f'Добро пожаловать обратно, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    users = load_users()
    user_data = users.get(session['username'], {})
    stats = user_data.get('stats', {})
    
    matches = stats.get('matches', [])
    total_matches = len(matches)
    wins = stats.get('wins', 0)
    losses = stats.get('losses', 0)
    total_kills = stats.get('total_kills', 0)
    total_deaths = stats.get('total_deaths', 0)
    total_assists = stats.get('total_assists', 0)
    
    kd_ratio = round(total_kills / total_deaths, 2) if total_deaths > 0 else total_kills
    win_rate = round((wins / total_matches) * 100, 1) if total_matches > 0 else 0
    
    recent_matches = matches[-5:][::-1] if matches else []
    
    return render_template('dashboard.html', 
                         username=session['username'],
                         email=user_data.get('email', ''),
                         stats=stats,
                         total_matches=total_matches,
                         wins=wins,
                         losses=losses,
                         total_kills=total_kills,
                         total_deaths=total_deaths,
                         total_assists=total_assists,
                         kd_ratio=kd_ratio,
                         win_rate=win_rate,
                         recent_matches=recent_matches)

@app.route('/add_match', methods=['POST'])
@login_required
def add_match():
    try:
        result = request.form.get('result')
        kills = int(request.form.get('kills', 0))
        deaths = int(request.form.get('deaths', 0))
        assists = int(request.form.get('assists', 0))
        map_name = request.form.get('map', 'Unknown')
        
        if kills < 0 or deaths < 0 or assists < 0:
            flash('Значения не могут быть отрицательными', 'error')
            return redirect(url_for('dashboard'))
        
        users = load_users()
        user_stats = users[session['username']]['stats']
        
        kd = round(kills / deaths, 2) if deaths > 0 else kills
        
        match = {
            'result': result,
            'kills': kills,
            'deaths': deaths,
            'assists': assists,
            'map': map_name,
            'kd': kd,
            'date': __import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        
        user_stats['matches'].append(match)
        user_stats['total_kills'] += kills
        user_stats['total_deaths'] += deaths
        user_stats['total_assists'] += assists
        
        if result == 'win':
            user_stats['wins'] += 1
        else:
            user_stats['losses'] += 1
        
        user_stats['total_matches'] = len(user_stats['matches'])
        
        save_users(users)
        
        flash('Матч успешно добавлен в статистику!', 'success')
    except ValueError:
        flash('Введите корректные числовые значения', 'error')
    except Exception as e:
        flash('Произошла ошибка при добавлении матча', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)