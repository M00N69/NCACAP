import streamlit as st
from supabase import create_client, Client
import datetime

# Initialize Supabase
supabase_url = st.secrets["SUPABASE_URL"]
supabase_anon_key = st.secrets["SUPABASE_ANON_KEY"]
supabase: Client = create_client(supabase_url, supabase_anon_key)

# Utility Functions
def handle_error(response):
    """Centralized error handling."""
    if response.error:
        st.error(f"Error: {response.error.message}")
        return None
    return response.data

def upload_photos(photos):
    """Upload photos to the Supabase storage bucket."""
    photo_urls = []
    for photo in photos:
        file_path = f"photos/{photo.name}"
        response = supabase.storage.from_('photos').upload(file_path, photo)
        if response.error:
            st.error(f"Photo upload failed: {response.error.message}")
            continue
        photo_url = supabase.storage.from_('photos').get_public_url(file_path).get("publicUrl")
        photo_urls.append(photo_url)
    return photo_urls

def fetch_table(table, filters=None):
    """Fetch data from a Supabase table with optional filters."""
    query = supabase.table(table).select("*")
    if filters:
        for column, value in filters.items():
            query = query.eq(column, value)
    return handle_error(query.execute())

# Authentication
def authenticate_user(email, password):
    """Authenticate a user and return user data."""
    response = supabase.auth.sign_in(email=email, password=password)
    return handle_error(response)

# Submit Non-Conformity
def submit_non_conformity(user_id, objet, type, description, photos):
    """Submit a non-conformity report."""
    if not all([objet, type, description]):
        st.error("All fields are mandatory!")
        return
    photo_urls = upload_photos(photos)
    data = {
        "user_id": user_id,
        "objet": objet,
        "type": type,
        "description": description,
        "photos": photo_urls,
        "status": "open",
        "created_at": datetime.datetime.now().isoformat()
    }
    response = supabase.table('non_conformites').insert(data).execute()
    if response.error:
        st.error(f"Failed to submit non-conformity: {response.error.message}")
    else:
        st.success("Non-conformity submitted successfully!")

# Add Corrective Action
def add_corrective_action(non_conformite_id, action, delai, responsable_id):
    """Add a corrective action for a non-conformity."""
    if not action or not delai or not responsable_id:
        st.error("All fields are mandatory!")
        return
    data = {
        "non_conformite_id": non_conformite_id,
        "action": action,
        "delai": delai.isoformat(),
        "responsable": responsable_id,
        "created_at": datetime.datetime.now().isoformat()
    }
    response = supabase.table('actions_correctives').insert(data).execute()
    if response.error:
        st.error(f"Failed to add corrective action: {response.error.message}")
    else:
        st.success("Corrective action added successfully!")

# User Interface
st.title("Non-Conformity Management System")

# Sidebar Authentication
st.sidebar.title("Login")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
if st.sidebar.button("Login"):
    user = authenticate_user(email, password)
    if user:
        st.sidebar.success(f"Logged in as {user['email']}")
        st.session_state.user = user

# Check Authentication
if 'user' not in st.session_state:
    st.stop()

# Role-based Access Control
user = st.session_state.user
is_admin = user["role"] == "admin"

# Non-Conformity Form
st.header("Submit a Non-Conformity")
objet = st.text_input("Subject")
type = st.selectbox("Type", ["Quality", "Safety", "Environment"])
description = st.text_area("Description")
photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

if st.button("Submit"):
    submit_non_conformity(
        user_id=user["id"],
        objet=objet,
        type=type,
        description=description,
        photos=photos
    )

# Display Non-Conformities
st.header("Non-Conformities Dashboard")
filters = {"user_id": user["id"]} if not is_admin else None
non_conformities = fetch_table('non_conformites', filters)
if non_conformities:
    for nc in non_conformities:
        st.subheader(nc["objet"])
        st.write(nc["description"])
        st.write(f"Type: {nc['type']}")
        st.write(f"Status: {nc['status']}")
        if is_admin:
            st.write(f"Submitted by User ID: {nc['user_id']}")
        if nc["photos"]:
            for photo in nc["photos"]:
                st.image(photo, use_column_width=True)

        # Display corrective actions
        corrective_actions = fetch_table("actions_correctives", {"non_conformite_id": nc["id"]})
        if corrective_actions:
            st.subheader("Corrective Actions")
            for action in corrective_actions:
                st.write(f"Action: {action['action']}")
                st.write(f"Deadline: {action['delai']}")
                st.write(f"Responsible User ID: {action['responsable']}")
        else:
            st.write("No corrective actions yet.")

# Corrective Actions (Admins Only)
if is_admin:
    st.header("Add Corrective Action")
    selected_nc = st.selectbox(
        "Select Non-Conformity", 
        non_conformities, 
        format_func=lambda nc: nc["objet"]
    )
    if selected_nc:
        action = st.text_input("Action")
        delai = st.date_input("Deadline")
        responsables = fetch_table('users')
        responsable = st.selectbox("Responsible", responsables, format_func=lambda user: user['email'])
        if st.button("Add Action"):
            add_corrective_action(
                non_conformite_id=selected_nc["id"],
                action=action,
                delai=delai,
                responsable_id=responsable["id"]
            )
