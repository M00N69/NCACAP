import streamlit as st
from supabase import create_client, Client
import datetime
import uuid
import re

# Initialisation de Streamlit
st.set_page_config(layout="wide", page_title="Gestion des Non-Conformités", page_icon="🛠️")

# Initialisation de Supabase
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except KeyError:
    st.error("Les clés Supabase ne sont pas configurées dans les secrets Streamlit.")
    st.stop()

# Initialisation de l'état de session
if "user" not in st.session_state:
    st.session_state.user = None


# Fonction : Authentifier un utilisateur
def authenticate_user(email, password):
    try:
        response = supabase.table("users").select("*").eq("email", email).eq("password", password).single().execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur lors de l'authentification : {e}")
        return None


# Fonction : Charger les non-conformités
def load_non_conformities(user_id=None, is_admin=False):
    try:
        query = supabase.table("non_conformities").select("*")
        if not is_admin:
            query = query.eq("user_id", user_id)
        response = query.execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erreur lors du chargement des non-conformités : {e}")
        return []


# Fonction : Charger les actions correctives
def load_corrective_actions(non_conformite_id):
    try:
        response = supabase.table("actions_correctives").select("*").eq("non_conformite_id", non_conformite_id).execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erreur lors du chargement des actions correctives : {e}")
        return []


# Fonction : Ajouter une action corrective
def add_corrective_action(non_conformite_id, action, delai, responsable):
    try:
        supabase.table("actions_correctives").insert({
            "non_conformite_id": non_conformite_id,
            "action": action,
            "delai": delai.isoformat(),
            "responsable": responsable,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }).execute()
        st.success("Action corrective ajoutée avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'ajout de l'action corrective : {e}")


# Fonction : Nettoyer les noms de fichiers
def sanitize_filename(filename):
    """Nettoyer le nom du fichier pour éviter les erreurs de téléversement."""
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^\w\.-]", "", filename)
    return filename


# Fonction : Soumettre une non-conformité
def submit_non_conformity(user_id, objet, type, description, photos):
    photo_urls = []
    for photo in photos:
        sanitized_name = sanitize_filename(photo.name)
        unique_name = f"{uuid.uuid4()}_{sanitized_name}"
        file_path = f"photos/{unique_name}"
        file_data = photo.read()
        try:
            supabase.storage.from_("photos").upload(file_path, file_data)
            public_url = supabase.storage.from_("photos").get_public_url(file_path)
            if public_url:
                photo_urls.append(public_url)
            else:
                st.error(f"Erreur : Impossible de générer l'URL publique pour {photo.name}")
        except Exception as e:
            st.error(f"Erreur inattendue lors du téléversement de {photo.name} : {e}")

    data = {
        "user_id": user_id,
        "objet": objet,
        "type": type,
        "description": description,
        "photos": photo_urls,
        "status": "open",
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    try:
        supabase.table("non_conformities").insert(data).execute()
        st.success("Non-conformité soumise avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'insertion dans la base de données : {e}")


# CSS pour styliser les tableaux et les boutons
def inject_custom_css():
    st.markdown(
        """
        <style>
        body { font-family: Arial, sans-serif; }
        .styled-table { width: 100%; border-collapse: collapse; }
        .styled-table th, .styled-table td { border: 1px solid #ddd; text-align: left; padding: 8px; vertical-align: top; }
        .styled-table th { background-color: #f4f4f4; font-weight: bold; }
        .styled-table tr:nth-child(even) { background-color: #f9f9f9; }
        .styled-table tr:hover { background-color: #f1f1f1; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_custom_css()

# Interface utilisateur Streamlit
st.title("🛠️ Gestion des Non-Conformités")

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
                st.sidebar.error("Échec de la connexion. Vérifiez vos identifiants.")
else:
    user = st.session_state.user
    is_admin = user.get("role") == "admin"

    # Onglets
    tabs = ["Accueil", "Soumettre une Non-Conformité", "Tableau de Bord", "Profil"]
    active_tab = st.sidebar.selectbox("Navigation", tabs)

    if active_tab == "Accueil":
        st.header("Bienvenue")
        st.write("Utilisez les onglets pour naviguer.")

    elif active_tab == "Soumettre une Non-Conformité":
        st.header("📋 Soumettre une Non-Conformité")
        with st.form("non_conformity_form"):
            objet = st.text_input("Objet")
            type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
            description = st.text_area("Description")
            photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
            if st.form_submit_button("Soumettre"):
                if not objet or not description:
                    st.error("Veuillez remplir tous les champs obligatoires.")
                else:
                    submit_non_conformity(user["id"], objet, type, description, photos)

    elif active_tab == "Tableau de Bord":
        st.header("📊 Tableau de Bord")
        non_conformities = load_non_conformities(user_id=user["id"], is_admin=is_admin)
        if non_conformities:
            for nc in non_conformities:
                st.write(nc)
        else:
            st.info("Aucune non-conformité trouvée.")

    elif active_tab == "Profil":
        st.header("Profil")
        st.write(f"**Email**: {user['email']}")
        st.write(f"**Rôle**: {user['role']}")
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.experimental_rerun()
