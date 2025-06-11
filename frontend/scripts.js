document.addEventListener("DOMContentLoaded", () => {
  const uploadForm = document.getElementById("uploadForm");
  const fileInput = document.getElementById("fileInput");
  const formatSelect = document.getElementById("formatSelect");
  const messageDiv = document.getElementById("responseContainer");
  const downloadLink = document.getElementById("downloadLink");
  const depthPreview = document.getElementById("depthPreview");
  const depthPreviewContainer = document.getElementById("depthPreviewContainer");
  const grayscalePreview = document.getElementById("grayscalePreview");
  const grayscalePreviewContainer = document.getElementById("grayscalePreviewContainer");
  const submitButton = uploadForm.querySelector("button[type='submit']");

  // Preview grayscale and depth map
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/preview-depthmap", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Failed to generate depth map preview");

      const result = await response.json();

      grayscalePreview.src = result.grayscale_url;
      grayscalePreviewContainer.classList.remove("hidden");

      depthPreview.src = result.depth_url;
      depthPreviewContainer.classList.remove("hidden");

    } catch (err) {
      console.error("Depth map preview error:", err.message);
      grayscalePreviewContainer.classList.add("hidden");
      depthPreviewContainer.classList.add("hidden");
    }
  });

  // Handle upload and export
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    const format = formatSelect.value;

    if (!file || !format) {
      messageDiv.innerHTML = `<p class="text-red-600">Please select a file and a format.</p>`;
      messageDiv.classList.remove("hidden");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    messageDiv.innerHTML = `<p class="text-blue-600">Uploading and processing file...</p>`;
    messageDiv.classList.remove("hidden");
    downloadLink.classList.add("hidden");
    submitButton.disabled = true;
    submitButton.textContent = "Processing...";

    try {
      const response = await fetch(`/upload-and-export/${format}/`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        messageDiv.innerHTML = `<p class="text-green-600 font-semibold">${result.message}</p>`;
        downloadLink.href = result.file;
        downloadLink.classList.remove("hidden");
      } else {
        throw new Error(result.detail || "Unknown error occurred.");
      }

    } catch (error) {
      messageDiv.innerHTML = `<p class="text-red-600">Error: ${error.message}</p>`;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Generate 3D Model";
    }
  });
});

