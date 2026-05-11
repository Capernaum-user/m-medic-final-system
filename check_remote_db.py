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
    cursor = conn.cursor()
    
    print("[*] Tables in Remote DB:")
    cursor.execute("SHOW TABLES")
    for (table_name,) in cursor:
        print(f" - {table_name}")
        
    # Check for vitals table
    cursor.execute("SHOW TABLES LIKE '%vital%'")
    vitals_table = cursor.fetchone()
    if vitals_table:
        print(f"\n[*] Vitals table found: {vitals_table[0]}")
        cursor.execute(f"DESC {vitals_table[0]}")
        print("[*] Structure:")
        for col in cursor:
            print(f"   {col}")
    else:
        print("\n[!] No vitals table found with 'vital' in name.")
        
    conn.close()
except Exception as e:
    print(f"[!] Error: {e}")
