// --- Health check ---
async function checkHealth() {
  const dot = document.getElementById("vllm-dot");
  const text = document.getElementById("vllm-status-text");
  try {
    const resp = await fetch("/health");
    const data = await resp.json();
    if (data.vllm && data.vllm.status === "healthy") {
      dot.className = "dot green";
      text.textContent = "vLLM is running";
    } else {
      dot.className = "dot red";
      text.textContent = "vLLM is not reachable — start it to enable analysis";
    }
  } catch {
    dot.className = "dot red";
    text.textContent = "App server error";
  }
}

// --- File upload ---
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const analyzeBtn = document.getElementById("analyze-btn");
const uploadStatus = document.getElementById("upload-status");
const progressBar = document.getElementById("progress-bar");
const progressFill = document.getElementById("progress-fill");
let selectedFile = null;

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) {
    selectedFile = e.dataTransfer.files[0];
    onFileSelected();
  }
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) {
    selectedFile = fileInput.files[0];
    onFileSelected();
  }
});

function onFileSelected() {
  uploadStatus.textContent = `Selected: ${selectedFile.name} (${(selectedFile.size / 1048576).toFixed(1)} MB)`;
  analyzeBtn.disabled = false;
}

document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  analyzeBtn.disabled = true;
  progressBar.hidden = false;
  progressFill.style.width = "10%";
  uploadStatus.textContent = "Uploading and analyzing...";

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    progressFill.style.width = "30%";
    const resp = await fetch("/api/analyze", { method: "POST", body: formData });
    progressFill.style.width = "90%";

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Analysis failed");
    }
    const result = await resp.json();
    progressFill.style.width = "100%";

    if (result.analysis) {
      uploadStatus.textContent = `Done! Virality score: ${result.analysis.virality_score}/10`;
    } else {
      uploadStatus.textContent = "Done (model returned unstructured response)";
    }

    // Reload to show updated results
    setTimeout(() => location.reload(), 1500);
  } catch (err) {
    uploadStatus.textContent = `Error: ${err.message}`;
    progressFill.style.width = "0%";
    analyzeBtn.disabled = false;
  }
});

// Run health check on load
checkHealth();
// Re-check every 30s
setInterval(checkHealth, 30000);
