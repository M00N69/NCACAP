import streamlit as st
from supabase import create_client, Client
import datetime

# Initialiser Supabase
supabase_url = st.secrets["SUPABASE_URL"]
supabase_anon_key = st.secrets["SUPABASE_ANON_KEY"]
supabase: Client = create_client(supabase_url, supabase_anon_key)

# Initialisation de l'état de session
if "user" not in st.session_state:
    st.session_state.user = None

# Fonctions utilitaires
def handle_error(response):
    """Gestion centralisée des erreurs."""
    if response.error:
        st.error(f"Erreur : {response.error.get('message', 'Erreur inconnue')}")
        return None
    return response.data

def fetch_user_details(user_id):
    """Récupérer les détails de l'utilisateur depuis la table 'users'."""
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()
    return handle_error(response)

def upload_photos(photos):
    """Télécharger des photos dans le bucket Supabase Storage."""
    photo_urls = []
    for photo in photos:
        file_path = f"photos/{photo.name}"
        upload_response = supabase.storage.from_('photos').upload(file_path, photo)
        if upload_response.error:
            st.error(f"Échec du téléchargement de la photo : {upload_response.error.get('message', 'Erreur inconnue')}")
            continue
        url_response = supabase.storage.from_('photos').get_public_url(file_path)
        if url_response.error:
            st.error(f"Échec de récupération de l'URL de la photo : {url_response.error.get('message', 'Erreur inconnue')}")
            continue
        photo_urls.append(url_response.data.get("publicUrl"))
    return photo_urls

def fetch_table(table, filters=None):
    """Récupérer les données d'une table avec des filtres optionnels."""
    query = supabase.table(table).select("*")
    if filters:
        for column, value in filters.items():
            query = query.eq(column, value)
    return handle_error(query.execute())

# Authentification
def authenticate_user(email, password):
    """Authentifier un utilisateur et retourner ses données."""
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    user = handle_error(response)
    if user:
        user_details = fetch_user_details(user["user"]["id"])
        if user_details:
            return user_details
    return None

# Soumettre une non-conformité
def submit_non_conformity(user_id, objet, type, description, photos):
    """Soumettre une non-conformité."""
    if not all([objet, type, description]):
        st.error("Tous les champs sont obligatoires !")
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
        st.error(f"Échec de la soumission de la non-conformité : {response.error.get('message', 'Erreur inconnue')}")
    else:
        st.success("Non-conformité soumise avec succès !")

# Ajouter une action corrective
def add_corrective_action(non_conformite_id, action, delai, responsable_id):
    """Ajouter une action corrective pour une non-conformité."""
    if not action or not delai or not responsable_id:
        st.error("Tous les champs sont obligatoires !")
        return
    delai_iso = datetime.datetime.combine(delai, datetime.datetime.min.time()).isoformat()
    data = {
        "non_conformite_id": non_conformite_id,
        "action": action,
        "delai": delai_iso,
        "responsable": responsable_id,
        "created_at": datetime.datetime.now().isoformat()
    }
    response = supabase.table('actions_correctives').insert(data).execute()
    if response.error:
        st.error(f"Échec de l'ajout de l'action corrective : {response.error.get('message', 'Erreur inconnue')}")
    else:
        st.success("Action corrective ajoutée avec succès !")

# Interface utilisateur
st.title("Système de Gestion des Non-Conformités")

# Authentification via la barre latérale
st.sidebar.title("Connexion")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Mot de passe", type="password")
if st.sidebar.button("Connexion"):
    user = authenticate_user(email, password)
    if user:
        st.session_state.user = user
        st.sidebar.success(f"Connecté en tant que {user['email']}")

# Vérification de l'authentification
if not st.session_state.user:
    st.stop()

# Gestion des rôles
user = st.session_state.user
is_admin = user["role"] == "admin"

# Formulaire de soumission de non-conformité
st.header("Soumettre une Non-Conformité")
objet = st.text_input("Objet")
type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
description = st.text_area("Description")
photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

if st.button("Soumettre"):
    submit_non_conformity(
        user_id=user["id"],
        objet=objet,
        type=type,
        description=description,
        photos=photos
    )

# Tableau de bord des non-conformités
st.header("Tableau de Bord des Non-Conformités")
filters = {"user_id": user["id"]} if not is_admin else None
non_conformities = fetch_table('non_conformites', filters)
if non_conformities:
    for nc in non_conformities:
        st.subheader(nc["objet"])
        st.write(nc["description"])
        st.write(f"Type : {nc['type']}")
        st.write(f"Statut : {nc['status']}")
        if is_admin:
            st.write(f"Soumis par l'utilisateur ID : {nc['user_id']}")
        if nc["photos"]:
            for photo in nc["photos"]:
                st.image(photo, use_column_width=True)

        # Affichage des actions correctives
        corrective_actions = fetch_table("actions_correctives", {"non_conformite_id": nc["id"]})
        if corrective_actions:
            st.subheader("Actions Correctives")
            for action in corrective_actions:
                st.write(f"Action : {action['action']}")
                st.write(f"Échéance : {action['delai']}")
                st.write(f"Responsable : {action['responsable']}")
        else:
            st.write("Aucune action corrective pour l'instant.")

# Ajout d'actions correctives (administrateurs uniquement)
if is_admin:
    st.header("Ajouter une Action Corrective")
    selected_nc = st.selectbox(
        "Sélectionnez une Non-Conformité",
        non_conformities,
        format_func=lambda nc: nc["objet"]
    )
    if selected_nc:
        action = st.text_input("Action")
        delai = st.date_input("Échéance")
        responsables = fetch_table('users')
        responsable = st.selectbox("Responsable", responsables, format_func=lambda user: user['email'])
        if st.button("Ajouter une Action"):
            add_corrective_action(
                non_conformite_id=selected_nc["id"],
                action=action,
                delai=delai,
                responsable_id=responsable["id"]
            )

