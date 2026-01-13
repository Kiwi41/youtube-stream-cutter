# Configuration Google Drive OAuth2

## Étapes pour activer l'upload vers Google Drive

### 1. Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet
3. Activez l'API Google Drive :
   - Menu → APIs & Services → Enable APIs and Services
   - Recherchez "Google Drive API"
   - Cliquez sur "Enable"

### 2. Créer des credentials OAuth2

1. Dans Google Cloud Console :
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type : Desktop app
   - Name : YouTube Stream Cutter (ou autre)
   - Téléchargez le fichier JSON

2. Récupérez `client_id` et `client_secret` du fichier JSON

### 3. Configurer settings.yaml

Modifiez le fichier `settings.yaml` à la racine du projet :

```yaml
client_config_backend: settings
client_config:
  client_id: VOTRE_CLIENT_ID_ICI
  client_secret: VOTRE_CLIENT_SECRET_ICI

save_credentials: True
save_credentials_backend: file
save_credentials_file: credentials.json

get_refresh_token: True

oauth_scope:
  - https://www.googleapis.com/auth/drive.file
  - https://www.googleapis.com/auth/drive.install
```

### 4. Premier lancement

Au premier téléchargement avec "Upload vers Google Drive" coché :
1. Un navigateur s'ouvrira
2. Connectez-vous à votre compte Google
3. Autorisez l'application
4. Les credentials seront sauvegardés dans `credentials.json`

### 5. ID de dossier Drive (optionnel)

Pour uploader dans un dossier spécifique :
1. Ouvrez le dossier sur Google Drive
2. L'URL ressemble à : `https://drive.google.com/drive/folders/XXXXXXXXXXXXX`
3. Copiez la partie `XXXXXXXXXXXXX` dans le champ "ID dossier Drive"

Si vous laissez ce champ vide, les fichiers seront uploadés à la racine de votre Drive.
