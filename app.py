import streamlit as st
from supabase import create_client
import datetime
import uuid
import re

# Configuration Streamlit
st.set_page_config(page_title="Gestion des Non-Conformités", layout="wide")

# Initialisation de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialisation de l'état de session
if "user" not in st.session_state:
    st.session_state.user = None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None

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
    """Soumettre une non-conformité avec gestion des photos."""
    photo_urls = []
    for photo in photos:
        sanitized_name = photo.name.replace(" ", "_")
        unique_name = f"{uuid.uuid4()}_{sanitized_name}"
        file_path = f"photos/{unique_name}"
        file_data = photo.read()
        try:
            supabase.storage.from_("photos").upload(file_path, file_data)
            public_url = supabase.storage.from_("photos").get_public_url(file_path)
            photo_urls.append(public_url)
        except Exception as e:
            st.error(f"Erreur lors du téléversement de {photo.name} : {e}")

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
        supabase.table("non_conformites").insert(data).execute()
        st.success("Non-conformité soumise avec succès !")
    except Exception as e:
        st.error(f"Erreur lors de l'insertion dans la base de données : {e}")

# Interface utilisateur Streamlit
st.title("🛠️ Système de Gestion des Non-Conformités")

if st.session_state.user is None:
    # Page de connexion
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

    # Navigation dans la barre latérale
    menu = st.sidebar.selectbox("Navigation", ["Fiche de Non-Conformité", "Tableau de Bord", "Profil"])

    if menu == "Fiche de Non-Conformité":
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

    elif menu == "Tableau de Bord":
        st.header("📊 Tableau de Bord des Non-Conformités")
        # Récupérer les non-conformités
        response = supabase.table("non_conformites").select("*").eq("user_id", user["id"]).execute() if not is_admin else supabase.table("non_conformites").select("*").execute()
        non_conformities = response.data

        if non_conformities:
            for nc in non_conformities:
                st.markdown("---")
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9;">
                        <h4 style="font-size: 20px;">{nc['objet']} ({nc['type']})</h4>
                        <p style="font-size: 16px;"><strong>Description :</strong> {nc['description']}</p>
                        <p style="font-size: 16px;"><strong>Statut :</strong> {nc['status']}</p>
                        <p style="font-size: 16px;"><strong>Créé le :</strong> {nc['created_at']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Miniatures des photos
                st.markdown("**Photos :**")
                for photo_url in nc["photos"]:
                    st.image(photo_url, caption="Cliquez pour agrandir", width=150, use_column_width=True)

                # Actions Correctives
                st.markdown("**Actions Correctives :**")
                actions = supabase.table("actions_correctives").select("*").eq("non_conformite_id", nc["id"]).execute().data
                if actions:
                    for action in actions:
                        st.write(f"- **Action**: {action['action']} (Responsable: {action['responsable']}, Échéance: {action['delai']})")
                else:
                    st.info("Aucune action corrective.")

                # Boutons pour chaque carte
                edit_button = st.button(f"✏️ Éditer {nc['objet']}", key=f"edit_{nc['id']}")
                add_action_button = st.button(f"➕ Ajouter une Action Corrective {nc['objet']}", key=f"action_{nc['id']}")

                if edit_button:
                    st.session_state.edit_mode = nc["id"]
                    st.markdown("### Formulaire d'Édition")
                    edited_objet = st.text_input("Objet", value=nc["objet"])
                    edited_description = st.text_area("Description", value=nc["description"])
                    edited_status = st.selectbox("Statut", ["open", "closed"], index=["open", "closed"].index(nc["status"]))
                    if st.button("Enregistrer les modifications"):
                        supabase.table("non_conformites").update({
                            "objet": edited_objet,
                            "description": edited_description,
                            "status": edited_status
                        }).eq("id", nc["id"]).execute()
                        st.success("Modifications enregistrées.")

                if add_action_button:
                    st.markdown(f"### Ajouter une Action Corrective pour {nc['objet']}")
                    action_name = st.text_input("Nom de l'action")
                    responsible = st.text_input("Responsable")
                    due_date = st.date_input("Date d'échéance")
                    if st.button("Ajouter l'Action"):
                        supabase.table("actions_correctives").insert({
                            "non_conformite_id": nc["id"],
                            "action": action_name,
                            "responsable": responsible,
                            "delai": due_date.isoformat(),
                            "created_at": datetime.datetime.utcnow().isoformat(),
                        }).execute()
                        st.success("Action corrective ajoutée avec succès.")
