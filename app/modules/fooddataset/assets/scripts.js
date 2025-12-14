var currentId = 0;
var amount_authors = 0;

function show_upload_dataset() {
    document.getElementById("upload_dataset").style.display = "block";
}

function generateIncrementalId() {
    return currentId++;
}

function addField(newAuthor, name, text, className = 'col-lg-6 col-12 mb-3') {
    let fieldWrapper = document.createElement('div');
    fieldWrapper.className = className;

    let label = document.createElement('label');
    label.className = 'form-label';
    label.for = name;
    label.textContent = text;

    let field = document.createElement('input');
    field.name = name;
    field.className = 'form-control';

    fieldWrapper.appendChild(label);
    fieldWrapper.appendChild(field);
    newAuthor.appendChild(fieldWrapper);
}

function addRemoveButton(newAuthor) {
    let buttonWrapper = document.createElement('div');
    buttonWrapper.className = 'col-12 mb-2';

    let button = document.createElement('button');
    button.textContent = 'Remove author';
    button.className = 'btn btn-danger btn-sm';
    button.type = 'button';
    button.addEventListener('click', function (event) {
        event.preventDefault();
        newAuthor.remove();
    });

    buttonWrapper.appendChild(button);
    newAuthor.appendChild(buttonWrapper);
}

function createAuthorBlock(idx, suffix) {
    let newAuthor = document.createElement('div');
    newAuthor.className = 'author row';
    newAuthor.style.cssText = "border:2px dotted #ccc;border-radius:10px;padding:10px;margin:10px 0; background-color: white";

    addField(newAuthor, `${suffix}authors-${idx}-name`, 'Name *');
    addField(newAuthor, `${suffix}authors-${idx}-affiliation`, 'Affiliation');
    addField(newAuthor, `${suffix}authors-${idx}-orcid`, 'ORCID');
    addRemoveButton(newAuthor);

    return newAuthor;
}

function check_title_and_description() {
    let titleInput = document.querySelector('input[name="title"]');
    let descriptionTextarea = document.querySelector('textarea[name="desc"]');

    titleInput.classList.remove("error");
    descriptionTextarea.classList.remove("error");
    clean_upload_errors();

    let titleLength = titleInput.value.trim().length;
    let descriptionLength = descriptionTextarea.value.trim().length;

    if (titleLength < 3) {
        write_upload_error("Title must be of minimum length 3");
        titleInput.classList.add("error");
    }

    if (descriptionLength < 3) {
        write_upload_error("Description must be of minimum length 3");
        descriptionTextarea.classList.add("error");
    }

    return (titleLength >= 3 && descriptionLength >= 3);
}

document.getElementById('add_author').addEventListener('click', function () {
    let authors = document.getElementById('authors');
    let newAuthor = createAuthorBlock(amount_authors++, "");
    authors.appendChild(newAuthor);
});



function show_loading() {
    document.getElementById("upload_button").style.display = "none";
    document.getElementById("loading").style.display = "block";
}

function hide_loading() {
    document.getElementById("upload_button").style.display = "block";
    document.getElementById("loading").style.display = "none";
}

function clean_upload_errors() {
    let upload_error = document.getElementById("upload_error");
    upload_error.innerHTML = "";
    upload_error.style.display = 'none';
}

function write_upload_error(error_message) {
    let upload_error = document.getElementById("upload_error");
    let alert = document.createElement('p');
    alert.style.margin = '0';
    alert.style.padding = '0';
    alert.textContent = 'Upload error: ' + error_message;
    upload_error.appendChild(alert);
    upload_error.style.display = 'block';
}

window.onload = function () {
    if (typeof test_fakenodo_connection === 'function') {
        test_fakenodo_connection();
    }

    document.getElementById('upload_button').addEventListener('click', function () {
        clean_upload_errors();
        show_loading();

        if (check_title_and_description()) {
            const formUploadData = new FormData();
            
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;
            formUploadData.append('csrf_token', csrfToken);

            const basicInputs = document.querySelectorAll('#basic_info_form input, #basic_info_form select, #basic_info_form textarea');
            basicInputs.forEach(input => {
                if (input.name && input.type !== 'submit') {
                    formUploadData.append(input.name, input.value);
                }
            });

            const modelInputs = document.querySelectorAll('#uploaded_models_form input, #uploaded_models_form select, #uploaded_models_form textarea');
            modelInputs.forEach(input => {
                if (input.name) {
                    formUploadData.append(input.name, input.value);
                }
            });

            console.log('Sending FormData...');
            
            fetch('/dataset/upload', {
                method: 'POST',
                body: formUploadData
            })
            .then(response => {
                if (response.ok) {
                    response.json().then(data => {
                        console.log(data.message);
                        window.location.href = data.redirect || "/dataset/list";
                    });
                } else {
                    response.json().then(data => {
                        console.error('Error: ' + data.message);
                        hide_loading();
                        write_upload_error(data.message || "Unknown error occurred");
                    });
                }
            })
            .catch(error => {
                console.error('Error in POST request:', error);
                hide_loading();
                write_upload_error("Network error");
            });

        } else {
            hide_loading();
        }
    });
};

function isValidOrcid(orcid) {
    let orcidRegex = /^\d{4}-\d{4}-\d{4}-\d{4}$/;
    return orcidRegex.test(orcid);
}

function validateTempFile(filename, statusElementId) {
    let statusEl = document.getElementById(statusElementId);
    statusEl.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Checking...';

    fetch('/api/food_checker/check/temp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({filename: filename})
    })
    .then(res => res.json())
    .then(data => {
        if (data.valid) {
            statusEl.innerHTML = `<span class="badge bg-success">Valid: ${data.data.type}</span>`;
        } else {
            statusEl.innerHTML = `<span class="badge bg-danger">Invalid Format</span>`;
            console.error(data.error);
        }
    })
    .catch(() => {
        statusEl.innerHTML = `<span class="badge bg-warning">Check Failed</span>`;
    });
}

document.addEventListener('click', function(e) {

    if (e.target.closest('.trending-view-link')) {
        e.preventDefault();
        var link = e.target.closest('.trending-view-link');
        var datasetId = link.getAttribute('data-dataset-id');
        var datasetUrl = link.getAttribute('href');

        fetch('/food/dataset/' + datasetId + '/view', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function(response) { 
            return response.json(); 
        })
        .then(function(data) {
            if (!data.success) {
                console.error('Error registering view:', data.message);
            }
            window.location.href = datasetUrl;
        })
        .catch(function(error) { 
            console.error('Error:', error);
            // Redirigir de todos modos
            window.location.href = datasetUrl;
        });
    }

    if (e.target.closest('.trending-download-link')) {
        e.preventDefault();
        var link = e.target.closest('.trending-download-link');
        var datasetId = link.getAttribute('data-dataset-id');
        var downloadUrl = link.getAttribute('href');
        
        fetch('/food/dataset/' + datasetId + '/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(function(response) { 
            return response.json(); 
        })
        .then(function(data) {
            if (!data.success) {
                console.error('Error registering download:', data.message);
                alert('Error: ' + data.message);
            } else {
                window.location.href = downloadUrl;
            }
        })
        .catch(function(error) { 
            console.error('Error:', error);
            alert('Error registering download');
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});