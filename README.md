# 🛠️ Système de Gestion des Non-Conformités

Cette application est un système de gestion des non-conformités construit avec **Streamlit** et **Supabase**. Elle permet aux utilisateurs de soumettre, consulter et gérer des non-conformités. Les administrateurs peuvent également y ajouter des actions correctives.

---

## 📝 Fonctionnalités

### 1. **Authentification**
- Les utilisateurs doivent se connecter pour accéder à l'application.
- L'authentification est gérée via la table `users` de Supabase.
- Les rôles des utilisateurs sont définis (`utilisateur` ou `admin`).

### 2. **Soumission de Non-Conformités**
- Les utilisateurs peuvent soumettre des non-conformités en fournissant :
  - Un **objet**
  - Un **type** (Qualité, Sécurité, Environnement)
  - Une **description**
  - Des **photos** associées (PNG, JPG ou JPEG).
- Les photos sont téléversées vers le stockage Supabase et leurs URL publiques sont enregistrées dans la base de données.

### 3. **Tableau de Bord**
- Le tableau de bord affiche toutes les non-conformités sous forme de tableau :
  - **Objet** : Résumé du sujet de la non-conformité.
  - **Description** : Explication détaillée.
  - **Type** : Catégorie de la non-conformité.
  - **Statut** : Statut actuel (par défaut, "Open").
  - **Photos** : Miniatures des photos associées.
  - **Éditer** : Bouton pour modifier ou gérer une non-conformité.
- Les actions correctives associées à chaque non-conformité sont listées.
- Les administrateurs peuvent ajouter de nouvelles actions correctives.

### 4. **Gestion des Actions Correctives**
- Les actions correctives sont liées à une non-conformité via son identifiant.
- Une action comprend :
  - La **description de l'action**
  - Une **échéance**
  - Le **responsable** de la mise en œuvre.
- Les actions sont enregistrées dans la table `actions_correctives`.

### 5. **Profil Utilisateur**
- Les utilisateurs peuvent consulter leur profil, y compris :
  - Leur **email**
  - Leur **rôle**
- Une option de déconnexion est disponible.

---

## ⚙️ Configuration

### Prérequis
- Python 3.9 ou supérieur
- Une base de données Supabase configurée avec les tables suivantes :
  - `users`
  - `non_conformites`
  - `actions_correctives`

### Installation
1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/votre-repo/non-conformite-app.git
   cd non-conformite-app
Installez les dépendances :

bash
Copier le code
pip install -r requirements.txt
Configurez les variables secrètes de Streamlit :

Créez un fichier .streamlit/secrets.toml :
toml
Copier le code
[general]
SUPABASE_URL = "votre_supabase_url"
SUPABASE_ANON_KEY = "votre_supabase_anon_key"
Lancez l'application :

bash
Copier le code
streamlit run app.py
📂 Structure des Données
Table users
Champ	Type	Description
id	UUID	Identifiant unique
email	String	Adresse email de l'utilisateur
password	String	Mot de passe (crypté recommandé)
role	String	Rôle de l'utilisateur (admin/user)
Table non_conformites
Champ	Type	Description
id	UUID	Identifiant unique
user_id	UUID	Référence à l'utilisateur
objet	String	Objet de la non-conformité
type	String	Type de non-conformité (Qualité, etc.)
description	Text	Description détaillée
photos	Array	Liste des URL des photos associées
status	String	Statut de la non-conformité (ex: Open)
created_at	DateTime	Date de création
Table actions_correctives
Champ	Type	Description
id	UUID	Identifiant unique
non_conformite_id	UUID	Référence à la non-conformité
action	String	Description de l'action corrective
delai	Date	Échéance de l'action
responsable	String	Responsable de l'action
created_at	DateTime	Date de création
🛠️ Fonctionnement de l'Application
Authentification
Les utilisateurs saisissent leurs identifiants pour se connecter.
Les informations sont vérifiées dans la base de données Supabase via l'API.
Soumission d'une Non-Conformité
L'utilisateur remplit un formulaire contenant les champs obligatoires.
Les photos sont téléversées vers Supabase Storage.
Les informations sont sauvegardées dans la table non_conformites.
Affichage des Non-Conformités
Les non-conformités sont listées sous forme de tableau.
Chaque ligne affiche les attributs principaux, avec des boutons pour afficher ou modifier les détails.
Gestion des Actions Correctives
Les administrateurs peuvent ajouter des actions correctives.
Les actions sont liées aux non-conformités via leur identifiant.
🚀 Améliorations Futures
Ajout d'un système de filtres pour rechercher ou trier les non-conformités.
Notifications pour les échéances d'actions correctives.
Tableau de bord analytique avec graphiques pour visualiser les tendances.
