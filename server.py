from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import config
from main import run_analysis
from extensions import db
from models import User, ScanHistory

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'quantum-core-secret-key-change-in-prod-abc-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quantum_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure DB Created
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('landing'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('landing'))
        else:
            flash('Invalid credentials')
            
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('login'))
        
    hashed_pw = generate_password_hash(password, method='scrypt')
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    login_user(new_user)
    return redirect(url_for('landing'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main App Routes ---
@app.route('/')
def landing():
    """Public Landing Page"""
    """Public Landing Page"""
    return render_template('landing.html', user=current_user if current_user.is_authenticated else None)

@app.route('/dashboard')
@login_required
def dashboard():
    """Main Scanner Interface"""
    return render_template('index.html', user=current_user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Configuration Page"""
    if request.method == 'POST':
        try:
            # Update Global Config (Scan defaults)
            config.START_AMOUNT = float(request.form.get('start_amount', 100))
            config.MIN_PROFIT_PERCENT = float(request.form.get('min_profit', 0.2))
            config.MAX_DEPTH = int(request.form.get('max_depth', 3))
            
            # Save User-Specific Trading Keys to DB
            current_user.bybit_api_key = request.form.get('bybit_key', '')
            current_user.bybit_api_secret = request.form.get('bybit_secret', '')
            
            # Persist
            db.session.commit()
            
            # Update Global Config for consistency in this session
            config.BYBIT_API_KEY = current_user.bybit_api_key
            config.BYBIT_API_SECRET = current_user.bybit_api_secret
            
            flash('Configuration updated successfully!')
        except ValueError:
            flash('Invalid input parameters.')
            
    # Load from User DB
    current_conf = {
        'start_amount': config.START_AMOUNT,
        'min_profit': config.MIN_PROFIT_PERCENT,
        'max_depth': config.MAX_DEPTH,
        'bybit_key': current_user.bybit_api_key or '',
        'bybit_secret': current_user.bybit_api_secret or '',
        'trade_mode': config.TRADE_MODE
    }
    return render_template('settings.html', user=current_user, config=current_conf)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/api/update_balance', methods=['POST'])
@login_required
def update_balance():
    data = request.json
    try:
        current_user.paper_balance_usdt = float(data.get('usdt', 0))
        current_user.paper_balance_usdc = float(data.get('usdc', 0))
        db.session.commit()
        
        # Update Auto Trader Instance State
        from auto_trader import auto_trader
        auto_trader.update_wallet_from_user(current_user)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/auto/start', methods=['POST'])
@login_required
def auto_start():
    data = request.json or {}
    mode = data.get('mode', 'PAPER')
    
    from auto_trader import auto_trader
    
    # Push User Config to Auto Trader
    config.TRADE_MODE = mode
    config.BYBIT_API_KEY = current_user.bybit_api_key
    config.BYBIT_API_SECRET = current_user.bybit_api_secret
    
    # Sync Balance
    auto_trader.update_wallet_from_user(current_user)
    
    auto_trader.start()
    return jsonify({"status": "started", "mode": mode})
def about():
    return render_template('about.html', user=current_user if current_user.is_authenticated else None)

@app.route('/reviews')
def reviews():
    return render_template('reviews.html', user=current_user if current_user.is_authenticated else None)

@app.route('/api/config')
def get_config():
    return jsonify({
        "supported_exchanges": config.ENABLED_EXCHANGES,
        "min_profit_percent": config.MIN_PROFIT_PERCENT
    })

@app.route('/pricing')
def pricing():
    return render_template('pricing.html', user=current_user)

@app.route('/payment/<plan>')
@login_required
def payment(plan):
    return render_template('payment.html', user=current_user, plan=plan)



@app.route('/api/upgrade', methods=['POST'])
@login_required
def upgrade_plan():
    data = request.json or {}
    new_plan = data.get('plan', 'Pro')
    current_user.plan = new_plan
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/scan', methods=['POST'])
@login_required
def scan():
    try:
        data = request.json or {}
        selected_exchanges = data.get('exchanges', [])
        
        if not selected_exchanges:
             selected_exchanges = config.ENABLED_EXCHANGES
             
        logger.info(f"Received scan request for: {selected_exchanges} from user {current_user.username}")
        
        results = run_analysis(target_exchanges=selected_exchanges)
        
        # Save History (SQLite)
        try:
            history = ScanHistory(
                user_id=current_user.id,
                exchanges=",".join(selected_exchanges),
                profitable_count=len(results['profitable'])
            )
            db.session.add(history)
            db.session.commit()
        except Exception as db_e:
            logger.error(f"Failed to save history: {db_e}")

        # Save History (Firebase)
        try:
            from firebase_service import firebase_manager
            firebase_manager.save_scan_log(
                user_id=current_user.id,
                user_data={'username': current_user.username},
                scan_data={
                    'exchanges': selected_exchanges,
                    'profitable_count': len(results['profitable']),
                    'total_analyzed': len(results['all_paths'])
                }
            )
        except Exception as fb_e:
            logger.error(f"Firebase logging failed: {fb_e}")

        response = {
            "status": "success",
            "count": len(results['profitable']),
            "opportunities": results['profitable'],
            "all_opportunities": results['all_paths'],
            "total_analyzed": len(results['all_paths']) # Explicit count
        }
        return jsonify(response)

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/auto_trade')
@login_required
def auto_trade_page():
    return render_template('auto_trade.html', user=current_user)



@app.route('/api/auto/stop', methods=['POST'])
@login_required
def auto_stop():
    from auto_trader import auto_trader
    auto_trader.stop()
    return jsonify({"status": "stopped"})

@app.route('/api/auto/status')
@login_required
def auto_status_endpoint():
    from auto_trader import auto_trader
    return jsonify(auto_trader.get_status())

if __name__ == '__main__':
    print("Starting Web Server on http://localhost:5000")
    app.run(debug=True, port=5000)
