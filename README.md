# SecurePay — AI-Powered UPI Fraud Detection System

> 🌐 **Live Demo:** https://securepay-ml-1.onrender.com/

SecurePay is a full-stack UPI payment simulation platform with a built-in CNN-based fraud detection model. Every transaction is analyzed in real-time using behavioral, geolocation, and device signals to block fraudulent payments before they go through.

---

## Features

- **OTP-based login** — 6-digit OTP sent to registered email, expires in 5 minutes
- **Real-time fraud detection** — CNN model scores every transaction before it's processed
- **Multi-signal analysis** — device fingerprint, geolocation, spending patterns, PIN retries, login failures
- **Tiered fraud response** — auto-block for high-risk, DOB confirmation for medium-risk, approve low-risk transactions
- **Merchant portal** — UPI setup, QR code generation, transaction history
- **Admin panel** — manage users, merchants, and all transactions
- **QR code payments** — scan-to-pay flow for merchants

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| ML Model | TensorFlow/Keras (CNN), Scikit-learn |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript (Jinja2 templates) |
| Auth | Brevo Email API, OTP verification, device fingerprinting |
| Config | python-dotenv |

---

## Project Structure

```
SecurePay/
├── app.py                  # Main Flask app & all routes
├── config.py               # DB and email config (reads from .env)
├── database/
│   └── schema.sql          # MySQL schema + sample data
├── model/
│   ├── upi_fraud_cnn_latest.h5       # Trained CNN model
│   ├── upi_fraud_scaler_latest.pkl   # Feature scaler
│   ├── le_bank/category/device/network_latest.pkl  # Label encoders
│   ├── feature_names_latest.npy      # Feature order
│   ├── best_threshold_latest.npy     # Optimal decision threshold
│   └── requirements.txt
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── qr/                 # Generated QR codes
├── templates/              # All HTML pages
└── .env                    # Environment variables (not committed)
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/securepay-ml.git
cd securepay-ml
```

### 2. Install dependencies

```bash
pip install flask mysql-connector-python tensorflow scikit-learn joblib numpy qrcode python-dotenv
```

### 3. Set up the database

```bash
mysql -u root -p < database/schema.sql
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=<your_mysql_password>
DB_NAME=securepay

EMAIL_ADDRESS=<verified_sender_email>
EMAIL_PASSWORD=<brevo_api_key>
```

> Configure a verified sender email in Brevo before sending OTP emails.

### 5. Run the app

```bash
python app.py
```

Visit `http://localhost:5000`

---

## How Fraud Detection Works

Each payment triggers the CNN model with 23 features:

| Signal | Features |
|---|---|
| Transaction | amount, category, time (hour/day/month) |
| Behavioral | ratio to avg amount, txns last 1hr/10min, spending trend |
| Security | PIN retries, failed login attempts, OTP attempts |
| Device | device type, is_new_device (fingerprint comparison) |
| Location | latitude/longitude, distance from prev txn, is_new_location |
| Account | account age, user age, bank |

**Fraud response tiers:**
- Score ≥ threshold → **BLOCKED** immediately
- Amount ≥ ₹50,000 with unusual ratio → **DOB confirmation** required
- Amount ≥ ₹1,00,000 with unusual ratio → **Auto-blocked**, no confirmation

---

## Project Summary

SecurePay was built to simulate a real-world UPI payment system with AI-powered fraud prevention at its core. Here's a quick overview of what the system does end-to-end:

**User Flow**
1. User enters mobile number → OTP sent to registered email
2. OTP verified → session created with device fingerprint
3. User initiates payment → CNN model scores the transaction in real-time
4. Based on fraud score and amount, transaction is either approved, flagged for DOB confirmation, or blocked

**Merchant Flow**
1. Any user can register as a merchant with a UPI ID and category
2. A QR code is auto-generated for the merchant's UPI
3. Merchants can view all incoming transactions on their dashboard

**Admin Flow**
1. Admin logs in with username + password (MD5 hashed)
2. Full control over users, merchants, and transaction records
3. Can create, edit, or delete user accounts

**Fraud Detection Pipeline**
```
Payment Request
     ↓
Extract 23 features (behavioral + device + location + account)
     ↓
Label encode categoricals → Scale with StandardScaler
     ↓
CNN model predicts fraud score (0.0 – 1.0)
     ↓
Score ≥ threshold  →  BLOCKED
Amount ≥ ₹50,000 + high ratio  →  DOB confirmation
Score < threshold  →  SUCCESS
```

**Key Design Decisions**
- Threshold tuned to `0.08` to catch real fraud while ignoring small noise
- Haversine formula used to calculate distance from user's home state
- Device fingerprint stored on first login, compared on every payment
- Spending trend only flagged when amount > ₹5,000 AND this month is 10x+ last month

---

## License

This project is for educational purposes.
