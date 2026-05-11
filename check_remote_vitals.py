import mysql.connector
import sys

try:
    conn = mysql.connector.connect(
        host='project-db-campus.smhrd.com',
        port=3307,
        user='MDTS',
        password='12345',
        database='MDTS'
    )
    cursor = conn.cursor(dictionary=True)
    
    print("[*] Latest 5 Vitals in tb_vital:")
    cursor.execute("SELECT * FROM tb_vital ORDER BY measured_at DESC LIMIT 5")
    for row in cursor:
        print(f" - ID: {row['vital_id']}, Time: {row['measured_at']}, HR: {row['heart_rate']}, SpO2: {row['spo2']}, BP: {row['blood_pressure']}, Temp: {row['temperature']}")
        
    conn.close()
except Exception as e:
    print(f"[!] Error: {e}")
