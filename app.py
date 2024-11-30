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

# Fonction : Nettoyer les noms de fichiers
def sanitize_filename(filename):
    """Nettoyer le nom du fichier pour éviter les erreurs de téléversement."""
    filename = filename.replace(" ", "_")  # Remplacer les espaces par des underscores
    filename = re.sub(r"[^\w\.-]", "", filename)  # Supprimer les caractères non autorisés
    return filename

# Fonction : Soumettre une non-conformité
def submit_non_conformity(user_id, objet, type, description, photos):
    """Soumettre une non-conformité avec gestion des photos."""
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
        "created_at": datetime.datetime.now().isoformat(),
    }
    try:
        supabase.table("non_conformites").insert(data).execute()
        st.success("Non-conformité soumise avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'insertion dans la base de données : {e}")

# CSS pour styliser les tableaux
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
            text-align: left;
            padding: 8px;
            vertical-align: top;
        }
        .styled-table th {
            background-color: #f4f4f4;
            font-weight: bold;
        }
        .styled-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .styled-table tr:hover {
            background-color: #f1f1f1;
        }
        .thumbnail {
            width: 80px;
            cursor: pointer;
        }
        .action-buttons button {
            background-color: #007BFF;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 5px;
        }
        .action-buttons button:hover {
            background-color: #0056b3;
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

    # Onglets
    tabs = st.tabs(["Accueil", "Soumettre une Non-Conformité", "Tableau de Bord", "Profil"])

    with tabs[0]:
        st.header("Bienvenue dans le Système de Gestion des Non-Conformités")
        st.write("Utilisez les onglets pour naviguer dans l'application.")

    with tabs[1]:
        st.header("📋 Soumettre une Non-Conformité")
        with st.form("non_conformity_form"):
            objet = st.text_input("Objet")
            type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
            description = st.text_area("Description")
            photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
            submit_button = st.form_submit_button("Soumettre")
            reset_button = st.form_submit_button("Réinitialiser")

            if submit_button:
                if not objet or not type or not description:
                    st.error("Veuillez remplir tous les champs obligatoires.")
                else:
                    submit_non_conformity(user_id=user["id"], objet=objet, type=type, description=description, photos=photos)

            if reset_button:
                st.session_state.form_submitted = False

    with tabs[2]:
        st.header("📊 Tableau de Bord des Non-Conformités")
        non_conformities = load_non_conformities(user_id=user["id"], is_admin=is_admin)

        if non_conformities:
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
                photo_html = ""
                if "photos" in nc and nc["photos"]:
                    for photo_url in nc["photos"]:
                        photo_html += f"<img src='{photo_url}' class='thumbnail' onclick='window.open(\"{photo_url}\", \"_blank\")'>"

                st.markdown(
                    f"""
                    <tr>
                        <td>{nc['objet']}</td>
                        <td>{nc['description']}</td>
                        <td>{nc['type']}</td>
                        <td>{nc['status']}</td>
                        <td>{photo_html}</td>
                        <td class="action-buttons">
                            <button onclick='alert("Édition de la non-conformité {nc['id']}")'>✏️ Éditer</button>
                            <button onclick='alert("Ajout d'action corrective pour {nc['id']}")'>➕ Action</button>
                        </td>
                    </tr>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</table>", unsafe_allow_html=True)
        else:
            st.info("Aucune non-conformité trouvée.")

    with tabs[3]:
        st.header("Profil Utilisateur")
        st.write(f"**Email**: {user['email']}")
        st.write(f"**Rôle**: {user['role']}")
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.experimental_rerun()

