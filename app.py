import streamlit as st
from supabase import create_client
import datetime
import uuid
import re

# Initialisation de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialisation de l'état de session
if "user" not in st.session_state:
    st.session_state.user = None
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# Fonction : Authentifier un utilisateur
def authenticate_user(email, password):
    try:
        response = supabase.table("users").select("*").eq("email", email).eq("password", password).single().execute()
        if response and response.data:
            return response.data
        else:
            st.error("Email ou mot de passe incorrect.")
    except Exception as e:
        st.error(f"Erreur lors de l'authentification : {e}")
    return None

# Fonction : Nettoyer les noms de fichiers
def sanitize_filename(filename):
    filename = filename.replace(" ", "_")
    return re.sub(r"[^\w\.-]", "", filename)

# Fonction : Soumettre une non-conformité
def submit_non_conformity(user_id, objet, type, description, photos):
    photo_urls = []
    for photo in photos:
        sanitized_name = sanitize_filename(photo.name)
        unique_name = f"{uuid.uuid4()}_{sanitized_name}"
        file_path = f"photos/{unique_name}"
        try:
            supabase.storage.from_("photos").upload(file_path, photo.read())
            public_url = supabase.storage.from_("photos").get_public_url(file_path)
            if public_url:
                photo_urls.append(public_url)
            else:
                st.error(f"Erreur : Impossible de générer l'URL pour {photo.name}")
        except Exception as e:
            st.error(f"Erreur lors du téléversement de {photo.name} : {e}")
            return

    try:
        supabase.table("non_conformites").insert({
            "user_id": user_id,
            "objet": objet,
            "type": type,
            "description": description,
            "photos": photo_urls,
            "status": "open",
            "created_at": datetime.datetime.now().isoformat(),
        }).execute()
        st.success("Non-conformité soumise avec succès !")
        st.session_state.form_submitted = True
    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement : {e}")

# Fonction : Ajouter une action corrective
def add_corrective_action(non_conformite_id, action, delai, responsable):
    try:
        supabase.table("actions_correctives").insert({
            "non_conformite_id": non_conformite_id,
            "action": action,
            "delai": delai.isoformat(),
            "responsable": responsable,
            "created_at": datetime.datetime.now().isoformat(),
        }).execute()
        st.success("Action corrective ajoutée avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'ajout de l'action corrective : {e}")

# Interface utilisateur Streamlit
st.set_page_config(layout="wide")
st.title("🛠️ Système de Gestion des Non-Conformités")

# Connexion
if st.session_state.user is None:
    st.sidebar.title("Connexion")
    with st.sidebar.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter"):
            user = authenticate_user(email, password)
            if user:
                st.session_state.user = user
                st.sidebar.success(f"Connecté en tant que {user['email']}")
else:
    user = st.session_state.user
    is_admin = user.get("role") == "admin"

    # Onglets
    tabs = st.tabs(["Accueil", "Soumettre une Non-Conformité", "Tableau de Bord", "Profil"])

    with tabs[0]:
        st.header("Bienvenue")
        st.write("Utilisez les onglets pour naviguer dans l'application.")

    with tabs[1]:
        st.header("📋 Soumettre une Non-Conformité")
        with st.form("non_conformity_form"):
            objet = st.text_input("Objet")
            type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
            description = st.text_area("Description")
            photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
            if st.form_submit_button("Soumettre"):
                if objet and type and description:
                    submit_non_conformity(user_id=user["id"], objet=objet, type=type, description=description, photos=photos)
                else:
                    st.error("Veuillez remplir tous les champs obligatoires.")
        if st.session_state.form_submitted:
            st.session_state.form_submitted = False
            st.experimental_rerun()

    with tabs[2]:
        st.header("📊 Tableau de Bord")
        try:
            response = supabase.table("non_conformites").select("*").execute()
            if response and response.data:
                for nc in response.data:
                    with st.expander(nc["objet"]):
                        st.write(f"**Type**: {nc['type']}")
                        st.write(f"**Description**: {nc['description']}")
                        st.write(f"**Statut**: {nc['status']}")
                        if nc["photos"]:
                            for photo in nc["photos"]:
                                st.image(photo, caption="Photo", width=100)
        except Exception as e:
            st.error(f"Erreur lors du chargement : {e}")

    with tabs[3]:
        st.header("Profil Utilisateur")
        st.write(f"**Email**: {user['email']}")
        st.write(f"**Rôle**: {user['role']}")
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.experimental_rerun()
