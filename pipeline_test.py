import sys, numpy as np, joblib
sys.stdout.reconfigure(encoding='utf-8')
from tensorflow.keras.models import load_model

model = load_model('model/upi_fraud_cnn_latest.h5', compile=False)
scaler = joblib.load('model/upi_fraud_scaler_latest.pkl')
le_bank = joblib.load('model/le_bank_latest.pkl')
le_category = joblib.load('model/le_category_latest.pkl')
le_device = joblib.load('model/le_device_latest.pkl')
le_network = joblib.load('model/le_network_latest.pkl')
feature_names = np.load('model/feature_names_latest.npy', allow_pickle=True)
threshold = 0.30  # lowered threshold

def predict(amount, avg_amount, txns_1hr, txns_10min, time_since):
    ratio = amount / avg_amount if avg_amount > 0 else 1.0
    f = {
        'trans_hour': 14, 'trans_day_of_week': 2, 'trans_month': 5,
        'amount': amount,
        'category': le_category.transform(['Education'])[0],
        'distance_from_prev_txn_km': 0,
        'time_since_prev_txn_hrs': time_since,
        'device_type': le_device.transform(['Android'])[0],
        'network_type': le_network.transform(['4G'])[0],
        'is_new_device': 0, 'is_new_location': 0,
        'txns_last_1hr': txns_1hr, 'txns_last_10min': txns_10min,
        'ratio_to_avg_amount': ratio,
        'failed_login_attempts': 0, 'otp_verification_attempts': 1,
        'pin_retries': 0, 'account_age_days': 1,
        'user_age': 17,
        'bank': le_bank.transform(['SBI'])[0],
        'is_odd_hour': 0, 'is_foreign_location': 0, 'spending_trend': 0
    }
    arr = scaler.transform(np.array([[f[k] for k in feature_names]]))
    score = model.predict(arr, verbose=0)[0][0]
    result = "FRAUD BLOCKED" if score >= threshold else "SUCCESS"
    print(f"Rs{amount:>10,} | avg=Rs{avg_amount:>6,.0f} | ratio={ratio:>6.1f}x | txns_10min={txns_10min} | score={score:.4f} | {result}")

print(f"\nThreshold: {threshold}\n")
print("Payment sequence: 100 -> 200 -> 500 -> 800 -> 1000 -> 1500 -> 50000\n")

payments = [100, 200, 500, 800, 1000, 1500]
running_sum = 0

for i, amt in enumerate(payments):
    running_avg = running_sum / i if i > 0 else amt
    predict(amt, running_avg if i > 0 else amt, i, min(i, 6), 0.1)
    running_sum += amt

# Big payment
avg_after = running_sum / len(payments)
predict(50000, avg_after, 6, 6, 0.1)
