# SecurePay — AI-Powered UPI Fraud Detection System

> 🌐 **Live Demo:** [Add your link here once deployed]

SecurePay is a full-stack UPI payment simulation platform with a built-in CNN-based fraud detection model. Every transaction is analyzed in real-time using behavioral, geolocation, and device signals to block fraudulent payments before they go through.

---

## Features

- **OTP-based login** — 6-digit OTP sent to registered email, expires in 5 minutes
- **Real-time fraud detection** — CNN model scores every transaction before it's processed
- **Multi-signal analysis** — device fingerprint, geolocation, spending patterns, PIN retries, login failures
- **Tiered fraud response** — auto-block for high-risk, DOB confirmation for medium-risk, pass for low-risk
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
| Auth | OTP via Gmail SMTP, device fingerprinting |
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
git clone https://github.com/<your-username>/SecurePay.git
cd SecurePay
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

EMAIL_ADDRESS=<your_gmail>
EMAIL_PASSWORD=<your_gmail_app_password>
```

> For Gmail, use an [App Password](https://myaccount.google.com/apppasswords), not your regular password.

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

## Default Admin Login

```
Username: admin
Password: admin123
```

> Change this immediately after setup.

---

## Sample Test Users

| Name | Mobile | DOB |
|---|---|---|
| Test User | 8888888888 | 2000-01-01 |
| Deekshitha | 7702777044 | 2004-05-18 |

---

## Screenshots

> Add screenshots here after deployment

---

## License

This project is for educational purposes.
