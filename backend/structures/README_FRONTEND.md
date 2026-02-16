# 🎨 Smart-Notebook - Frontend

Interface web moderne et responsive pour Smart-Notebook, votre clone de Google NotebookLM.

## 🌟 Caractéristiques du Design

### Esthétique Brutaliste Moderne
- **Palette distinctive** : Thème sombre avec accents néon verts (#00FF9D)
- **Typographie** : Archivo Black (display) + DM Sans (body) + JetBrains Mono (code)
- **Effets visuels** : Glassmorphism, grain texture, animations fluides
- **No AI slop** : Design unique qui évite les clichés (Inter, gradients violets, etc.)

### Technologies
- **Vue.js 3** (CDN) - Framework réactif
- **Bootstrap 5** - Grid responsive
- **Axios** - Requêtes HTTP vers l'API Django
- **Bootstrap Icons** - Icônes modernes
- **Vanilla CSS** - Animations et effets personnalisés

## 📂 Structure du fichier

```
index.html
├── Head
│   ├── Bootstrap 5 CSS
│   ├── Google Fonts (Archivo Black, DM Sans, JetBrains Mono)
│   ├── Bootstrap Icons
│   ├── Vue.js 3 (CDN)
│   └── Axios (CDN)
│
├── Style CSS embarqué
│   ├── Variables CSS (palette de couleurs)
│   ├── Background animé avec grain
│   ├── Glassmorphic cards
│   ├── Animations et transitions
│   └── Responsive design
│
├── Body (Vue App)
│   ├── Navbar fixe
│   ├── Hero Section avec stats
│   ├── Features (3 cartes)
│   ├── Upload Zone (drag & drop)
│   ├── Chat Interface (RAG)
│   ├── Documents List
│   └── Footer
│
└── Scripts
    ├── Vue.js App Setup
    ├── API Integration (Axios)
    └── Bootstrap JS
```

## 🚀 Installation & Configuration

### 1. Aucune installation requise !

Ce fichier HTML est **standalone** et fonctionne directement dans le navigateur.  
Toutes les dépendances sont chargées via CDN.

### 2. Configuration de l'API

Ouvrez `index.html` et modifiez ces lignes dans la section `data()` :

```javascript
data() {
    return {
        // Configuration API
        apiBaseUrl: 'http://localhost:8000/api',  // ← URL de votre backend Django
        authToken: 'votre-token-ici',              // ← Token d'authentification
        // ...
    }
}
```

### 3. Obtenir un token d'authentification

#### Option A : Via Django Admin
```bash
python manage.py createsuperuser
python manage.py drf_create_token <username>
```

#### Option B : Via Python Shell
```python
python manage.py shell

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user = User.objects.get(username='votre-username')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
```

#### Option C : Via l'API (si DRF Auth est configurée)
```bash
curl -X POST http://localhost:8000/api/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "votre-username", "password": "votre-password"}'
```

### 4. Lancement

Deux options :

#### Option A : Serveur HTTP simple (Python)
```bash
python -m http.server 8080
```
Puis ouvrez : http://localhost:8080

#### Option B : Live Server (VS Code)
- Installez l'extension "Live Server"
- Clic droit sur `index.html` → "Open with Live Server"

#### Option C : Directement dans le navigateur
```bash
# Linux/Mac
open index.html

# Ou glissez simplement le fichier dans votre navigateur
```

## 🎯 Fonctionnalités

### 1. Dashboard de Statistiques
- Nombre total de documents
- Nombre total de chunks vectorisés
- Nombre total de caractères indexés
- Mise à jour automatique toutes les 5 secondes

### 2. Upload de Documents
- **Drag & Drop** : Glissez vos PDFs directement
- **Click to Browse** : Sélection classique de fichiers
- **Multi-upload** : Plusieurs fichiers simultanément
- **Progress Bar** : Suivi de l'upload en temps réel
- **Support** : PDF et TXT (50 MB max)

### 3. Interface de Chat RAG
- **Questions en langage naturel** : Posez vos questions simplement
- **Réponses contextualisées** : Réponses basées sur vos documents
- **Sources citées** : Chaque réponse affiche ses sources
- **Scroll automatique** : Interface fluide
- **Loading states** : Feedback visuel pendant le traitement

### 4. Gestion des Documents
- **Liste complète** : Tous vos documents uploadés
- **Statuts en temps réel** :
  - 🟡 PENDING : En attente de traitement
  - 🟢 PROCESSING : Traitement en cours
  - ✅ COMPLETED : Prêt à être interrogé
  - ❌ FAILED : Erreur de traitement
- **Suppression** : Bouton de suppression avec confirmation
- **Métadonnées** : Taille, nombre de chunks, date d'upload

## 🎨 Personnalisation du Design

### Changer la palette de couleurs

Modifiez les variables CSS dans la section `:root` :

```css
:root {
    /* Votre palette personnalisée */
    --primary: #votre-couleur;
    --accent: #votre-accent;
    --text-primary: #votre-texte;
    /* ... */
}
```

### Thèmes prédéfinis suggérés

#### Thème Cyberpunk
```css
--primary: #0D0221;
--accent: #F72585;
--accent-glow: rgba(247, 37, 133, 0.3);
```

#### Thème Nature
```css
--primary: #1A3A1A;
--accent: #7FFF00;
--accent-glow: rgba(127, 255, 0, 0.3);
```

#### Thème Ocean
```css
--primary: #001B2E;
--accent: #00D9FF;
--accent-glow: rgba(0, 217, 255, 0.3);
```

## 🔧 Connexion avec le Backend Django

### Endpoints utilisés

```javascript
// Statistiques
GET /api/rag/stats/

// Liste des documents
GET /api/documents/

// Upload de document
POST /api/documents/upload/
Body: FormData avec 'file' et 'title'

// Poser une question RAG
POST /api/rag/ask/
Body: {
  "question": "Votre question",
  "top_k": 5
}

// Supprimer un document
DELETE /api/documents/<id>/
```

### Configuration CORS (Backend)

Assurez-vous que votre backend Django autorise les requêtes depuis le frontend :

```python
# config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5500",  # Live Server VS Code
]
```

## 📱 Responsive Design

L'interface s'adapte automatiquement à toutes les tailles d'écran :

- **Desktop** (>1200px) : Layout complet avec toutes les fonctionnalités
- **Tablet** (768px-1200px) : Layout adapté, grilles réorganisées
- **Mobile** (<768px) : Layout vertical, navigation simplifiée

## 🎬 Animations

### Animations d'entrée
- **Fade-in** : Apparition progressive des sections
- **Stagger** : Décalage temporel entre les éléments
- **Slide-in** : Messages de chat glissent depuis le bas

### Micro-interactions
- **Hover effects** : Cartes qui s'élèvent, bordures qui brillent
- **Float animation** : Icône d'upload qui flotte
- **Pulse** : Badge "Processing" qui pulse
- **Glow effects** : Accents néon qui brillent

## 🐛 Dépannage

### Problème : CORS Error
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution** : Vérifiez que `CORS_ALLOWED_ORIGINS` dans Django inclut votre URL frontend.

### Problème : 401 Unauthorized
```
Authentication credentials were not provided
```
**Solution** : Vérifiez que `authToken` est correct dans `index.html`.

### Problème : Les stats ne se chargent pas
**Solution** :
1. Vérifiez que Django tourne : `http://localhost:8000`
2. Vérifiez que l'API répond : `curl http://localhost:8000/api/rag/stats/`
3. Ouvrez la console du navigateur (F12) pour voir les erreurs

### Problème : Upload ne fonctionne pas
**Solution** :
1. Vérifiez la taille du fichier (< 50 MB)
2. Vérifiez le type de fichier (PDF ou TXT uniquement)
3. Consultez les logs Django pour les erreurs côté serveur

## 🚀 Optimisations de Production

### 1. Hébergement Statique
Le fichier HTML peut être hébergé n'importe où :
- Netlify
- Vercel
- GitHub Pages
- Nginx
- Apache

### 2. CDN → Local
Pour de meilleures performances, téléchargez les dépendances :

```bash
# Créer un dossier assets
mkdir -p assets/{css,js}

# Télécharger Bootstrap
wget https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css -O assets/css/bootstrap.min.css
wget https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js -O assets/js/bootstrap.bundle.min.js

# Télécharger Vue.js
wget https://cdn.jsdelivr.net/npm/vue@3.4.15/dist/vue.global.prod.js -O assets/js/vue.global.prod.js

# Télécharger Axios
wget https://cdn.jsdelivr.net/npm/axios@1.6.5/dist/axios.min.js -O assets/js/axios.min.js
```

Puis modifiez les liens dans `<head>` :
```html
<link href="assets/css/bootstrap.min.css" rel="stylesheet">
<script src="assets/js/vue.global.prod.js"></script>
<script src="assets/js/axios.min.js"></script>
```

### 3. Minification CSS
Pour réduire la taille, minifiez le CSS embarqué avec un outil comme :
- https://www.toptal.com/developers/cssminifier/
- https://cssnano.co/

## 📊 Performance

### Lighthouse Score cible
- Performance : 90+
- Accessibility : 95+
- Best Practices : 90+
- SEO : 85+

### Optimisations déjà implémentées
✅ CSS-only animations (pas de JavaScript lourd)  
✅ Lazy loading des ressources  
✅ Minimal JavaScript footprint  
✅ Responsive images (via Bootstrap)  
✅ GPU-accelerated transforms  

## 🎓 Concepts Clés

### Architecture Vue.js
```javascript
createApp({
  data() {
    // État réactif de l'application
    return {
      documents: [],
      messages: [],
      stats: {}
    }
  },
  
  mounted() {
    // Chargement initial des données
    this.loadStats();
    this.loadDocuments();
    
    // Polling toutes les 5 secondes
    setInterval(() => {
      this.loadStats();
      this.loadDocuments();
    }, 5000);
  },
  
  methods: {
    // Méthodes pour interagir avec l'API
    async loadStats() { ... },
    async askQuestion() { ... },
    async uploadFiles() { ... }
  }
})
```

### Glassmorphism
Effet de verre givré obtenu avec :
- `backdrop-filter: blur(20px)` - Flou du fond
- `background: rgba()` - Transparence
- `border: 1px solid rgba()` - Bordure subtile

### Animations CSS
```css
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn 0.6s ease-out;
}
```

## 🆘 Support

En cas de problème :
1. Vérifiez la console du navigateur (F12)
2. Vérifiez les logs Django
3. Vérifiez que tous les services sont démarrés (Django, Redis, Celery, Ollama)

## 📞 Ressources

- [Vue.js 3 Docs](https://vuejs.org/)
- [Bootstrap 5 Docs](https://getbootstrap.com/)
- [Axios Docs](https://axios-http.com/)
- [CSS Animations](https://animate.style/)

## 🎉 Prochaines Étapes

Améliorations possibles :
- [ ] Authentification complète (login/logout)
- [ ] Mode sombre/clair
- [ ] Export des conversations
- [ ] Recherche dans les documents
- [ ] Génération de podcasts (interface TTS)
- [ ] Graphiques de statistiques (Chart.js)
- [ ] Notifications push (WebSockets)

---

**Fait avec ❤️ en design brutaliste moderne**
