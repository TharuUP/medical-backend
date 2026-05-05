from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import datetime
import os
import cloudinary.api
import pytz
import cloudinary
import cloudinary.uploader
#import cloudinary.utils

import os

app = Flask(__name__)



CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

DB_FILE = 'medical_assistance.db'

cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

@app.route("/")
def home():
    return "Backend is running 🚀"

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        print("🔥 FILE RECEIVED")   # ADD
        file = request.files['file']
        patient_name = request.form.get('patientName', 'general')

        print("🔥 NAME:", file.filename)
        print("🔥 PATIENT:", patient_name)

        result = cloudinary.uploader.upload(
            file.stream,  
            folder=f"patients/{patient_name}",
            resource_type="auto"
        )

        print("🔥 UPLOADED:", result)

        return jsonify({
            "success": True,
            "url": result['secure_url'],
            "public_id": result['public_id'],
            "name": file.filename
        })

    except Exception as e:
        print("🔥 ERROR:", str(e))   # 🔥 ADD THIS
        return jsonify({"error": str(e)}), 500

'''
@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    try:
        data = request.json
        public_id = data.get("public_id")

        print("🔥 DELETE ID:", public_id)   # 👈 ADD THIS

        result = cloudinary.uploader.destroy(public_id)

        if result.get("result") == "not found":
            result = cloudinary.uploader.destroy(public_id, resource_type="raw")

        print("🔥 RESULT:", result)  # 👈 ADD THIS

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
'''
@app.route('/api/files/<patientName>', methods=['GET'])
def get_files(patientName):
    try:
        result = cloudinary.api.resources(
            type="upload",
            prefix=f"patients/{patientName}",
            resource_type="auto",
            max_results=100
        )

        files = []

        for r in result.get("resources", []):
            files.append({
                "url": r["secure_url"],
                "name": r["public_id"].split("/")[-1],
                "public_id": r["public_id"]
            })

        return jsonify(files)


    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    try:
        data = request.json
        public_id = data.get("public_id")

        result = cloudinary.uploader.destroy(public_id, resource_type="auto")

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
@app.route('/api/files/<patientName>', methods=['GET'])
def get_files(patientName):
    try:
        folder_path = f"patients/{patientName}"

        files = []

        # 🔥 GET IMAGES
        images = cloudinary.api.resources(
            type="upload",
            prefix=folder_path,
            resource_type="image",
            max_results=50
        )

        # 🔥 GET RAW (PDF)
        raws = cloudinary.api.resources(
            type="upload",
            prefix=folder_path,
            resource_type="raw",
            max_results=50
        )

        # IMAGES
        for r in images.get('resources', []):
            ext = r.get('format') or "jpg"

            files.append({
                "url": r['secure_url'],
                "name": r['public_id'].split('/')[-1] + "." + ext,
                "public_id": r['public_id']
            })

        # PDF / RAW
        for r in raws.get('resources', []):
            full_public_id = r['public_id']
            file_name = full_public_id.split('/')[-1]

            # ensure extension
            if not file_name.lower().endswith('.pdf'):
                file_name += ".pdf"

            # 🔥 FORCE DOWNLOAD NAME
            import urllib.parse

            encoded_id = urllib.parse.quote(full_public_id)

            url, options = cloudinary.utils.cloudinary_url(
                full_public_id,
                resource_type="raw",
                secure=True,
                flags="attachment"
            )
            files.append({
                "url": url,
                "name": file_name,
                "public_id": full_public_id
            })

        return jsonify(files)

    except Exception as e:
        print("🔥 CLOUDINARY ERROR:", e)
        return jsonify({"error": str(e)}), 500
'''
'''
@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        patient_name = request.form.get('patientName', 'general')

        import os

        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext == ".pdf":
            filename = os.path.splitext(file.filename)[0]

            import datetime
            unique_name = f"{filename}_{int(datetime.datetime.now().timestamp())}"

            result = cloudinary.uploader.upload(
                file,
                public_id=unique_name,   # ✅ avoid overwrite
                resource_type="raw",
                folder=f"patients/{patient_name}",
                #format="pdf",
                use_filename=True,
                unique_filename=False
            )
        else:
            result = cloudinary.uploader.upload(
                file,
                resource_type="image",  # ✅ IMAGE ONLY
                folder=f"patients/{patient_name}",
        type="upload"
    )

        return jsonify({
            "success": True,
            "url": result['secure_url'],
            "public_id": result['public_id']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
'''
# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            signIn TEXT,
            signOut TEXT,
            location TEXT,
            status TEXT,
            revised INTEGER DEFAULT 0,
            revisedBy TEXT
        )
    ''')

    # Create default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('admin', '1234', 'Admin'))

    # Cases Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patientName TEXT NOT NULL,
            insuranceCo TEXT,
            location TEXT,
            refNumber TEXT UNIQUE,
            paxDob TEXT,
            paxOther TEXT,
            hospitalName TEXT,
            hospitalAddress TEXT,
            treatingDoctor TEXT,
            insuranceDesk TEXT,
            doa TEXT,
            roomNo TEXT,
            dod TEXT,
            policyExcess TEXT,
            symptoms TEXT,
            notes TEXT,
            status TEXT DEFAULT 'Ongoing',
            createdAt TEXT,
            createdBy TEXT
        )
    ''')

    # Bills Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patientName TEXT,
            hospital TEXT,
            receivedDate TEXT,
            toBePaid TEXT,
            amount TEXT,
            paid TEXT,
            paidDate TEXT,
            createdBy TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            firstName TEXT,
            lastName TEXT,
            mobile TEXT,
            position TEXT,
            workingHours TEXT,
            dob TEXT,
            image TEXT
        )
    ''')

    conn.commit()
    conn.close()



'''def get_or_create_patient_folder(patient_name):
    query = f"name = '{patient_name}' and '{PARENT_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(
        q=query,
        fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    items = results.get('files', [])
    if not items:
        file_metadata = {'name': patient_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [PARENT_FOLDER_ID]}
        folder = drive_service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return folder.get('id')
    return items[0]['id']'''
 # ✅ MUST BE HERE
# --- API ROUTES ---



@app.route('/api/import-bills', methods=['POST'])
def import_bills():
    try:
        import pandas as pd

        file = request.files['file']

        df = pd.read_excel(file)

        def clean(val):
            if pd.isna(val):
                return "NA"

            val = str(val).strip()

            if val == "" or val.lower() in ["na", "n/a", "not applicable"]:
                return "NA"

            return val

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM bills")

        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO bills (
                    patientName, hospital, receivedDate,
                    toBePaid, amount, paid, paidDate, createdBy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                clean(row.get('PATIENTS NAME')),
                clean(row.get('HOSPITAL/ Providers')),
                clean(row.get('BILLS RECEIVED DATE')),
                clean(row.get('TO BE PAID')),
                clean(row.get('AMOUNT')),
                clean(row.get('PAID')),
                clean(row.get('Paid Date')),
                "Excel Import"
            ))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print("🔥 IMPORT ERROR:", e)   # 👈 VERY IMPORTANT
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def save_profile():
    data = request.json
    username = data.get('username')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profiles WHERE username=?", (username,))
    exists = cursor.fetchone()

    if exists:
        cursor.execute('''
            UPDATE profiles SET
                firstName=?, lastName=?, mobile=?, position=?,
                workingHours=?, dob=?, image=?
            WHERE username=?
        ''', (
            data.get('firstName'),
            data.get('lastName'),
            data.get('mobile'),
            data.get('position'),
            data.get('workingHours'),
            data.get('dob'),
            data.get('image'),
            username
        ))
    else:
        cursor.execute('''
            INSERT INTO profiles (
                username, firstName, lastName, mobile,
                position, workingHours, dob, image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            data.get('firstName'),
            data.get('lastName'),
            data.get('mobile'),
            data.get('position'),
            data.get('workingHours'),
            data.get('dob'),
            data.get('image')
        ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route('/api/profile/<username>', methods=['GET'])
def get_profile(username):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profiles WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify(dict(row))
    else:
        return jsonify({})

@app.route('/api/change-password', methods=['POST'])
def change_password_self():
    data = request.json
    username = data.get('username')
    new_password = data.get('newPassword')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))

    conn.commit()
    conn.close()

    return jsonify({"success": True})



@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "success": True,
            "user": {
                "name": user['username'],
                "role": user['role'],
                "email": f"{user['username']}@slmedical.lk"
            }
        })

    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, role FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', (data['username'], data['password'], data['role']))
        conn.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "User already exists"}), 400
    finally:
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route('/api/users/<int:user_id>/password', methods=['PUT'])
def change_password(user_id):
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET password=? WHERE id=?", (data['password'], user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route('/api/cases/<int:case_id>', methods=['DELETE'])
def delete_case(case_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cases WHERE id=?", (case_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route('/api/cases', methods=['GET', 'POST'])
def handle_cases():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.json

        try:
            # 🔵 UPDATE (if id exists)
            if data.get('id'):
                cursor.execute('''
                    UPDATE cases SET
                        patientName=?, insuranceCo=?, location=?, refNumber=?,
                        paxDob=?, paxOther=?, hospitalName=?, hospitalAddress=?,
                        treatingDoctor=?, insuranceDesk=?, doa=?, roomNo=?,
                        dod=?, policyExcess=?, symptoms=?, notes=?, status=?
                    WHERE id=?
                ''', (
                    data['patientName'], data['insuranceCo'], data['location'], data['refNumber'],
                    data['paxDob'], data['paxOther'], data['hospitalName'], data['hospitalAddress'],
                    data['treatingDoctor'], data['insuranceDesk'], data['doa'], data['roomNo'],
                    data['dod'], data['policyExcess'], data['symptoms'], data['notes'],
                    data['status'], data['id']
                ))

                conn.commit()
                return jsonify({"success": True, "message": "Case updated successfully"})

            # 🟢 INSERT (new case)
            else:
                cursor.execute('''
                    INSERT INTO cases (
                        patientName, insuranceCo, location, refNumber, paxDob, paxOther,
                        hospitalName, hospitalAddress, treatingDoctor, insuranceDesk,
                        doa, roomNo, dod, policyExcess, symptoms, notes, status, createdAt, createdBy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['patientName'], data['insuranceCo'], data['location'], data['refNumber'],
                    data['paxDob'], data['paxOther'], data['hospitalName'], data['hospitalAddress'],
                    data['treatingDoctor'], data['insuranceDesk'], data['doa'], data['roomNo'],
                    data['dod'], data['policyExcess'], data['symptoms'], data['notes'],
                    data['status'], data['createdAt'], data['createdBy']
                ))

                conn.commit()
                return jsonify({"success": True, "message": "Case saved successfully"})

        except sqlite3.IntegrityError:
            return jsonify({"success": False, "message": "Reference number already exists"}), 400

        finally:
            conn.close()

    # GET method
    cursor.execute('SELECT * FROM cases ORDER BY id DESC')
    rows = cursor.fetchall()
    cases = [dict(row) for row in rows]
    conn.close()
    return jsonify(cases)

'''@app.route('/api/drive/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    # Handle the 'Preflight' request from the browser
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    try:
        data = request.json
        patient_name = data['patientName']
        file_name = data['fileName']
        mime_type = data['mimeType']

        # FIX: Ensure we handle the base64 string correctly
        file_data_str = data['fileData']
        if "," in file_data_str:
            file_data_str = file_data_str.split(",")[1]

        file_content = base64.b64decode(file_data_str)

        folder_id = get_or_create_patient_folder(patient_name)
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mime_type)

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True   # 🔥 IMPORTANT
        ).execute()

        return jsonify({"success": True, "file_id": file.get('id')})
    except Exception as e:
        print(f"!!! UPLOAD CRASH: {str(e)}") # LOOK AT YOUR TERMINAL FOR THIS
        return jsonify({"success": False, "error": str(e)}), 500 '''


@app.route('/api/bills', methods=['GET', 'POST'])
def handle_bills():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.json

        try:
            patientName = data.get('patientName')
            hospital = data.get('hospital')
            receivedDate = data.get('receivedDate')
            toBePaid = data.get('toBePaid')
            amount = data.get('amount')
            paid = data.get('paid')
            paidDate = data.get('paidDate')
            createdBy = data.get('createdBy', 'Unknown')  # ✅ SAFE

            cursor.execute('''
                INSERT INTO bills (
                    patientName, hospital, receivedDate,
                    toBePaid, amount, paid, paidDate, createdBy
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patientName, hospital, receivedDate,
                toBePaid, amount, paid, paidDate, createdBy
            ))

            conn.commit()
            return jsonify({"success": True, "message": "Bill recorded"})

        except Exception as e:
            print("ERROR:", e)  # 🔥 VERY IMPORTANT
            return jsonify({"success": False, "error": str(e)}), 500

        finally:
            conn.close()
     # ✅ ADD THIS PART (GET)
    cursor.execute('SELECT * FROM bills ORDER BY id DESC')
    rows = cursor.fetchall()
    bills = [dict(row) for row in rows]

    conn.close()
    return jsonify(bills)

@app.route('/api/attendance/<username>/<month>', methods=['GET'])
def get_attendance_by_month(username, month):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM attendance
        WHERE username=? AND substr(date, 1, 7)=?
        ORDER BY date ASC
    ''', (username, month))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

@app.route('/api/attendance/signin', methods=['POST'])
def sign_in():
    data = request.json
    username = data['username']
    today = datetime.date.today().isoformat()
    sri_lanka = pytz.timezone("Asia/Colombo")
    now = datetime.datetime.now(sri_lanka).strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM attendance WHERE username=? AND date=?", (username, today))
    if cursor.fetchone():
        return jsonify({"error": "Already signed in"}), 400

    cursor.execute('''
        INSERT INTO attendance (username, date, signIn, location, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, today, now, data.get('location'), 'Present'))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route('/api/attendance/signout', methods=['POST'])
def sign_out():
    data = request.json
    username = data['username']
    today = datetime.date.today().isoformat()
    sri_lanka = pytz.timezone("Asia/Colombo")
    now = datetime.datetime.now(sri_lanka).strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE attendance
        SET signOut=?
        WHERE username=? AND date=?
    ''', (now, username, today))

    conn.commit()
    conn.close()

    return jsonify({"success": True})



@app.route('/api/bills/<int:id>', methods=['PUT'])
def update_bill(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    data = request.json

    try:
        cursor.execute('''
            UPDATE bills SET
                patientName = ?,
                hospital = ?,
                receivedDate = ?,
                toBePaid = ?,
                amount = ?,
                paid = ?,
                paidDate = ?,
                createdBy = ?
            WHERE id = ?
        ''', (
            data.get('patientName'),
            data.get('hospital'),
            data.get('receivedDate'),
            data.get('toBePaid'),
            data.get('amount'),
            data.get('paid'),
            data.get('paidDate'),
            data.get('createdBy'),
            id
        ))

        conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    finally:
        conn.close()

@app.route('/api/attendance/leave', methods=['POST'])
def mark_leave():
    data = request.json
    username = data['username']
    date = data['date']

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO attendance (username, date, status)
        VALUES (?, ?, ?)
    ''', (username, date, 'Leave'))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

@app.route('/api/attendance/update', methods=['POST'])
def update_attendance():
    data = request.json

    username = data['username']
    date = data['date']
    signIn = data.get('signIn')
    signOut = data.get('signOut')
    location = data.get('location')
    editedBy = data.get('editedBy')

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE attendance
        SET signIn=?, signOut=?, location=?, revised=1, revisedBy=?
        WHERE username=? AND date=?
    ''', (signIn, signOut, location, editedBy, username, date))

    conn.commit()
    conn.close()

    return jsonify({"success": True})
    
@app.route('/api/bills/<int:id>', methods=['DELETE'])
def delete_bill(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM bills WHERE id=?", (id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

init_db()  

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)