import streamlit as st
from supabase import create_client
import datetime
import uuid
import re

# Initialisation de Streamlit
st.set_page_config(layout="wide", page_title="Gestion des Non-Conformités", page_icon="🛠️")

# Initialisation de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialisation de l'état de session
if "user" not in st.session_state:
    st.session_state.user = None

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

# Fonction : Charger les non-conformités
def load_non_conformities(user_id=None, is_admin=False):
    try:
        if is_admin:
            response = supabase.table("non_conformites").select("*").execute()
        else:
            response = supabase.table("non_conformites").select("*").eq("user_id", user_id).execute()

        return response.data if response and response.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des non-conformités : {e}")
        return []

# Fonction : Charger les actions correctives
def load_corrective_actions(non_conformite_id):
    try:
        response = supabase.table("actions_correctives").select("*").eq("non_conformite_id", non_conformite_id).execute()
        return response.data if response and response.data else []
    except Exception as e:
        st.error(f"Erreur lors du chargement des actions correctives : {e}")
        return []

# Fonction : Soumettre une mise à jour
def update_non_conformity(non_conformity_id, updated_data):
    try:
        supabase.table("non_conformites").update(updated_data).eq("id", non_conformity_id).execute()
        st.success("Non-conformité mise à jour avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour : {e}")

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

# CSS pour styliser les tableaux et miniatures
def inject_custom_css():
    st.markdown(
        """
        <style>
        body {
            font-family: Arial, sans-serif;
        }
        .styled-table {
            width: 100%;
            border-collapse: collapse;
        }
        .styled-table th, .styled-table td {
            border: 1px solid #ddd;
            padding: 8px;
        }
        .styled-table th {
            background-color: #f4f4f4;
            text-align: left;
        }
        .styled-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .styled-table tr:hover {
            background-color: #f1f1f1;
        }
        .thumbnail {
            width: 60px;
            cursor: pointer;
        }
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
    user = st.session_state.user
    is_admin = user.get("role") == "admin"

    # Chargement des non-conformités
    non_conformities = load_non_conformities(user_id=user["id"], is_admin=is_admin)

    # Affichage des non-conformités
    st.header("📊 Tableau des Non-Conformités")
    st.markdown("<table class='styled-table'>", unsafe_allow_html=True)
    st.markdown(
        """
        <tr>
            <th>Objet</th>
            <th>Description</th>
            <th>Type</th>
            <th>Statut</th>
            <th>Photos</th>
            <th>Actions</th>
        </tr>
        """,
        unsafe_allow_html=True,
    )
    for nc in non_conformities:
        st.markdown("<tr>", unsafe_allow_html=True)
        st.markdown(f"<td>{nc['objet']}</td>", unsafe_allow_html=True)
        st.markdown(f"<td>{nc['description']}</td>", unsafe_allow_html=True)
        st.markdown(f"<td>{nc['type']}</td>", unsafe_allow_html=True)
        st.markdown(f"<td>{nc['status']}</td>", unsafe_allow_html=True)

        # Miniatures cliquables
        photo_html = ""
        if "photos" in nc and nc["photos"]:
            for photo_url in nc["photos"]:
                photo_html += f"<img src='{photo_url}' class='thumbnail' onclick='window.open(\"{photo_url}\", \"_blank\")'>"
        st.markdown(f"<td>{photo_html}</td>", unsafe_allow_html=True)

        # Boutons d'édition
        action_buttons = f"""
        <td>
            <button onclick='alert("Édition non-conformité {nc['id']}")'>✏️ Éditer</button>
            <button onclick='alert("Ajout action corrective {nc['id']}")'>➕ Action</button>
        </td>
        """
        st.markdown(action_buttons, unsafe_allow_html=True)
        st.markdown("</tr>", unsafe_allow_html=True)
    st.markdown("</table>", unsafe_allow_html=True)

    if st.button("Déconnexion"):
        st.session_state.user = None
        st.experimental_rerun()
