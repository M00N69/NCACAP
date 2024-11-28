async function uploadPhotos(files) {
    const storageBucket = 'photos';
    const uploadedFiles = [];

    for (const file of files) {
        const filePath = `${Date.now()}_${file.name}`;
        const { data, error } = await supabase.storage.from(storageBucket).upload(filePath, file);
        if (error) {
            console.error('Erreur :', error.message);
        } else {
            const publicURL = supabase.storage.from(storageBucket).getPublicUrl(filePath).data.publicUrl;
            uploadedFiles.push(publicURL);
        }
    }

    return uploadedFiles;
}

async function submitNonConformite() {
    const objet = document.getElementById('objet').value;
    const type = document.getElementById('type').value;
    const description = document.getElementById('description').value;
    const files = document.getElementById('photos').files;

    const photos = await uploadPhotos(files);

    const { data, error } = await supabase
        .from('non_conformites')
        .insert([{ objet, type, description, photos, status: 'ouvert' }]);

    if (error) {
        alert('Erreur : ' + error.message);
    } else {
        alert('Fiche créée avec succès !');
        loadNonConformites();
    }
}

async function loadNonConformites() {
    const { data, error } = await supabase.from('non_conformites').select('*');
    if (error) {
        alert('Erreur : ' + error.message);
    } else {
        const ficheList = document.getElementById('fiche-list');
        ficheList.innerHTML = '';
        data.forEach(fiche => {
            const photosHTML = fiche.photos.map(photoUrl => `<img src="${photoUrl}" style="width: 100px;">`).join('');
            ficheList.innerHTML += `
                <div>
                    <h3>${fiche.objet}</h3>
                    <p>${fiche.description}</p>
                    <div>${photosHTML}</div>
                </div>
            `;
        });
    }
}

