// Tracking de vistas y descargas para datasets en la página principal
document.addEventListener('DOMContentLoaded', function () {
    console.log('=== TRACKING SCRIPT LOADED ===');
    
    // Inicializar feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Función para registrar una vista
    function registerView(datasetId, redirectUrl) {
        console.log(`Registrando vista para dataset ${datasetId}`);
        
        fetch(`/dataset/${datasetId}/view`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log('Respuesta de vista:', response.status);
            if (!response.ok) {
                console.warn('Error registrando vista, pero continuando...');
            }
            return response.json();
        })
        .then(data => {
            console.log('Vista registrada:', data);
            window.location.href = redirectUrl;
        })
        .catch(error => {
            console.error('Error registrando vista:', error);
            window.location.href = redirectUrl;
        });
    }

    // Función para registrar una descarga
    function registerDownload(datasetId, downloadUrl) {
        console.log(`Registrando descarga para dataset ${datasetId}`);
        
        fetch(`/dataset/${datasetId}/download`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log('Respuesta de descarga:', response.status);
            if (!response.ok) {
                console.warn('Error registrando descarga, pero continuando...');
            }
            return response.json();
        })
        .then(data => {
            console.log('Descarga registrada:', data);
            window.location.href = downloadUrl;
        })
        .catch(error => {
            console.error('Error registrando descarga:', error);
            window.location.href = downloadUrl;
        });
    }

    // Manejar clics en la página
    document.addEventListener('click', function (e) {
        console.log('Click detectado en:', e.target.tagName, e.target.className);
        
        // 1. Detectar clic en botón "View dataset" USANDO LA CLASE dataset-view-link
        const viewButton = e.target.closest('.dataset-view-link');
        if (viewButton) {
            console.log('Botón View dataset encontrado');
            e.preventDefault();
            
            const datasetId = viewButton.getAttribute('data-dataset-id');
            const redirectUrl = viewButton.getAttribute('href');
            
            console.log('Dataset ID:', datasetId, 'URL:', redirectUrl);
            
            if (datasetId) {
                registerView(datasetId, redirectUrl);
            } else {
                console.warn('No hay dataset ID, redirigiendo sin tracking');
                window.location.href = redirectUrl;
            }
            return;
        }
        
        // 2. Detectar clic en el título del dataset
        const titleLink = e.target.closest('h2 a');
        if (titleLink) {
            console.log('Título del dataset clickeado');
            e.preventDefault();
            
            // Buscar el dataset ID en la misma tarjeta
            const card = titleLink.closest('.card');
            if (card) {
                const downloadLink = card.querySelector('.dataset-download-link');
                if (downloadLink) {
                    const datasetId = downloadLink.getAttribute('data-dataset-id');
                    const redirectUrl = titleLink.getAttribute('href');
                    
                    console.log('Dataset ID desde download link:', datasetId);
                    
                    if (datasetId) {
                        registerView(datasetId, redirectUrl);
                    } else {
                        console.warn('No hay dataset ID en el download link');
                        window.location.href = redirectUrl;
                    }
                } else {
                    console.warn('No se encontró download link en la tarjeta');
                    window.location.href = titleLink.getAttribute('href');
                }
            } else {
                console.warn('No se encontró la tarjeta contenedora');
                window.location.href = titleLink.getAttribute('href');
            }
            return;
        }
        
        // 3. Detectar clic en botón "Download"
        const downloadLink = e.target.closest('.dataset-download-link');
        if (downloadLink) {
            console.log('Botón Download encontrado');
            e.preventDefault();
            
            const datasetId = downloadLink.getAttribute('data-dataset-id');
            const downloadUrl = downloadLink.getAttribute('href');
            
            console.log('Dataset ID:', datasetId, 'URL:', downloadUrl);
            
            if (datasetId) {
                registerDownload(datasetId, downloadUrl);
            } else {
                console.warn('No hay dataset ID, redirigiendo sin tracking');
                window.location.href = downloadUrl;
            }
        }
    });
});