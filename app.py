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
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^\w\.-]", "", filename)
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
            return

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

# Fonction : Ajouter une action corrective
def add_corrective_action(non_conformite_id, action, delai, responsable):
    """Ajouter une action corrective pour une non-conformité."""
    data = {
        "non_conformite_id": non_conformite_id,
        "action": action,
        "delai": delai.isoformat(),
        "responsable": responsable,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    try:
        supabase.table("actions_correctives").insert(data).execute()
        st.success("Action corrective ajoutée avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'ajout de l'action corrective : {e}")

# Interface utilisateur Streamlit
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

    # Soumission de non-conformité
    st.header("📋 Soumettre une Non-Conformité")
    with st.form("non_conformity_form"):
        objet = st.text_input("Objet")
        type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
        description = st.text_area("Description")
        photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
        submit_button = st.form_submit_button("Soumettre")

        if submit_button:
            if not objet or not type or not description:
                st.error("Veuillez remplir tous les champs obligatoires.")
            else:
                submit_non_conformity(user_id=user["id"], objet=objet, type=type, description=description, photos=photos)

    # Affichage des non-conformités
    st.header("📊 Tableau de Bord des Non-Conformités")
    response = supabase.table("non_conformities").select("*").execute()
    non_conformities = response.data

    if non_conformities:
        for nc in non_conformities:
            with st.expander(nc["objet"]):
                st.write(f"**Type**: {nc['type']}")
                st.write(f"**Description**: {nc['description']}")
                st.write(f"**Statut**: {nc['status']}")
                if nc["photos"]:
                    st.write("**Photos**:")
                    for photo_url in nc["photos"]:
                        st.image(photo_url, use_column_width=True)

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
    else:
        st.info("Aucune non-conformité trouvée.")
