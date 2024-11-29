import streamlit as st
from supabase import create_client
import datetime

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

# Fonction : Soumettre une non-conformité
def submit_non_conformity(user_id, objet, type, description, photos):
    """Soumettre une non-conformité."""
    photo_urls = []
    for photo in photos:
        file_path = f"photos/{photo.name}"
        response = supabase.storage.from_("photos").upload(file_path, photo)
        if response.error:
            st.error(f"Erreur lors du téléversement de la photo : {response.error}")
            return
        public_url = supabase.storage.from_("photos").get_public_url(file_path).data["publicUrl"]
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
        st.error(f"Erreur lors de la soumission : {response.error}")
    else:
        st.success("Non-conformité soumise avec succès !")

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
    response = supabase.table("actions_correctives").insert(data).execute()
    if response.error:
        st.error(f"Erreur lors de l'ajout de l'action corrective : {response.error}")
    else:
        st.success("Action corrective ajoutée avec succès !")

# Interface utilisateur Streamlit
st.title("Système de Gestion des Non-Conformités")

# Vérification de la connexion
if st.session_state.user is None:
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
            st.experimental_set_query_params(logged_in="true")
            # Redessiner la page
            st.experimental_rerun()
else:
    # Continuer si l'utilisateur est connecté
    user = st.session_state.user
    is_admin = user["role"] == "admin"

    # Soumettre une non-conformité
    st.header("Soumettre une Non-Conformité")
    objet = st.text_input("Objet")
    type = st.selectbox("Type", ["Qualité", "Sécurité", "Environnement"])
    description = st.text_area("Description")
    photos = st.file_uploader("Photos", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

    if st.button("Soumettre Non-Conformité"):
        submit_non_conformity(user_id=user["id"], objet=objet, type=type, description=description, photos=photos)

    # Afficher les non-conformités
    st.header("Tableau de Bord des Non-Conformités")
    filters = {"user_id": user["id"]} if not is_admin else {}
    response = supabase.table("non_conformites").select("*").filter(filters).execute()
    non_conformities = response.data

    if non_conformities:
        for nc in non_conformities:
            st.subheader(nc["objet"])
            st.write(f"Type : {nc['type']}")
            st.write(f"Description : {nc['description']}")
            st.write(f"Statut : {nc['status']}")
            for photo in nc["photos"]:
                st.image(photo, use_column_width=True)

            # Actions correctives associées
            corrective_actions = supabase.table("actions_correctives").select("*").eq("non_conformite_id", nc["id"]).execute().data
            if corrective_actions:
                st.write("Actions Correctives :")
                for action in corrective_actions:
                    st.write(f"- {action['action']} (Responsable : {action['responsable']}, Échéance : {action['delai']})")

            # Ajouter une action corrective (pour les administrateurs)
            if is_admin:
                st.subheader("Ajouter une Action Corrective")
                action = st.text_input(f"Action pour {nc['objet']}")
                delai = st.date_input(f"Échéance pour {nc['objet']}")
                responsable = st.text_input(f"Responsable pour {nc['objet']}")
                if st.button(f"Ajouter Action Corrective pour {nc['id']}"):
                    add_corrective_action(nc["id"], action, delai, responsable)
