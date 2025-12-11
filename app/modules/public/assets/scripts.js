// Tracking de vistas y descargas para datasets en la página principal
document.addEventListener('click', function (e) {

    // Registrar vista cuando se hace clic en "View dataset" o en el título del dataset
    if (e.target.closest('.dataset-view-link')) {
        e.preventDefault();
        var link = e.target.closest('.dataset-view-link');
        var datasetId = link.getAttribute('data-dataset-id');
        var datasetUrl = link.getAttribute('href');

        // Registrar la vista
        fetch('/food/dataset/' + datasetId + '/view', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (!data.success) {
                    console.error('Error registering view:', data.message);
                }
                // Redirigir al dataset
                window.location.href = datasetUrl;
            })
            .catch(function (error) {
                console.error('Error registering view:', error);
                // Redirigir de todos modos
                window.location.href = datasetUrl;
            });
    }

    // Registrar descarga cuando se hace clic en "Download"
    if (e.target.closest('.dataset-download-link')) {
        e.preventDefault();
        var link = e.target.closest('.dataset-download-link');
        var datasetId = link.getAttribute('data-dataset-id');
        var downloadUrl = link.getAttribute('href');

        // Registrar la descarga
        fetch('/food/dataset/' + datasetId + '/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (!data.success) {
                    console.error('Error registering download:', data.message);
                    // Continuar con la descarga de todos modos
                }
                // Iniciar descarga
                window.location.href = downloadUrl;
            })
            .catch(function (error) {
                console.error('Error registering download:', error);
                // Continuar con la descarga de todos modos
                window.location.href = downloadUrl;
            });
    }
});


document.addEventListener('DOMContentLoaded', function () {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});