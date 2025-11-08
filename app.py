from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
import os
import json
import io
import math
import pandas as pd
from fpdf import FPDF
from utils.hashing import HashTable, rebuild_hashtable_from_list
from utils.searching import search_by_id, search_by_name
from utils.sorting import sort_employees_by_percentage

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "database.json")
HASH_TABLE_SIZE = 20  # change if you want larger table

app = Flask(__name__)
CORS(app)

# Initialize in-memory store + hash table
if not os.path.exists(DB_PATH):
    with open(DB_PATH, "w") as f:
        json.dump([], f, indent=2)

with open(DB_PATH, "r") as f:
    try:
        database = json.load(f)
    except Exception:
        database = []

# Build hash table from stored database
hash_table = HashTable(size=HASH_TABLE_SIZE)
rebuild_hashtable_from_list(hash_table, database)


def save_database_from_hashtable():
    """
    Persist flattened entries from hash table to database.json
    (keeps stable ordering as list of stored items)
    """
    entries = [entry for entry in hash_table.flatten() if entry is not None]
    with open(DB_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def process_records(raw_list):
    """
    Accepts list of dicts with keys:
    id, name, department, attendance, total_days
    Returns list of processed records (with attendance_percentage and hash_index)
    and inserts them into hash_table (replacing same id if present).
    """
    processed = []
    for rec in raw_list:
        try:
            emp_id = int(rec.get("id"))
            name = str(rec.get("name", "")).strip()
            dept = str(rec.get("department", "")).strip()
            attendance = int(rec.get("attendance", 0))
            total_days = int(rec.get("total_days", 0)) if rec.get("total_days") is not None else 0
        except Exception:
            continue

        percent = 0.0
        if total_days > 0:
            percent = round((attendance / total_days) * 100, 1)
        hash_idx = emp_id % HASH_TABLE_SIZE

        record = {
            "id": emp_id,
            "name": name,
            "department": dept,
            "attendance": attendance,
            "total_days": total_days,
            "attendance_percentage": percent,
            "hash_index": hash_idx
        }

        hash_table.insert(record)
        processed.append(record)

    save_database_from_hashtable()
    return processed


# ✅ Root route to confirm backend is active
@app.route("/", methods=["GET"])
def home():
    return "✅ Backend is active", 200


@app.route("/upload", methods=["POST"])
def upload():
    if request.is_json and not request.files:
        payload = request.get_json()
        if isinstance(payload, list):
            processed = process_records(payload)
            return jsonify({"status": "success", "count": len(processed), "data": processed}), 200
        else:
            return jsonify({"status": "error", "message": "JSON body must be a list of records"}), 400

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400

    file = request.files['file']
    filename = file.filename.lower()

    if filename.endswith(".json"):
        try:
            file_json = json.load(file)
            if not isinstance(file_json, list):
                return jsonify({"status": "error", "message": "JSON must be an array of records"}), 400
            processed = process_records(file_json)
            return jsonify({"status": "success", "count": len(processed), "data": processed}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Invalid JSON file: {str(e)}"}), 400

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            df = pd.read_excel(file)
            df_columns = [c.lower() for c in df.columns]
            required = {"id", "name", "department", "attendance", "total_days"}
            if not required.issubset(set(df_columns)):
                return jsonify({"status": "error", "message": f"Excel must contain columns: {required}"}), 400

            df.columns = [c.lower() for c in df.columns]
            records = df.to_dict(orient="records")
            processed = process_records(records)
            return jsonify({"status": "success", "count": len(processed), "data": processed}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to parse Excel: {str(e)}"}), 400

    return jsonify({"status": "error", "message": "Unsupported file type. Use .json or .xlsx"}), 400


@app.route("/view", methods=["GET"])
def view_all():
    all_records = [r for r in hash_table.flatten() if r is not None]
    return jsonify(all_records), 200


@app.route("/hashview", methods=["GET"])
def hash_view():
    table = hash_table.as_list()
    return jsonify(table), 200


@app.route("/search/id/<int:emp_id>", methods=["GET"])
def api_search_id(emp_id):
    result, steps = search_by_id(hash_table, emp_id)
    if result is None:
        return jsonify({"found": False, "trace": steps}), 404
    return jsonify({"found": True, "trace": steps, "record": result}), 200


@app.route("/search/name/<string:name>", methods=["GET"])
def api_search_name(name):
    results, steps = search_by_name(hash_table, name)
    if not results:
        return jsonify({"found": False, "trace": steps}), 404
    return jsonify({"found": True, "trace": steps, "records": results}), 200


# ✅ New dynamic search route (case-insensitive, partial matches)
@app.route("/search/dynamic", methods=["GET"])
def api_dynamic_search():
    """
    Dynamic search by id, name, and department.
    Example: /search/dynamic?name=go&id=12&department=cse
    """
    all_records = [r for r in hash_table.flatten() if r is not None]
    id_query = request.args.get("id", "").strip().lower()
    name_query = request.args.get("name", "").strip().lower()
    dept_query = request.args.get("department", "").strip().lower()

    results = []
    for r in all_records:
        if (
            (not id_query or id_query in str(r.get("id", "")).lower())
            and (not name_query or name_query in str(r.get("name", "")).lower())
            and (not dept_query or dept_query in str(r.get("department", "")).lower())
        ):
            results.append(r)

    return jsonify(results), 200


@app.route("/sort/<string:order>", methods=["GET"])
def api_sort(order):
    order = order.lower()
    if order not in ("asc", "desc"):
        return jsonify({"status": "error", "message": "order must be 'asc' or 'desc'"}), 400
    all_records = [r for r in hash_table.flatten() if r is not None]
    sorted_list = sort_employees_by_percentage(all_records, order)
    return jsonify(sorted_list), 200


@app.route("/filter/above/<int:percent>", methods=["GET"])
def api_filter(percent):
    all_records = [r for r in hash_table.flatten() if r is not None]
    filtered = [r for r in all_records if r.get("attendance_percentage", 0) >= percent]
    return jsonify(filtered), 200


@app.route("/download/pdf/<int:percent>", methods=["GET"])
def api_download_pdf(percent):
    all_records = [r for r in hash_table.flatten() if r is not None]
    filtered = [r for r in all_records if r.get("attendance_percentage", 0) >= percent]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Employees with attendance >= {percent}%", ln=True, align="C")
    pdf.ln(4)

    col_widths = [20, 50, 35, 25, 25]
    headers = ["ID", "Name", "Department", "Attendance %", "Hash Index"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1)
    pdf.ln()

    for r in filtered:
        pdf.cell(col_widths[0], 8, str(r.get("id", "")), border=1)
        pdf.cell(col_widths[1], 8, str(r.get("name", ""))[:30], border=1)
        pdf.cell(col_widths[2], 8, str(r.get("department", ""))[:20], border=1)
        pdf.cell(col_widths[3], 8, str(r.get("attendance_percentage", "")), border=1)
        pdf.cell(col_widths[4], 8, str(r.get("hash_index", "")), border=1)
        pdf.ln()

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    response = make_response(pdf_output.read())
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename=f'employees_{percent}_percent.pdf')
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7077, debug=True)
