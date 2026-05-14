import os
from dotenv import load_dotenv

load_dotenv()


from flask import Flask, render_template, request, redirect, session
import qrcode
import os
import mysql.connector
import random

import hashlib
import time
import numpy as np
import joblib
import math
from tensorflow.keras.models import load_model


from config import DB_CONFIG
from config import EMAIL_CONFIG
from datetime import datetime, date
import pytz

from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_CONFIG["email"]
app.config['MAIL_PASSWORD'] = EMAIL_CONFIG["password"]

mail = Mail(app)
model = None
scaler = None
le_bank = None
le_category = None
le_device = None
le_network = None
feature_names = None
threshold = None

# ==========================
# HAVERSINE DISTANCE
# ==========================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# State center coordinates for is_new_location detection
STATE_COORDS = {
    'Andhra Pradesh': (15.9129, 79.7400), 'Arunachal Pradesh': (28.2180, 94.7278),
    'Assam': (26.2006, 92.9376), 'Bihar': (25.0961, 85.3131),
    'Chhattisgarh': (21.2787, 81.8661), 'Goa': (15.2993, 74.1240),
    'Gujarat': (22.2587, 71.1924), 'Haryana': (29.0588, 76.0856),
    'Himachal Pradesh': (31.1048, 77.1734), 'Jharkhand': (23.6102, 85.2799),
    'Karnataka': (15.3173, 75.7139), 'Kerala': (10.8505, 76.2711),
    'Madhya Pradesh': (22.9734, 78.6569), 'Maharashtra': (19.7515, 75.7139),
    'Manipur': (24.6637, 93.9063), 'Meghalaya': (25.4670, 91.3662),
    'Mizoram': (23.1645, 92.9376), 'Nagaland': (26.1584, 94.5624),
    'Odisha': (20.9517, 85.0985), 'Punjab': (31.1471, 75.3412),
    'Rajasthan': (27.0238, 74.2179), 'Sikkim': (27.5330, 88.5122),
    'Tamil Nadu': (11.1271, 78.6569), 'Telangana': (18.1124, 79.0193),
    'Tripura': (23.9408, 91.9882), 'Uttar Pradesh': (26.8467, 80.9462),
    'Uttarakhand': (30.0668, 79.0193), 'West Bengal': (22.9868, 87.8550),
    'Delhi': (28.7041, 77.1025), 'Jammu and Kashmir': (33.7782, 76.5762),
    'Ladakh': (34.1526, 77.5770)
}

# ==========================
# LOAD ML MODEL
# ==========================
#model = load_model('model/upi_fraud_cnn_latest.h5', compile=False)
#scaler = joblib.load('model/upi_fraud_scaler_latest.pkl')
#le_bank = joblib.load('model/le_bank_latest.pkl')
#le_category = joblib.load('model/le_category_latest.pkl')
#le_device = joblib.load('model/le_device_latest.pkl')
#le_network = joblib.load('model/le_network_latest.pkl')
#feature_names = np.load('model/feature_names_latest.npy', allow_pickle=True)
#threshold = np.load('model/best_threshold_latest.npy', allow_pickle=True)[0]
#threshold = 0.08  # Tuned threshold - catches real fraud, ignores small noise

# ==========================
# DATABASE CONNECTION
# ==========================
db = mysql.connector.connect(**DB_CONFIG)

def get_cursor():
    global db
    if not db.is_connected():
        db.reconnect()
    return db.cursor(dictionary=True, buffered=True)

# ==========================
# LOGIN PAGE
# ==========================
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        role = request.form.get('role')

        # ================= USER LOGIN =================
        if role == "user":

            mobile = request.form.get('mobile')

            otp = str(random.randint(100000, 999999))

            session['otp'] = otp
            session['mobile'] = mobile
            session['otp_time'] = time.time()

            cursor = get_cursor()

            cursor.execute(
                "SELECT email FROM users WHERE mobile=%s",
                (mobile,)
            )

            user = cursor.fetchone()

            if not user:
                return "User not found"

            receiver_email = user['email']

            try:

                msg = Message(
                    subject="SecurePay OTP Verification",
                    sender=EMAIL_CONFIG["email"],
                    recipients=[receiver_email]
                )

                msg.body = f"""
Your SecurePay OTP is: {otp}

This OTP is valid for 5 minutes.
"""

                mail.send(msg)

                print("OTP email sent successfully")

            except Exception as e:

                print("EMAIL ERROR:", e)
                print("OTP:", otp)

            return """
<h2>OTP Sent Successfully</h2>
<p>Please check your email for the OTP.</p>
<a href='/verify-otp'>Verify OTP</a>
"""      

          

              
        # ================= ADMIN LOGIN =================
        elif role == "admin":

            username = request.form.get('username')
            password = request.form.get('password')

            hashed_password = hashlib.md5(
                password.encode()
            ).hexdigest()

            cursor = get_cursor()
            cursor.execute(
                """
                SELECT * FROM admin
                WHERE username=%s AND password=%s
                """,
                (username, hashed_password)
            )

            admin = cursor.fetchone()

            if admin:
                session['admin'] = username
                return redirect('/admin')

            else:
                return "Invalid Admin Credentials"

    return render_template("login.html")


# ==========================
# VERIFY OTP
# ==========================
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():

    if request.method == 'GET':
        return render_template("otp_verify.html")

    user_otp = request.form['otp'].strip()

    otp_time = session.get('otp_time')
    print(f"[DEBUG] user_otp='{user_otp}' session_otp='{session.get('otp')}' mobile='{session.get('mobile')}'"
)

    if otp_time:
        if time.time() - otp_time > 300:
            session.clear()
            return "OTP expired. Please login again."

    if user_otp == session.get('otp'):

        cursor = get_cursor()
        cursor.execute(
            "SELECT * FROM users WHERE mobile=%s",
            (session.get('mobile'),)
        )
        user = cursor.fetchone()

        if user:
            failed = session.get('failed_otp', 0)
            device_fp = request.form.get('device_fingerprint', '')
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_mobile'] = user['mobile']
            session['failed_login_attempts'] = failed

            # Store device fingerprint in DB if not set, else keep for comparison
            cursor2 = get_cursor()
            cursor2.execute("SELECT device_fingerprint FROM users WHERE id=%s", (user['id'],))
            stored = cursor2.fetchone()
            if not stored['device_fingerprint']:
                cursor2.execute("UPDATE users SET device_fingerprint=%s WHERE id=%s", (device_fp, user['id']))
                db.commit()
            session['known_device_fp'] = stored['device_fingerprint'] or device_fp
            session['current_device_fp'] = device_fp

            return redirect('/dashboard')
        else:
            return "User not found"

    else:
        session['failed_otp'] = session.get('failed_otp', 0) + 1
        return render_template('otp_verify.html', error='Invalid OTP. Try again.')


# ==========================
# CONFIRM PAYMENT
# ==========================
@app.route('/confirm-payment', methods=['GET', 'POST'])
def confirm_payment():
    if not session.get('user_id'):
        return redirect('/')

    if request.method == 'POST':
        action = request.form.get('action')
        txn = session.get('pending_txn')

        if not txn:
            return redirect('/payment')

        if action == 'cancel':
            session.pop('pending_txn', None)
            return render_template('success.html', result='Fraud', fraud_score=0.99)

        # Verify DOB
        entered_dob = request.form.get('dob', '').strip()
        cursor = get_cursor()
        cursor.execute("SELECT dob FROM users WHERE mobile=%s", (session.get('user_mobile'),))
        user = cursor.fetchone()
        real_dob = str(user['dob']) if user else ''

        if entered_dob != real_dob:
            session.pop('pending_txn', None)
            return render_template('success.html', result='Fraud', fraud_score=0.95)

        # DOB correct — process payment
        cursor.execute("""
            INSERT INTO transactions
            (user_mobile, merchant_upi, amount, status, date_time, category, age, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session.get('user_mobile'),
            txn['merchant_upi'],
            txn['amount'],
            'SUCCESS',
            datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S'),
            txn['category'],
            txn['age'],
            txn.get('curr_lat'),
            txn.get('curr_lon')
        ))
        db.commit()
        session.pop('pending_txn', None)
        return render_template('success.html', result='Success', fraud_score=0.25)

    return redirect('/payment')


# ==========================
# SET PIN
# ==========================
@app.route('/set-pin', methods=['POST'])
def set_pin():
    if not session.get('user_id'):
        return redirect('/')
    pin = request.form['pin']
    cursor = get_cursor()
    cursor.execute("UPDATE users SET pin=%s WHERE id=%s", (pin, session.get('user_id')))
    db.commit()
    return redirect('/profile')


# ==========================
# LOGOUT
# ==========================
@app.route('/logout')
def logout():

    session.clear()
    return redirect('/')


# ==========================
# DASHBOARD
# ==========================
@app.route('/dashboard')
def dashboard():

    if not session.get('user_id'):
        return redirect('/')

    return render_template(
        "dashboard.html",
        name=session.get('user_name')
    )


# ==========================
# MERCHANT SETUP
# ==========================
@app.route('/merchant/setup', methods=['GET', 'POST'])
def merchant_setup():

    if not session.get('user_id'):
        return redirect('/')

    if request.method == 'POST':

        upi = request.form['upi']
        category = request.form['category']

        if "@" not in upi:
            return "Invalid UPI ID"

        cursor = get_cursor()
        cursor.execute(
            "SELECT * FROM merchants WHERE user_id=%s",
            (session.get('user_id'),)
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute("""
                UPDATE merchants
                SET upi=%s, category=%s
                WHERE user_id=%s
            """, (
                upi,
                category,
                session.get('user_id')
            ))

        else:

            cursor.execute("""
                INSERT INTO merchants
                (user_id, upi, category, created_at)
                VALUES (%s, %s, %s, %s)
            """, (
                session.get('user_id'),
                upi,
                category,
                datetime.utcnow()
            ))

        db.commit()

        return redirect('/merchant/dashboard')

    cursor = get_cursor()
    cursor.execute(
        "SELECT * FROM merchants WHERE user_id=%s",
        (session.get('user_id'),)
    )

    merchant = cursor.fetchone()

    return render_template(
        "merchant_setup.html",
        merchant=merchant
    )


# ==========================
# MERCHANT DASHBOARD
# ==========================
@app.route('/merchant/dashboard')
def merchant_dashboard():

    if not session.get('user_id'):
        return redirect('/')

    cursor = get_cursor()
    cursor.execute(
        "SELECT * FROM merchants WHERE user_id=%s",
        (session.get('user_id'),)
    )

    merchant = cursor.fetchone()

    return render_template(
        "merchant-dashboard.html",
        merchant=merchant
    )


# ==========================
# MERCHANT TRANSACTIONS
# ==========================
@app.route('/merchant/transactions')
def merchant_transactions():

    if not session.get('user_id'):
        return redirect('/')

    cursor = get_cursor()
    cursor.execute("""
        SELECT DISTINCT t.*
        FROM transactions t
        JOIN merchants m
        ON t.merchant_upi = m.upi
        WHERE m.user_id = %s
    """, (session.get('user_id'),))

    data = cursor.fetchall()

    return render_template(
        "merchant_transactions.html",
        data=data
    )


# ==========================
# MERCHANT PROFILE
# ==========================
@app.route('/merchant/profile')
def merchant_profile():

    if not session.get('user_id'):
        return redirect('/')

    cursor = get_cursor()
    cursor.execute("""
        SELECT m.*, u.name, u.mobile, u.email
        FROM merchants m
        JOIN users u
        ON m.user_id = u.id
        WHERE m.user_id=%s
    """, (session.get('user_id'),))

    merchant = cursor.fetchone()

    if not merchant:
        return "No merchant found"

    upi = merchant['upi']

    qr = qrcode.make(upi)

    folder = "static/qr"

    if not os.path.exists(folder):
        os.makedirs(folder)

    safe_upi = upi.replace("@", "_")

    path = os.path.join(
        folder,
        f"{safe_upi}.png"
    )

    qr.save(path)

    return render_template(
        "merchant_profile.html",
        merchant=merchant
    )


# ==========================
# PAYMENT PAGE
# ==========================
@app.route('/payment', methods=['GET', 'POST'])
def payment():

    global model, scaler, le_bank, le_category
    global le_device, le_network, feature_names, threshold

    if request.method == 'POST':

        if model is None:

            model = load_model(
                'model/upi_fraud_cnn_latest.h5',
                compile=False
            )

            scaler = joblib.load(
                'model/upi_fraud_scaler_latest.pkl'
            )

            le_bank = joblib.load(
                'model/le_bank_latest.pkl'
            )

            le_category = joblib.load(
                'model/le_category_latest.pkl'
            )

            le_device = joblib.load(
                'model/le_device_latest.pkl'
            )

            le_network = joblib.load(
                'model/le_network_latest.pkl'
            )

            feature_names = np.load(
                'model/feature_names_latest.npy',
                allow_pickle=True
            )

            threshold = 0.08

        merchant_upi = request.form['upi']
        amount = float(request.form['amount'])


        cursor = get_cursor()
        cursor.execute(
            "SELECT category FROM merchants WHERE upi=%s",
            (merchant_upi,)
        )

        merchant = cursor.fetchone()

        if merchant:
            category = merchant['category']
        else:
            category = "Other"

        cursor.execute(
            "SELECT dob FROM users WHERE mobile=%s",
            (session.get('user_mobile'),)
        )

        user = cursor.fetchone()

        if not user:
            return "User not found"

        dob_str = str(user['dob'])

        dob = datetime.strptime(
            dob_str,
            "%Y-%m-%d"
        ).date()

        today = date.today()

        age = today.year - dob.year - (
            (today.month, today.day)
            < (dob.month, dob.day)
        )

        # ==========================
        # FRAUD DETECTION WITH ML MODEL
        # ==========================
        
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE user_mobile=%s 
            ORDER BY date_time DESC LIMIT 1
        """, (session.get('user_mobile'),))
        prev_txn = cursor.fetchone()
        
        now = datetime.now()
        
        # Calculate features
        trans_hour = now.hour
        trans_day_of_week = now.weekday()
        trans_month = now.month
        
        # Previous transaction features
        if prev_txn:
            prev_time = prev_txn['date_time']
            time_diff = (now - prev_time).total_seconds() / 3600
            time_since_prev_txn_hrs = time_diff
            distance_from_prev_txn_km = 0  # Same location assumed
        else:
            time_since_prev_txn_hrs = 999
            distance_from_prev_txn_km = 0
        
        # Transaction frequency
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM transactions 
            WHERE user_mobile=%s AND date_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """, (session.get('user_mobile'),))
        txns_last_1hr = cursor.fetchone()['cnt']
        
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM transactions 
            WHERE user_mobile=%s AND date_time >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        """, (session.get('user_mobile'),))
        txns_last_10min = cursor.fetchone()['cnt']
        
        # Average amount
        cursor.execute("""
            SELECT AVG(amount) as avg_amt FROM transactions 
            WHERE user_mobile=%s
        """, (session.get('user_mobile'),))
        avg_result = cursor.fetchone()
        avg_amount = avg_result['avg_amt'] if avg_result['avg_amt'] else amount
        ratio_to_avg_amount = amount / avg_amount if avg_amount > 0 else 1.0
        
        # Account age
        cursor.execute("""
            SELECT DATEDIFF(NOW(), MIN(date_time)) as acc_age FROM transactions 
            WHERE user_mobile=%s
        """, (session.get('user_mobile'),))
        acc_age_result = cursor.fetchone()
        account_age_days = acc_age_result['acc_age'] if acc_age_result['acc_age'] else 0

        # Spending trend (this month vs last month)
        cursor.execute("""
            SELECT
                SUM(CASE WHEN MONTH(date_time)=MONTH(NOW()) AND YEAR(date_time)=YEAR(NOW()) THEN amount ELSE 0 END) as this_month,
                SUM(CASE WHEN MONTH(date_time)=MONTH(NOW()-INTERVAL 1 MONTH) AND YEAR(date_time)=YEAR(NOW()-INTERVAL 1 MONTH) THEN amount ELSE 0 END) as last_month
            FROM transactions WHERE user_mobile=%s
        """, (session.get('user_mobile'),))
        trend_result = cursor.fetchone()
        this_month = trend_result['this_month'] or 0
        last_month = trend_result['last_month'] or 0
        # Only flag if this month spending is 10x+ more than last month AND amount > 5000
        if last_month > 0 and amount > 5000:
            spending_trend = min((this_month - last_month) / last_month, 10.0)
        else:
            spending_trend = 0.0

        # Failed login attempts from session
        failed_login_attempts = session.get('failed_login_attempts', 0)

        # Get user-submitted context fields
        device_type = request.form.get('device_type', 'Android')
        network_type = request.form.get('network_type', '4G')
        bank = request.form.get('bank', 'SBI')
        entered_pin = request.form.get('pin', '')
        current_fp = request.form.get('device_fingerprint', '')

        # PIN verification — count retries from session
        cursor.execute("SELECT pin FROM users WHERE mobile=%s", (session.get('user_mobile'),))
        pin_row = cursor.fetchone()
        pin_retries = session.get('pin_retries', 0)
        if pin_row and pin_row['pin']:
            if entered_pin != pin_row['pin']:
                pin_retries += 1
                session['pin_retries'] = pin_retries
            else:
                session['pin_retries'] = 0
                pin_retries = 0
        else:
            pin_retries = 0

        # is_new_device — compare current fingerprint with stored
        known_fp = session.get('known_device_fp', '')
        is_new_device = 1 if (known_fp and current_fp and current_fp != known_fp) else 0

        # Geolocation features
        try:
            curr_lat = float(request.form.get('latitude', 0) or 0)
            curr_lon = float(request.form.get('longitude', 0) or 0)
        except:
            curr_lat, curr_lon = 0, 0

        # distance_from_prev_txn_km
        distance_from_prev_txn_km = 0
        if prev_txn and curr_lat and curr_lon:
            prev_lat = prev_txn.get('latitude') or 0
            prev_lon = prev_txn.get('longitude') or 0
            if prev_lat and prev_lon:
                distance_from_prev_txn_km = haversine(curr_lat, curr_lon, prev_lat, prev_lon)

        # is_new_location — compare with user's registered state
        is_new_location = 0
        if curr_lat and curr_lon:
            cursor.execute("SELECT state FROM users WHERE mobile=%s", (session.get('user_mobile'),))
            state_row = cursor.fetchone()
            if state_row and state_row['state']:
                state_coords = STATE_COORDS.get(state_row['state'])
                if state_coords:
                    dist_from_home = haversine(curr_lat, curr_lon, state_coords[0], state_coords[1])
                    is_new_location = 1 if dist_from_home > 300 else 0

        # Prepare features
        features = {
            'trans_hour': trans_hour,
            'trans_day_of_week': trans_day_of_week,
            'trans_month': trans_month,
            'amount': amount,
            'category': category,
            'distance_from_prev_txn_km': distance_from_prev_txn_km,
            'time_since_prev_txn_hrs': time_since_prev_txn_hrs,
            'device_type': device_type,
            'network_type': network_type,
            'is_new_device': is_new_device,
            'is_new_location': is_new_location,
            'txns_last_1hr': txns_last_1hr,
            'txns_last_10min': txns_last_10min,
            'ratio_to_avg_amount': ratio_to_avg_amount,
            'failed_login_attempts': failed_login_attempts,
            'otp_verification_attempts': 1,
            'pin_retries': pin_retries,
            'account_age_days': account_age_days,
            'user_age': age,
            'bank': bank,
            'is_odd_hour': 1 if trans_hour < 6 or trans_hour > 22 else 0,
            'is_foreign_location': 0,
            'spending_trend': spending_trend
        }
        
        # Encode categorical features
        try:
            features['category'] = le_category.transform([features['category']])[0]
        except:
            features['category'] = 0
        
        try:
            features['device_type'] = le_device.transform([features['device_type']])[0]
        except:
            features['device_type'] = 0
        
        try:
            features['network_type'] = le_network.transform([features['network_type']])[0]
        except:
            features['network_type'] = 0
        
        try:
            features['bank'] = le_bank.transform([features['bank']])[0]
        except:
            features['bank'] = 0
        
        # Create feature array in correct order
        feature_array = np.array([[features[f] for f in feature_names]])
        
        # Scale features
        feature_scaled = scaler.transform(feature_array)
        
        # Predict
        prediction = model.predict(feature_scaled, verbose=0)[0][0]

        print(f"[ML] amount={amount} ratio={ratio_to_avg_amount:.2f} txns_1hr={txns_last_1hr} txns_10min={txns_last_10min} odd_hour={1 if trans_hour < 6 or trans_hour > 22 else 0} pin_retries={pin_retries} failed_login={failed_login_attempts} spending_trend={spending_trend:.0f} is_new_device={is_new_device} is_new_location={is_new_location} score={prediction:.4f} threshold={threshold:.2f} -> {'FRAUD' if prediction >= threshold else 'LEGIT'}")

        # IMMEDIATE BLOCK: Rs1,00,000+ with high ratio -> no confirmation
        if amount >= 100000 and ratio_to_avg_amount > 20:
            result = "Fraud"
            status = "BLOCKED"

        # CONFIRMATION POPUP: Rs50,000-99,999 with high ratio
        elif amount >= 50000 and ratio_to_avg_amount > 20:
            session['pending_txn'] = {
                'merchant_upi': merchant_upi,
                'amount': amount,
                'category': category,
                'age': age,
                'curr_lat': curr_lat,
                'curr_lon': curr_lon
            }
            return render_template('confirm_payment.html', amount=amount, merchant_upi=merchant_upi)

        # ML MODEL: decides everything else
        elif prediction >= threshold:
            result = "Fraud"
            status = "BLOCKED"
        else:
            result = "Success"
            status = "SUCCESS"

        # ==========================
        # SAVE TRANSACTION
        # ==========================
        cursor.execute("""
            INSERT INTO transactions
            (
                user_mobile,
                merchant_upi,
                amount,
                status,
                date_time,
                category,
                age,
                latitude,
                longitude
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session.get('user_mobile'),
            merchant_upi,
            amount,
            status,
            datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S'),
            category,
            age,
            curr_lat or None,
            curr_lon or None
        ))

        db.commit()

        return render_template(
            "success.html",
            result=result,
            fraud_score=float(prediction)
        )

    return render_template("payment.html")


# ==========================
# TRANSACTIONS
# ==========================
@app.route('/transactions')
def transactions():

    cursor = get_cursor()
    cursor.execute("""

        SELECT
            t.*,
            m.category,
            u.state,
            u.zipcode

        FROM transactions t

        LEFT JOIN merchants m
        ON t.merchant_upi = m.upi

        LEFT JOIN users u
        ON m.user_id = u.id

        WHERE t.user_mobile = %s

        ORDER BY t.date_time DESC

    """, (session['user_mobile'],))

    data = cursor.fetchall()

    return render_template(
        "transaction_history.html",
        data=data
    )


# ==========================
# USER PROFILE
# ==========================
@app.route('/profile')
def profile():

    if not session.get('user_id'):
        return redirect('/')

    profile_cursor = get_cursor()
    profile_cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session.get('user_id'),)
    )

    user = profile_cursor.fetchone()

    return render_template(
        "profile.html",
        user=user
    )


# ==========================
# ADMIN PANEL
# ==========================
@app.route('/admin')
def admin():

    return render_template(
        "admin_dashboard.html"
    )


# ==========================
# CREATE ACCOUNT
# ==========================
@app.route('/admin/create', methods=['GET', 'POST'])
def create_account():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        dob = request.form['dob']
        address = request.form['address']
        state = request.form['state']
        zipcode = request.form['zip']

        cursor = get_cursor()
        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                mobile,
                dob,
                address,
                zipcode,
                state
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            email,
            mobile,
            dob,
            address,
            zipcode,
            state
        ))

        db.commit()

        return redirect('/admin/users')

    return render_template(
        "create_account.html"
    )


# ==========================
# ADMIN USERS
# ==========================
@app.route('/admin/users')
def admin_users():

    admin_cursor = get_cursor()
    admin_cursor.execute(
        "SELECT * FROM users"
    )

    users = admin_cursor.fetchall()

    return render_template(
        "admin_users.html",
        users=users
    )


# ==========================
# ADMIN MERCHANTS
# ==========================
@app.route('/admin/merchants')
def admin_merchants():

    cursor = get_cursor()
    cursor.execute("""
        SELECT
            merchants.*,
            users.name,
            users.mobile,
            users.email
        FROM merchants
        JOIN users
        ON merchants.user_id = users.id
    """)

    merchants = cursor.fetchall()

    return render_template(
        "admin_merchants.html",
        merchants=merchants
    )


# ==========================
# ADMIN TRANSACTIONS
# ==========================
@app.route('/admin/transactions')
def admin_transactions():

    cursor = get_cursor()
    cursor.execute("""

        SELECT
            t.*,
            m.category,
            u.state,
            u.zipcode

        FROM transactions t

        LEFT JOIN merchants m
        ON t.merchant_upi = m.upi

        LEFT JOIN users u
        ON m.user_id = u.id

        ORDER BY t.date_time DESC

    """)

    data = cursor.fetchall()

    return render_template(
        "admin_transactions.html",
        data=data
    )


# ==========================
# DELETE USER
# ==========================
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):

    cursor = get_cursor()
    cursor.execute(
        "DELETE FROM users WHERE id=%s",
        (user_id,)
    )

    db.commit()

    return redirect('/admin/users')
# ==========================
# EDIT USER
# ==========================

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        dob = request.form['dob']
        address = request.form['address']
        zipcode = request.form['zipcode']
        state = request.form['state']

        cursor = get_cursor()
        cursor.execute("""
            UPDATE users
            SET
                name=%s,
                email=%s,
                mobile=%s,
                dob=%s,
                address=%s,
                zipcode=%s,
                state=%s
            WHERE id=%s
        """, (
            name,
            email,
            mobile,
            dob,
            address,
            zipcode,
            state,
            user_id
        ))

        db.commit()

        return redirect('/admin/users')

    cursor = get_cursor()
    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (user_id,)
    )

    user = cursor.fetchone()

    return render_template(
        "edit_user.html",
        user=user
    )


# ==========================
# RUN SERVER
# ==========================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)