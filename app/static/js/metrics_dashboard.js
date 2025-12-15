document.addEventListener("DOMContentLoaded", () => {
  fetch("/profile/metrics")
    .then(res => res.json())
    .then(data => {
      document.getElementById("uploaded").textContent = data.uploaded_datasets;
      document.getElementById("downloads").textContent = data.downloads;
      document.getElementById("syncs").textContent = data.synchronizations;
    })
    .catch(err => console.error("Error loading metrics:", err));
});
