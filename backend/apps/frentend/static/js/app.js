
        const { createApp } = Vue;

        createApp({
            delimiters: ['[[', ']]'],
            data() {
                return {
                    // Configuration API
                    apiBaseUrl: 'http://localhost:8000/api',
                    authToken: '', // À remplir avec votre token d'authentification
                    
                    // État de l'application
                    documents: [],
                    messages: [],
                    stats: {
                        total_documents: 0,
                        total_chunks: 0,
                        total_characters: 0
                    },
                    
                    // Upload
                    isDragging: false,
                    uploadProgress: [],
                    
                    // Chat
                    currentQuestion: '',
                    isLoadingAnswer: false
                };
            },
            
            mounted() {
                this.loadStats();
                this.loadDocuments();
                
                // Polling pour rafraîchir les stats et documents
                setInterval(() => {
                    this.loadStats();
                    this.loadDocuments();
                }, 5000);
            },
            
            methods: {
                // Configuration Axios avec token
                getAxiosConfig() {
                    return {
                        headers: {
                            'Authorization': `Token ${this.authToken}`,
                            'Content-Type': 'application/json'
                        }
                    };
                },
                
                // Charger les statistiques
                async loadStats() {
                    try {
                        const response = await axios.get(
                            `${this.apiBaseUrl}/rag/stats/`,
                            this.getAxiosConfig()
                        );
                        this.stats = response.data;
                    } catch (error) {
                        console.error('Erreur lors du chargement des stats:', error);
                    }
                },
                
                // Charger les documents
                async loadDocuments() {
                    try {
                        const response = await axios.get(
                            `${this.apiBaseUrl}/documents/`,
                            this.getAxiosConfig()
                        );
                        this.documents = response.data.results || response.data;
                    } catch (error) {
                        console.error('Erreur lors du chargement des documents:', error);
                    }
                },
                
                // Upload de fichiers
                triggerFileInput() {
                    this.$refs.fileInput.click();
                },
                
                handleFileSelect(event) {
                    const files = Array.from(event.target.files);
                    this.uploadFiles(files);
                },
                
                handleFileDrop(event) {
                    this.isDragging = false;
                    const files = Array.from(event.dataTransfer.files);
                    this.uploadFiles(files);
                },
                
                async uploadFiles(files) {
                    for (const file of files) {
                        const progressItem = {
                            name: file.name,
                            progress: 0,
                            status: 'Upload en cours...'
                        };
                        this.uploadProgress.push(progressItem);
                        
                        const formData = new FormData();
                        formData.append('file', file);
                        formData.append('title', file.name.replace(/\.[^/.]+$/, ''));
                        
                        try {
                            await axios.post(
                                `${this.apiBaseUrl}/documents/upload/`,
                                formData,
                                {
                                    headers: {
                                        'Authorization': `Token ${this.authToken}`,
                                        'Content-Type': 'multipart/form-data'
                                    },
                                    onUploadProgress: (progressEvent) => {
                                        progressItem.progress = Math.round(
                                            (progressEvent.loaded * 100) / progressEvent.total
                                        );
                                    }
                                }
                            );
                            
                            progressItem.status = 'Terminé';
                            progressItem.progress = 100;
                            
                            // Rafraîchir la liste
                            setTimeout(() => {
                                this.loadDocuments();
                                this.loadStats();
                            }, 1000);
                            
                        } catch (error) {
                            progressItem.status = 'Erreur';
                            console.error('Erreur upload:', error);
                        }
                    }
                    
                    // Nettoyer la progress bar après 3 secondes
                    setTimeout(() => {
                        this.uploadProgress = [];
                    }, 3000);
                },
                
                // Poser une question
                async askQuestion() {
                    if (!this.currentQuestion.trim()) return;
                    
                    // Ajouter la question à l'historique
                    this.messages.push({
                        role: 'user',
                        content: this.currentQuestion
                    });
                    
                    const question = this.currentQuestion;
                    this.currentQuestion = '';
                    this.isLoadingAnswer = true;
                    
                    // Scroll automatique
                    this.$nextTick(() => {
                        this.scrollToBottom();
                    });
                    
                    try {
                        const response = await axios.post(
                            `${this.apiBaseUrl}/rag/ask/`,
                            {
                                question: question,
                                top_k: 5
                            },
                            this.getAxiosConfig()
                        );
                        
                        // Ajouter la réponse
                        this.messages.push({
                            role: 'assistant',
                            content: response.data.answer,
                            sources: response.data.sources
                        });
                        
                    } catch (error) {
                        this.messages.push({
                            role: 'assistant',
                            content: '❌ Erreur lors de la génération de la réponse. Vérifiez votre configuration API.',
                            sources: []
                        });
                        console.error('Erreur RAG:', error);
                    } finally {
                        this.isLoadingAnswer = false;
                        this.$nextTick(() => {
                            this.scrollToBottom();
                        });
                    }
                },
                
                // Supprimer un document
                async deleteDocument(docId) {
                    if (!confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) return;
                    
                    try {
                        await axios.delete(
                            `${this.apiBaseUrl}/documents/${docId}/`,
                            this.getAxiosConfig()
                        );
                        this.loadDocuments();
                        this.loadStats();
                    } catch (error) {
                        console.error('Erreur suppression:', error);
                    }
                },
                
                // Utilitaires
                scrollToBottom() {
                    if (this.$refs.chatContainer) {
                        this.$refs.chatContainer.scrollTop = this.$refs.chatContainer.scrollHeight;
                    }
                },
                
                scrollToUpload() {
                    document.getElementById('upload').scrollIntoView({ behavior: 'smooth' });
                },
                
                formatFileSize(bytes) {
                    if (bytes === 0) return '0 B';
                    const k = 1024;
                    const sizes = ['B', 'KB', 'MB', 'GB'];
                    const i = Math.floor(Math.log(bytes) / Math.log(k));
                    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
                },
                
                formatNumber(num) {
                    if (num > 1000000) return (num / 1000000).toFixed(1) + 'M';
                    if (num > 1000) return (num / 1000).toFixed(1) + 'K';
                    return num;
                },
                
                formatDate(dateString) {
                    const date = new Date(dateString);
                    return date.toLocaleDateString('fr-FR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                }
            }
        }).mount('#app');