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

    elif menu == "Tableau de Bord":
        # Tableau de bord
        st.header("📊 Tableau de Bord des Non-Conformités")

        # Récupération des non-conformités
        if is_admin:
            response = supabase.table("non_conformites").select("*").execute()  # Tous les enregistrements pour les admins
        else:
            response = supabase.table("non_conformites").select("*").eq("user_id", user["id"]).execute()  # Seulement ceux de l'utilisateur

        non_conformities = response.data

        if non_conformities:
            st.write("### Liste des Non-Conformités")

            # Affichage dynamique des non-conformités sous forme de cartes
            for nc in non_conformities:
                st.markdown("---")
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 20px; background-color: #f9f9f9;">
                        <h4>{nc['objet']} ({nc['type']})</h4>
                        <p><strong>Description :</strong> {nc['description']}</p>
                        <p><strong>Statut :</strong> {nc['status']}</p>
                        <p><strong>Créé le :</strong> {nc['created_at']}</p>
                        <div>
                            {"".join([f"<img src='{url}' style='width: 80px; margin-right: 10px; border-radius: 5px;'>" for url in nc['photos']])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Actions Correctives
                st.markdown("#### Actions Correctives")
                actions = supabase.table("actions_correctives").select("*").eq("non_conformite_id", nc["id"]).execute().data
                if actions:
                    for action in actions:
                        st.write(f"- **Action**: {action['action']} (Responsable: {action['responsable']}, Échéance: {action['delai']})")
                else:
                    st.info("Aucune action corrective enregistrée.")

                # Boutons d'action
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✏️ Éditer - {nc['id']}"):
                        st.info(f"Formulaire d'édition pour {nc['objet']} non implémenté.")
                with col2:
                    if st.button(f"➕ Ajouter une Action Corrective - {nc['id']}"):
                        with st.form(f"add_action_{nc['id']}"):
                            new_action = st.text_input("Nouvelle Action")
                            responsable = st.text_input("Responsable")
                            due_date = st.date_input("Échéance")
                            submit_action = st.form_submit_button("Enregistrer")
                            if submit_action:
                                # Sauvegarde de l'action corrective
                                supabase.table("actions_correctives").insert({
                                    "non_conformite_id": nc["id"],
                                    "action": new_action,
                                    "responsable": responsable,
                                    "delai": due_date.isoformat(),
                                    "created_at": datetime.datetime.utcnow().isoformat()
                                }).execute()
                                st.success("Action corrective ajoutée avec succès !")
        else:
            st.info("Aucune non-conformité trouvée.")

    elif menu == "Profil":
        st.header("Profil Utilisateur")
        st.write(f"**Email**: {user['email']}")
        st.write(f"**Rôle**: {'Administrateur' if is_admin else 'Utilisateur Standard'}")
        if st.button("Déconnexion"):
            st.session_state.user = None
            st.experimental_rerun()
