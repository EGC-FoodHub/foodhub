// Tracking de vistas y descargas para datasets en la página principal
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Registrar vista cuando se hace clic en "View dataset" o en el título
    document.addEventListener('click', function (e) {
        // Verificar si es un enlace de vista de dataset
        const viewLink = e.target.closest('a[href*="/food/dataset/"]');
        if (viewLink && !viewLink.classList.contains('dataset-download-link')) {
            e.preventDefault();
            const href = viewLink.getAttribute('href');
            const datasetIdMatch = href.match(/\/food\/dataset\/(\d+)/);
            
            if (datasetIdMatch) {
                const datasetId = datasetIdMatch[1];
                
                // Registrar la vista
                fetch(`/food/dataset/${datasetId}/view`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': getCSRFToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        console.error('Error registering view:', data.message);
                    }
                    // Redirigir al dataset
                    window.location.href = href;
                })
                .catch(error => {
                    console.error('Error registering view:', error);
                    // Redirigir de todos modos
                    window.location.href = href;
                });
            }
        }

        // Registrar descarga cuando se hace clic en "Download"
        const downloadLink = e.target.closest('.dataset-download-link');
        if (downloadLink) {
            e.preventDefault();
            const datasetId = downloadLink.getAttribute('data-dataset-id');
            const downloadUrl = downloadLink.getAttribute('href');

            if (!datasetId) {
                console.error('Dataset ID not found in download link');
                window.location.href = downloadUrl;
                return;
            }

            // Registrar la descarga
            fetch(`/food/dataset/${datasetId}/download`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('Error registering download:', data.message);
                }
                // Iniciar descarga
                window.location.href = downloadUrl;
            })
            .catch(error => {
                console.error('Error registering download:', error);
                // Continuar con la descarga de todos modos
                window.location.href = downloadUrl;
            });
        }
    });

    // Función para obtener el token CSRF (si usas Flask-WTF)
    function getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        return '';
    }
});