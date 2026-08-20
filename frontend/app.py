import os
import requests
from flask import Flask, render_template, redirect, url_for, request, session, flash, send_from_directory, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "FLASK_SUPER_SECRET_KEY_CHANGE_ME")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api/v1")

def api_request(method: str, path: str, token: str = None, **kwargs):
    """Utility to proxy requests to FastAPI backend"""
    url = f"{BACKEND_URL}{path}"
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        return response
    except Exception as e:
        print(f"API Request failed: {e}")
        return None

@app.context_processor
def inject_user_context():
    """Inject current user metadata into templates"""
    return {
        "logged_in": "access_token" in session,
        "current_role": session.get("user_role"),
        "current_user_email": session.get("user_email"),
        "current_researcher_id": session.get("researcher_id")
    }

# Authenication decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "access_token" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        if not session.get("user_verified", False):
            flash("Please verify your email address to access this functionality.", "warning")
            return redirect(url_for("verify_email_notice", email=session.get("user_email", "")))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    if "access_token" in session:
        if not session.get("user_verified", False):
            return redirect(url_for("verify_email_notice", email=session.get("user_email", "")))
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # FastAPI login uses OAuth2 Form Data
        res = api_request("POST", "/auth/login", data={"username": email, "password": password})
        if res and res.status_code == 200:
            token_data = res.json()
            session["access_token"] = token_data["access_token"]
            session["refresh_token"] = token_data["refresh_token"]
            session["user_email"] = email
            
            # Fetch user profile to get role and researcher profile id
            res_user = api_request("GET", "/users/me", token=token_data["access_token"])
            is_verified = False
            if res_user and res_user.status_code == 200:
                is_verified = res_user.json().get("is_verified", False)
            session["user_verified"] = is_verified
            
            # Decode JWT payload (middle part) manually to avoid dependency on 'jose' package
            import base64
            import json
            try:
                parts = token_data["access_token"].split(".")
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                session["user_id"] = payload.get("sub")
                session["user_role"] = payload.get("role")
            except Exception:
                session["user_role"] = "researcher"
                
            # If user is researcher, fetch their researcher profile id
            if session["user_role"] == "researcher":
                res_profile = api_request("GET", "/researchers/", token=token_data["access_token"])
                if res_profile and res_profile.status_code == 200:
                    for prof in res_profile.json():
                        if str(prof["user_id"]) == str(session["user_id"]):
                            session["researcher_id"] = prof["id"]
                            break
            
            if not is_verified:
                flash("Please verify your email address.", "warning")
                return redirect(url_for("verify_email_notice", email=email))
                
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials. Please try again."
            if res:
                try:
                    error = res.json().get("detail", error)
                except Exception:
                    pass
            flash(error, "danger")
            
    return render_template("auth/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "researcher")
        full_name = request.form.get("full_name")
        orcid_id = request.form.get("orcid_id")
        mobile_number = request.form.get("mobile_number")
        gender = request.form.get("gender")
        gender_other = request.form.get("gender_other")
        country = request.form.get("country")
        city = request.form.get("city")
        institution = request.form.get("institution")
        department = request.form.get("department")
        interests = [i.strip() for i in request.form.get("interests", "").split(",") if i.strip()]
        
        res = api_request("POST", "/auth/register", json={
            "email": email,
            "password": password,
            "role": role
        })
        if res and res.status_code == 201:
            user_data = res.json()
            # If they registered as a researcher, auto-create researcher profile with demographics
            if role == "researcher":
                res_login = api_request("POST", "/auth/login", data={"username": email, "password": password})
                if res_login and res_login.status_code == 200:
                    tok = res_login.json()["access_token"]
                    api_request("POST", "/researchers/", token=tok, json={
                        "user_id": user_data["id"],
                        "full_name": full_name or email.split("@")[0],
                        "orcid_id": orcid_id,
                        "mobile_number": mobile_number or None,
                        "gender": gender or "prefer_not_to_say",
                        "gender_other": gender_other or None,
                        "nationality": None,
                        "country": country or None,
                        "city": city or None,
                        "institution_name": institution or None,
                        "department_name": department or None,
                        "research_interests": interests
                    })
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            error = "Registration failed."
            if res:
                try:
                    err_json = res.json()
                    if isinstance(err_json.get("detail"), list):
                        error = err_json["detail"][0].get("msg", error)
                    else:
                        error = err_json.get("detail", error)
                except Exception:
                    pass
            flash(error, "danger")
            
    res_inst = api_request("GET", "/institutions/")
    inst_list = res_inst.json() if res_inst and res_inst.status_code == 200 else []
    res_dept = api_request("GET", "/departments/")
    dept_list = res_dept.json() if res_dept and res_dept.status_code == 200 else []
    
    return render_template("auth/register.html", institutions=inst_list, departments=dept_list)

@app.route("/verify-email")
def verify_email_notice():
    email = request.args.get("email", "")
    token = request.args.get("token")
    if token:
        res = api_request("POST", "/auth/verify-email", json={"token": token})
        if res and res.status_code == 200:
            if "access_token" in session:
                session["user_verified"] = True
                flash("Email verified successfully!", "success")
                return redirect(url_for("dashboard"))
            flash("Email verified successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Verification failed or link expired.", "danger")
    return render_template("auth/verify.html", email=email)

@app.route("/api/resend-verification", methods=["POST"])
def api_resend_verification():
    email = request.form.get("email")
    if not email:
        return {"success": False, "message": "Email is required."}, 400
    res = api_request("POST", "/auth/resend-verification", json={"email": email})
    if res and res.status_code in [200, 201]:
        return {"success": True, "message": "Verification link sent!"}
    return {"success": False, "message": "Failed to resend verification link."}, 400

@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("user_role", "researcher")
    token = session.get("access_token")
    
    if role == "system_admin":
        res = api_request("GET", "/dashboards/admin", token=token)
        data = res.json() if res and res.status_code == 200 else {}
        return render_template("dashboard.html", view="admin", data=data)
    elif role == "institution_admin":
        res = api_request("GET", "/dashboards/institution/1", token=token)
        data = res.json() if res and res.status_code == 200 else {}
        return render_template("dashboard.html", view="institution", data=data)
    else:
        res_id = session.get("researcher_id")
        if not res_id:
            flash("Researcher profile not found. Please set up your profile.", "warning")
            return redirect(url_for("researcher_profile_edit"))
        res = api_request("GET", f"/dashboards/researcher/{res_id}", token=token)
        data = res.json() if res and res.status_code == 200 else {}
        
        # Fetch completion status
        res_comp = api_request("GET", f"/researchers/{res_id}/completion-status", token=token)
        completion_data = res_comp.json() if res_comp and res_comp.status_code == 200 else {}
        data["completion_status"] = completion_data
        
        return render_template("dashboard.html", view="researcher", data=data)

@app.route("/researchers")
@login_required
def researchers():
    token = session.get("access_token")
    res = api_request("GET", "/researchers/", token=token)
    data = res.json() if res and res.status_code == 200 else []
    return render_template("researchers.html", researchers=data)

@app.route("/researchers/<int:id>")
@login_required
def researcher_detail(id):
    token = session.get("access_token")
    res = api_request("GET", f"/researchers/{id}", token=token)
    if not res or res.status_code != 200:
        flash("Researcher profile not found.", "danger")
        return redirect(url_for("researchers"))
    profile = res.json()
    
    # Fetch publications, projects, and co-authors
    res_stats = api_request("GET", f"/dashboards/researcher/{id}", token=token)
    stats = res_stats.json() if res_stats and res_stats.status_code == 200 else {}
    
    return render_template("auth/profile_detail.html", profile=profile, stats=stats)

@app.route("/researchers/<int:id>/delete", methods=["POST"])
@login_required
def delete_researcher(id):
    token = session.get("access_token")
    role = session.get("user_role")
    if role not in ["system_admin", "institution_admin"]:
        flash("Only administrators can delete researcher profiles.", "danger")
        return redirect(url_for("researchers"))
        
    res = api_request("DELETE", f"/researchers/{id}", token=token)
    if res and res.status_code == 200:
        flash("Researcher profile deleted successfully.", "success")
    else:
        error_msg = "Failed to delete researcher profile."
        if res:
            try:
                error_msg = res.json().get("detail", error_msg)
            except Exception:
                pass
        flash(error_msg, "danger")
    return redirect(url_for("researchers"))

@app.route("/publications", methods=["GET", "POST"])
@login_required
def publications():
    token = session.get("access_token")
    
    res_id = session.get("researcher_id")
    current_researcher = None
    if res_id:
        res_current = api_request("GET", f"/researchers/{res_id}", token=token)
        if res_current and res_current.status_code == 200:
            current_researcher = res_current.json()

    if request.method == "POST":
        title = request.form.get("title")
        abstract = request.form.get("abstract")
        venue = request.form.get("venue")
        pub_date = request.form.get("publication_date")
        pub_type = request.form.get("type")
        status = request.form.get("status")
        doi = request.form.get("doi")
        
        payload = {
            "title": title,
            "abstract": abstract,
            "venue": venue,
            "type": pub_type,
            "status": status,
            "doi": doi or None
        }
        if pub_date:
            payload["publication_date"] = pub_date
            
        res = api_request("POST", "/publications/", token=token, json=payload)
        if res and res.status_code == 201:
            pub_data = res.json()
            flash("Publication entry created successfully!", "success")
            
            author_relations = []
            if current_researcher:
                author_relations.append(current_researcher["id"])
                
            co_author_ids = request.form.getlist("co_author_ids")
            for c_id in co_author_ids:
                if c_id and c_id.isdigit():
                    r_id = int(c_id)
                    if r_id not in author_relations:
                        author_relations.append(r_id)
            
            for idx, r_id in enumerate(author_relations):
                api_request("POST", "/publication-authors/", token=token, json={
                    "publication_id": pub_data["id"],
                    "researcher_id": r_id,
                    "author_order": idx + 1,
                    "is_corresponding_author": idx == 0
                })
            
            file = request.files.get("file")
            if file and file.filename:
                files = {"file": (secure_filename(file.filename), file.read(), file.content_type)}
                api_request("POST", f"/publications/{pub_data['id']}/upload", token=token, files=files)
                
            return redirect(url_for("publications"))
        else:
            flash("Failed to create publication entry.", "danger")
            
    res = api_request("GET", "/publications/", token=token)
    data = res.json() if res and res.status_code == 200 else []
    
    res_researchers = api_request("GET", "/researchers/", token=token)
    researchers_data = res_researchers.json() if res_researchers and res_researchers.status_code == 200 else []
    
    return render_template("publications.html", publications=data, researchers=researchers_data, current_researcher=current_researcher)

@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    token = session.get("access_token")
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        funding_source = request.form.get("funding_source")
        funding_amount = request.form.get("funding_amount")
        status = request.form.get("status")
        
        res = api_request("POST", "/projects/", token=token, json={
            "title": title,
            "description": description,
            "funding_source": funding_source,
            "funding_amount": float(funding_amount) if funding_amount else 0,
            "status": status
        })
        if res and res.status_code == 201:
            flash("Project created successfully!", "success")
        else:
            flash("Failed to create project.", "danger")
            
    res = api_request("GET", "/projects/", token=token)
    data = res.json() if res and res.status_code == 200 else []
    return render_template("projects.html", projects=data)

@app.route("/conferences", methods=["GET", "POST"])
@login_required
def conferences():
    token = session.get("access_token")
    if request.method == "POST":
        name = request.form.get("name")
        location = request.form.get("location")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        website = request.form.get("website")
        description = request.form.get("description")
        
        payload = {
            "name": name,
            "location": location,
            "website": website,
            "description": description
        }
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
            
        res = api_request("POST", "/conferences/", token=token, json=payload)
        if res and res.status_code == 201:
            flash("Conference registered successfully!", "success")
        else:
            flash("Failed to register conference.", "danger")
            
    res = api_request("GET", "/conferences/", token=token)
    data = res.json() if res and res.status_code == 200 else []
    return render_template("conferences.html", conferences=data)

@app.route("/network")
@login_required
def network():
    return render_template("network.html")

@app.route("/reports")
@login_required
def reports():
    token = session.get("access_token")
    res = api_request("GET", "/institutions/", token=token)
    insts = res.json() if res and res.status_code == 200 else []
    return render_template("reports.html", institutions=insts)

@app.route("/audit-logs")
@login_required
def audit_logs():
    token = session.get("access_token")
    role = session.get("user_role")
    if role not in ["system_admin", "institution_admin"]:
        flash("Access restricted to system administrators.", "danger")
        return redirect(url_for("dashboard"))
    res = api_request("GET", "/audit-logs/", token=token)
    data = res.json() if res and res.status_code == 200 else []
    return render_template("audit_logs.html", logs=data)

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    token = session.get("access_token")
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change_password":
            current_pass = request.form.get("current_password")
            new_pass = request.form.get("new_password")
            res = api_request("POST", "/auth/change-password", token=token, json={
                "current_password": current_pass,
                "new_password": new_pass
            })
            if res and res.status_code == 200:
                flash("Password updated successfully!", "success")
            else:
                err = "Failed to update password."
                if res:
                    try:
                        err_json = res.json()
                        if isinstance(err_json.get("detail"), list):
                            err = err_json["detail"][0].get("msg", err)
                        else:
                            err = err_json.get("detail", err)
                    except Exception:
                        pass
                flash(err, "danger")
    return render_template("settings.html")

@app.route("/help")
def help_page():
    return render_template("help.html")

@app.route("/researchers/edit", methods=["GET", "POST"])
@login_required
def researcher_profile_edit():
    token = session.get("access_token")
    role = session.get("user_role")
    
    # Handle researcher ID for admin editing
    param_id = request.form.get("id") or request.args.get("id")
    if param_id and role in ["system_admin", "institution_admin"]:
        res_id = int(param_id)
    else:
        res_id = session.get("researcher_id")
        
    # Fetch existing profile if available
    existing_profile = {}
    if res_id:
        res_ex = api_request("GET", f"/researchers/{res_id}", token=token)
        if res_ex and res_ex.status_code == 200:
            existing_profile = res_ex.json()

    if request.method == "POST":
        full_name = request.form.get("full_name")
        bio = request.form.get("bio")
        orcid = request.form.get("orcid_id")
        mobile_number = request.form.get("mobile_number")
        gender = request.form.get("gender")
        gender_other = request.form.get("gender_other")
        nationality = request.form.get("nationality")
        country = request.form.get("country")
        city = request.form.get("city")
        institution_name = request.form.get("institution_name")
        department_name = request.form.get("department_name")
        designation = request.form.get("designation")
        highest_qualification = request.form.get("highest_qualification")
        year_highest_qualification = request.form.get("year_highest_qualification")
        google_scholar_url = request.form.get("google_scholar_url")
        researchgate_url = request.form.get("researchgate_url")
        scopus_id = request.form.get("scopus_id")
        wos_id = request.form.get("wos_id")
        skills = [s.strip() for s in request.form.get("skills", "").split(",") if s.strip()]
        interests = [i.strip() for i in request.form.get("interests", "").split(",") if i.strip()]
        
        # If user is a researcher, the registration fields are disabled on frontend,
        # so they won't submit. We preserve their existing database values.
        if role == "researcher" and existing_profile:
            full_name = existing_profile.get("full_name") or full_name
            orcid = existing_profile.get("orcid_id") or orcid
            mobile_number = existing_profile.get("mobile_number") or mobile_number
            country = existing_profile.get("country") or country
            city = existing_profile.get("city") or city
            institution_name = existing_profile.get("institution_name") or institution_name
            department_name = existing_profile.get("department_name") or department_name

        payload = {
            "full_name": full_name,
            "bio": bio,
            "orcid_id": orcid or None,
            "mobile_number": mobile_number or None,
            "gender": gender or "prefer_not_to_say",
            "gender_other": gender_other or None,
            "nationality": nationality or None,
            "country": country or None,
            "city": city or None,
            "institution_name": institution_name or None,
            "department_name": department_name or None,
            "designation": designation or None,
            "highest_qualification": highest_qualification or None,
            "year_highest_qualification": int(year_highest_qualification) if year_highest_qualification and str(year_highest_qualification).isdigit() else None,
            "google_scholar_url": google_scholar_url or None,
            "researchgate_url": researchgate_url or None,
            "scopus_id": scopus_id or None,
            "wos_id": wos_id or None,
            "skills": skills,
            "research_interests": interests
        }
        
        if res_id:
            res = api_request("PUT", f"/researchers/{res_id}", token=token, json=payload)
        else:
            payload["user_id"] = int(session.get("user_id"))
            res = api_request("POST", "/researchers/", token=token, json=payload)
            
        if res and res.status_code in [200, 201]:
            updated_profile = res.json()
            # Only update session if editing own profile
            if not param_id or str(param_id) == str(session.get("researcher_id")):
                session["researcher_id"] = updated_profile["id"]
            flash("Profile updated successfully!", "success")
            
            # If admin was editing, go back to researcher detail
            if param_id and role in ["system_admin", "institution_admin"]:
                return redirect(url_for("researcher_detail", id=res_id))
            return redirect(url_for("dashboard"))
        else:
            err = "Failed to update profile."
            if res:
                try:
                    err_json = res.json()
                    if isinstance(err_json.get("detail"), list):
                        err = err_json["detail"][0].get("msg", err)
                    else:
                        err = err_json.get("detail", err)
                except Exception:
                    pass
            flash(err, "danger")
            
    profile = existing_profile
    return render_template("auth/profile.html", profile=profile)

@app.route("/reports/export")
@login_required
def reports_export():
    fmt = request.args.get("format", "xlsx")
    start = request.args.get("start_date")
    end = request.args.get("end_date")
    inst = request.args.get("institution_id")
    
    params = {"format": fmt}
    if start:
        params["start_date"] = start
    if end:
        params["end_date"] = end
    if inst:
        params["institution_id"] = inst
        
    token = session.get("access_token")
    res = api_request("GET", "/reports/export", token=token, params=params)
    if res and res.status_code == 200:
        content_type = res.headers.get("Content-Type", "application/octet-stream")
        cd = res.headers.get("Content-Disposition", "")
        return Response(
            res.content,
            mimetype=content_type,
            headers={"Content-Disposition": cd}
        )
    flash("Report export failed.", "danger")
    return redirect(url_for("reports"))

@app.route("/network/data")
@login_required
def network_data():
    token = session.get("access_token")
    res = api_request("GET", "/network/graph", token=token)
    if res and res.status_code == 200:
        return res.json()
    return {"nodes": [], "edges": []}

@app.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "")
    token = session.get("access_token")
    if not q:
        return {"query": "", "total_results": 0, "results": {}}
    res = api_request("GET", f"/search?q={q}", token=token)
    if res and res.status_code == 200:
        return res.json()
    return {"query": q, "total_results": 0, "results": {}}

@app.route("/api/notifications/unread-count")
@login_required
def api_notifications_count():
    token = session.get("access_token")
    res = api_request("GET", "/notifications/unread-count", token=token)
    if res and res.status_code == 200:
        return res.json()
    return {"unread_count": 0}

@app.route("/api/notifications/mark-read", methods=["POST"])
@login_required
def api_notifications_mark_read():
    token = session.get("access_token")
    res = api_request("POST", "/notifications/mark-read", token=token)
    if res and res.status_code == 200:
        return res.json()
    return {"message": "Done"}

@app.route("/users")
@login_required
def users_page():
    role = session.get("user_role")
    if role != "system_admin":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))
    token = session.get("access_token")
    res = api_request("GET", "/users/", token=token)
    users = res.json() if res and res.status_code == 200 else []
    return render_template("users.html", users=users)

@app.route("/institutions", methods=["GET", "POST"])
@login_required
def institutions_page():
    role = session.get("user_role")
    if role != "system_admin":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))
    token = session.get("access_token")
    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        inst_type = request.form.get("type")
        res = api_request("POST", "/institutions/", token=token, json={
            "name": name,
            "address": address,
            "type": inst_type
        })
        if res and res.status_code == 201:
            flash("Institution added successfully!", "success")
        else:
            flash("Failed to add institution.", "danger")
            
    res = api_request("GET", "/institutions/", token=token)
    institutions = res.json() if res and res.status_code == 200 else []
    return render_template("institutions.html", institutions=institutions)

@app.route("/departments", methods=["GET", "POST"])
@login_required
def departments_page():
    role = session.get("user_role")
    if role not in ["system_admin", "institution_admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))
    token = session.get("access_token")
    if request.method == "POST":
        name = request.form.get("name")
        inst_id = request.form.get("institution_id")
        res = api_request("POST", "/departments/", token=token, json={
            "name": name,
            "institution_id": int(inst_id) if inst_id else 1
        })
        if res and res.status_code == 201:
            flash("Department added successfully!", "success")
        else:
            flash("Failed to add department.", "danger")
            
    res = api_request("GET", "/departments/", token=token)
    departments = res.json() if res and res.status_code == 200 else []
    res_inst = api_request("GET", "/institutions/", token=token)
    institutions = res_inst.json() if res_inst and res_inst.status_code == 200 else []
    return render_template("departments.html", departments=departments, institutions=institutions)

@app.route("/assigned-reviews")
@login_required
def assigned_reviews_page():
    role = session.get("user_role")
    if role != "reviewer":
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))
    token = session.get("access_token")
    res = api_request("GET", "/publications/", token=token)
    pubs = res.json() if res and res.status_code == 200 else []
    review_pubs = [p for p in pubs if p.get("status") in ["submitted", "pending_review", "pending"]]
    
    res_researchers = api_request("GET", "/researchers/", token=token)
    researchers_data = res_researchers.json() if res_researchers and res_researchers.status_code == 200 else []
    return render_template("publications.html", publications=review_pubs, researchers=researchers_data, reviewer_view=True)

@app.route("/api/researchers/<int:id>/stats")
@login_required
def api_researcher_stats(id):
    token = session.get("access_token")
    res = api_request("GET", f"/dashboards/researcher/{id}", token=token)
    if res and res.status_code == 200:
        return res.json()
    return {"publications": [], "collaborators": [], "projects": []}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
