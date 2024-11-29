import streamlit as st
from supabase import create_client, Client
import datetime

# Initialisation de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialisation de l'état de session
if "user" not in st.session_state:
    st.session_state.user = None

# Fonction d'authentification
def authenticate_user(email, password):
    """Authentifier un utilisateur avec Supabase."""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = response.user
        user_details = supabase.table("users").select("*").eq("auth_user_id", user["id"]).single().execute()
        return user_details.data
    except Exception as e:
        st.error("Email ou mot de passe invalide.")
        return None

# Soumettre une non-conformité
def submit_non_conformity(user_id, objet, type, description, photos):
    """Soumettre une non-conformité."""
    photo_urls = []
    for photo in photos:
        file_path = f"photos/{photo.name}"
        supabase.storage.from_('photos').upload(file_path, photo)
        public_url = supabase.storage.from_('photos').get_public_url(file_path).data
        photo_urls.append(public_url)

    data = {
        "user_id": user_id,
        "objet": objet,
        "type": type,
        "description": description,
        "photos": photo_urls,
        "status": "open",
        "created_at": datetime.datetime.now().isoformat(),
    }
    response = supabase.table("non_conformites").insert(data).execute()
    if response.error:
        st.error("Erreur lors de la soumission de la non-conformité.")
    else:
        st.success("Non-conformité soumise avec succès !")

# Interface utilisateur
st.title("Système de Gestion des Non-Conformités")

# Connexion
st.sidebar.title("Connexion")
with st.sidebar.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    login_button = st.form_submit_button("Connexion")

if login_button:
    user = authenticate_user(email, password)
    if user:
        st.session_state.user = user
        st.sidebar.success(f"Connecté en tant que {user['email']}")
        st.experimental_rerun()

# Vérification de l'authentification
if not st.session_state.user:
    st.stop()

user = st.session_state.user
is_admin = user["role"] == "admin"

# Soumettre une non-conformité
st.header("Soumettre une Non-Conformité")
objet = st.text_input("Objet")
type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
description = st.text_area("Description")
photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

if st.button("Soumettre"):
    submit_non_conformity(user_id=user["auth_user_id"], objet=objet, type=type, description=description, photos=photos)

# Afficher les non-conformités
st.header("Tableau de Bord des Non-Conformités")
non_conformities = supabase.table("non_conformites").select("*").eq("user_id", user["auth_user_id"]).execute().data
if non_conformities:
    for nc in non_conformities:
        st.subheader(nc["objet"])
        st.write(f"Type : {nc['type']}")
        st.write(f"Description : {nc['description']}")
        st.write(f"Statut : {nc['status']}")
        for photo in nc["photos"]:
            st.image(photo, use_column_width=True)

# Ajouter des actions correctives (administrateurs uniquement)
if is_admin:
    st.header("Ajouter une Action Corrective")
    nc_id = st.selectbox("Non-Conformité", non_conformities, format_func=lambda x: x["objet"])
    action = st.text_input("Action")
    delai = st.date_input("Échéance")
    responsable = st.text_input("Responsable")
    if st.button("Ajouter Action Corrective"):
        supabase.table("actions_correctives").insert({
            "non_conformite_id": nc_id["id"],
            "action": action,
            "delai": delai.isoformat(),
            "responsable": responsable,
        }).execute()
        st.success("Action corrective ajoutée.")
