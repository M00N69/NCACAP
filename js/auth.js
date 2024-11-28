// Inscription d'un utilisateur
async function register(email, password) {
    const { data, error } = await supabase.auth.signUp({
        email,
        password
    });

    if (error) {
        alert('Erreur lors de l\'inscription : ' + error.message);
    } else {
        alert('Inscription réussie ! Veuillez vérifier votre email pour confirmer votre compte.');
    }
}

