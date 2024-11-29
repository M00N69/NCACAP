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
    """Vérifier les identifiants dans la table `users`."""
    try:
        response = supabase.table("users").select("*").eq("email", email).eq("password", password).single().execute()
        user = response.data
        if user:
            return user
        else:
            st.error("Email ou mot de passe incorrect.")
            return None
    except Exception as e:
        st.error(f"Erreur lors de l'authentification : {e}")
        return None

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
        # Nettoyer le nom du fichier
        sanitized_name = sanitize_filename(photo.name)
        # Générer un chemin unique
        unique_name = f"{uuid.uuid4()}_{sanitized_name}"
        file_path = f"photos/{unique_name}"
        file_data = photo.read()  # Lire le fichier en binaire

        try:
            # Téléversement vers Supabase Storage
            supabase.storage.from_("photos").upload(file_path, file_data)
            # Récupérer l'URL publique du fichier
            public_url = supabase.storage.from_("photos").get_public_url(file_path)
            if public_url:
                photo_urls.append(public_url)
            else:
                st.error(f"Erreur : Impossible de générer l'URL publique pour {photo.name}")
        except Exception as e:
            st.error(f"Erreur inattendue lors du téléversement de {photo.name} : {e}")
            return

    # Enregistrement dans la table `non_conformites`
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
        response = supabase.table("non_conformites").insert(data).execute()
        st.success("Non-conformité soumise avec succès !")
        st.session_state.form_submitted = True  # Indicateur de formulaire soumis
    except Exception as e:
        st.error(f"Erreur lors de l'insertion dans la base de données : {e}")

# Fonction : Ajouter une action corrective
def add_corrective_action(non_conformite_id, action, delai, responsable):
    """Ajouter une action corrective pour une non-conformité."""
    data = {
        "non_conformite_id": non_conformite_id,
        "action": action,
        "delai": delai.isoformat(),
        "responsable": responsable,
        "created_at": datetime.datetime.now().isoformat(),
    }
    try:
        response = supabase.table("actions_correctives").insert(data).execute()
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
        login_button = st.form_submit_button("Se connecter")

    if login_button:
        user = authenticate_user(email, password)
        if user:
            st.session_state.user = user
            st.sidebar.success(f"Connecté en tant que {user['email']}")
else:
    user = st.session_state.user
    is_admin = user["role"] == "admin"

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

            if reset_button or st.session_state.form_submitted:
                st.session_state.form_submitted = False  # Réinitialiser l'indicateur de formulaire soumis
                st.experimental_rerun()  # Réexécuter l'application pour réinitialiser le formulaire

    with tabs[2]:
        st.header("📊 Tableau de Bord des Non-Conformités")
        filters = {"user_id": user["id"]} if not is_admin else {}
        response = supabase.table("non_conformites").select("*").execute()
        non_conformities = response.data

        if non_conformities:
            for nc in non_conformities:
                with st.expander(nc["objet"]):
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                    col1.write(f"**Type**: {nc['type']}")
                    col2.write(f"**Description**: {nc['description']}")
                    col3.write(f"**Statut**: {nc['status']}")
                    if nc["photos"]:
                        col4.write("**Photos**:")
                        for photo in nc["photos"]:
                            if col4.image(photo, caption=nc["objet"], width=50):
                                with st.expander("Voir la photo"):
                                    st.image(photo, caption=nc["objet"], use_column_width=True)
                    col5.button("Éditer", key=f"edit_{nc['id']}")
                    col5.button("Voir", key=f"view_{nc['id']}")

                    # Actions correctives associées
                    corrective_actions = supabase.table("actions_correctives").select("*").eq("non_conformite_id", nc["id"]).execute().data
                    if corrective_actions:
                        st.write("**Actions Correctives**:")
                        for action in corrective_actions:
                            st.write(f"- {action['action']} (Responsable: {action['responsable']}, Échéance: {action['delai']})")

                    # Ajout d'action corrective (administrateurs uniquement)
                    if is_admin:
                        st.subheader("Ajouter une Action Corrective")
                        with st.form(f"corrective_form_{nc['id']}"):
                            action = st.text_input("Action")
                            delai = st.date_input("Échéance")
                            responsable = st.text_input("Responsable")
                            add_action_button = st.form_submit_button("Ajouter Action Corrective")
                            if add_action_button:
                                add_corrective_action(nc["id"], action, delai, responsable)

    with tabs[3]:
        st.header("Profil Utilisateur")
        st.write(f"**Email**: {user['email']}")
        st.write(f"**Rôle**: {user['role']}")
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.experimental_rerun()
