// Tracking de vistas y descargas para datasets en la página principal
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Función para registrar una vista
    function registerView(datasetId, redirectUrl) {
        fetch(`/dataset/${datasetId}/view`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                console.warn('Error registering view, but continuing...');
            }
            return response.json();
        })
        .then(data => {
            console.log('View registered:', data);
            window.location.href = redirectUrl;
        })
        .catch(error => {
            console.error('Error registering view:', error);
            window.location.href = redirectUrl;
        });
    }

    // Función para registrar una descarga
    function registerDownload(datasetId, downloadUrl) {
        fetch(`/dataset/${datasetId}/download`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                console.warn('Error registering download, but continuing...');
            }
            return response.json();
        })
        .then(data => {
            console.log('Download registered:', data);
            window.location.href = downloadUrl;
        })
        .catch(error => {
            console.error('Error registering download:', error);
            window.location.href = downloadUrl;
        });
    }

    // Manejar clics en la página
    document.addEventListener('click', function (e) {
        const target = e.target;
        
        // 1. Detectar clic en botón "View dataset" de Latest datasets
        const viewButton = target.closest('a.btn[href*="doi.org"]');
        if (viewButton && viewButton.textContent.includes('View dataset')) {
            e.preventDefault();
            
            // Buscar la tarjeta contenedora
            const card = viewButton.closest('.card');
            if (card) {
                // Buscar el enlace de descarga que tiene el data-dataset-id
                const downloadLink = card.querySelector('.dataset-download-link');
                if (downloadLink) {
                    const datasetId = downloadLink.getAttribute('data-dataset-id');
                    const redirectUrl = viewButton.getAttribute('href');
                    
                    if (datasetId) {
                        registerView(datasetId, redirectUrl);
                    } else {
                        window.location.href = redirectUrl;
                    }
                    return; // Importante: salir después de manejar el clic
                }
            }
            window.location.href = viewButton.getAttribute('href');
        }
        
        // 2. Detectar clic en el título del dataset (también es un enlace DOI)
        const titleLink = target.closest('a[href*="doi.org"]');
        if (titleLink && !titleLink.classList.contains('btn')) {
            // Verificar si es el título (está dentro de un h2)
            const h2Element = titleLink.closest('h2');
            if (h2Element) {
                e.preventDefault();
                
                const card = titleLink.closest('.card');
                if (card) {
                    const downloadLink = card.querySelector('.dataset-download-link');
                    if (downloadLink) {
                        const datasetId = downloadLink.getAttribute('data-dataset-id');
                        const redirectUrl = titleLink.getAttribute('href');
                        
                        if (datasetId) {
                            registerView(datasetId, redirectUrl);
                        } else {
                            window.location.href = redirectUrl;
                        }
                        return;
                    }
                }
                window.location.href = titleLink.getAttribute('href');
            }
        }
        
        // 3. Detectar clic en botón "Download"
        const downloadLink = target.closest('.dataset-download-link');
        if (downloadLink) {
            e.preventDefault();
            const datasetId = downloadLink.getAttribute('data-dataset-id');
            const downloadUrl = downloadLink.getAttribute('href');
            
            if (datasetId) {
                registerDownload(datasetId, downloadUrl);
            } else {
                window.location.href = downloadUrl;
            }
        }
    });
});