const predictForm = document.querySelector("#predict-form");
const fileInput = document.querySelector("#image-file");
const formMessage = document.querySelector("#form-message");
const predictionId = document.querySelector("#prediction-id");
const resultSummary = document.querySelector("#result-summary");
const predictionRows = document.querySelector("#prediction-rows");
const classCards = document.querySelector("#class-cards");
const retrainButton = document.querySelector("#retrain-button");
const latestRetrainingStatus = document.querySelector("#latest-retraining-status");
const latestRetrainingMessage = document.querySelector("#latest-retraining-message");
const retrainingJobRows = document.querySelector("#retraining-job-rows");
const driftAlert = document.querySelector("#drift-alert");
const imageCanvas = document.querySelector("#image-canvas");
const previewPlaceholder = document.querySelector("#preview-placeholder");
const canvasContext = imageCanvas?.getContext("2d");
const translations = window.DD_TRANSLATIONS || {};
let selectedImage = null;

const classColors = {
  1: "rgba(220, 38, 38, 0.58)",
  2: "rgba(37, 99, 235, 0.58)",
  3: "rgba(22, 163, 74, 0.58)",
  4: "rgba(202, 138, 4, 0.58)",
};

const statusElements = {
  data_drift: document.querySelector("#data-drift-status"),
  target_drift: document.querySelector("#target-drift-status"),
  concept_drift: document.querySelector("#concept-drift-status"),
};

function translate(key) {
  return translations[key] || key;
}

function setMessage(text) {
  formMessage.textContent = text;
}

function renderPrediction(payload) {
  const defectClasses = payload.predictions
    .filter((item) => item.has_defect)
    .map((item) => item.class_id);

  predictionId.textContent = payload.prediction_id;
  resultSummary.textContent = defectClasses.length
    ? `${translate("defect_found")}: ${defectClasses.join(", ")}`
    : translate("no_prediction");

  classCards.innerHTML = payload.predictions
    .map(
      (item) => `
        <div class="class-card ${item.has_defect ? "active" : ""}">
          <span class="class-dot" style="background: ${classColors[item.class_id]}"></span>
          <strong>${translate("class_label")} ${item.class_id}</strong>
          <span>${item.has_defect ? translate("defect_found") : translate("clean")}</span>
          <span class="mono">${item.area_pixels} px</span>
        </div>
      `,
    )
    .join("");

  predictionRows.innerHTML = payload.predictions
    .map(
      (item) => `
        <tr>
          <td>${item.class_id}</td>
          <td>
            <span class="status-pill ${item.has_defect ? "warning" : "ok"}">
              ${item.has_defect ? translate("defect_yes") : translate("defect_no")}
            </span>
          </td>
          <td>${item.area_pixels}</td>
        </tr>
      `,
    )
    .join("");

  drawOverlay(payload);
}

function updateStatusPill(element, status) {
  if (!element) {
    return;
  }

  element.textContent = translate(`status_${status}`);
  element.className = `status-pill ${status}`;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString();
}

function renderRetrainingJobs(jobs) {
  if (!retrainingJobRows || !latestRetrainingStatus || !latestRetrainingMessage) {
    return;
  }

  if (!jobs.length) {
    latestRetrainingStatus.textContent = translate("status_no_data");
    latestRetrainingStatus.className = "status-pill neutral";
    latestRetrainingMessage.textContent = translate("no_retraining_jobs_yet");
    retrainingJobRows.innerHTML = `
      <tr>
        <td colspan="3" class="empty">${translate("no_retraining_jobs_yet")}</td>
      </tr>
    `;
    return;
  }

  const latestJob = jobs[0];
  updateStatusPill(latestRetrainingStatus, latestJob.status);
  latestRetrainingMessage.textContent = latestJob.message || "-";
  retrainingJobRows.innerHTML = jobs
    .map((job) => {
      const mlflowLink = job.mlflow_run_url
        ? `<a href="${job.mlflow_run_url}" target="_blank" rel="noreferrer">${translate("open_mlflow_run")}</a>`
        : "-";

      return `
        <tr>
          <td>${formatDateTime(job.created_at)}</td>
          <td>
            <span class="status-pill ${job.status}">
              ${translate(`status_${job.status}`)}
            </span>
          </td>
          <td>${mlflowLink}</td>
        </tr>
      `;
    })
    .join("");
}

async function refreshRetrainingJobs() {
  if (!retrainingJobRows) {
    return;
  }

  const response = await fetch("/retrain/jobs");

  if (!response.ok) {
    return;
  }

  const payload = await response.json();
  renderRetrainingJobs(payload.items || []);
}

async function refreshDriftStatus() {
  const response = await fetch("/drift/status");

  if (!response.ok) {
    return;
  }

  const status = await response.json();
  const statuses = {
    data_drift: status.data_drift.status,
    target_drift: status.target_drift.status,
    concept_drift: status.concept_drift.status,
  };

  Object.entries(statuses).forEach(([key, value]) => {
    updateStatusPill(statusElements[key], value);
  });

  const warnings = Object.entries(statuses)
    .filter(([, value]) => value === "warning")
    .map(([key]) => translate(key));

  if (warnings.length) {
    driftAlert.textContent = `${translate("drift_warning")}: ${warnings.join(", ")}`;
    driftAlert.classList.remove("hidden");
  } else {
    driftAlert.classList.add("hidden");
  }
}

function loadSelectedImage(file) {
  if (!file || !imageCanvas || !canvasContext) {
    return;
  }

  selectedImage = new Image();
  selectedImage.onload = () => {
    const width = selectedImage.naturalWidth || 1600;
    const height = selectedImage.naturalHeight || 256;
    imageCanvas.width = width;
    imageCanvas.height = height;
    canvasContext.clearRect(0, 0, width, height);
    canvasContext.drawImage(selectedImage, 0, 0, width, height);
    previewPlaceholder.classList.add("hidden");
  };
  selectedImage.src = URL.createObjectURL(file);
}

function drawOverlay(payload) {
  if (!selectedImage || !imageCanvas || !canvasContext) {
    return;
  }

  const maskHeight = payload.tensor_shape[2];
  const maskWidth = payload.tensor_shape[3];

  imageCanvas.width = maskWidth;
  imageCanvas.height = maskHeight;
  canvasContext.clearRect(0, 0, maskWidth, maskHeight);
  canvasContext.drawImage(selectedImage, 0, 0, maskWidth, maskHeight);

  payload.predictions
    .filter((item) => item.has_defect && item.rle)
    .forEach((item) => {
      drawRleMask(item.rle, maskWidth, maskHeight, classColors[item.class_id]);
    });
}

function drawRleMask(rle, width, height, color) {
  const runs = rle.split(" ").map(Number);
  canvasContext.fillStyle = color;

  for (let index = 0; index < runs.length; index += 2) {
    const start = runs[index] - 1;
    const length = runs[index + 1];

    for (let offset = 0; offset < length; offset += 1) {
      const position = start + offset;
      const x = Math.floor(position / height);
      const y = position % height;
      canvasContext.fillRect(x, y, 1, 1);
    }
  }
}

fileInput?.addEventListener("change", () => {
  loadSelectedImage(fileInput.files[0]);
});

predictForm?.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    setMessage(translate("select_image_first"));
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  setMessage(translate("running_inference"));

  const response = await fetch("/predict", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorPayload = await response.json();
    setMessage(errorPayload.detail || translate("prediction_failed"));
    return;
  }

  const payload = await response.json();
  renderPrediction(payload);
  setMessage(translate("prediction_complete"));
  await refreshDriftStatus();
});

async function refreshRetrainingStatus(jobId) {
  const response = await fetch(`/retrain/status/${jobId}`);

  if (!response.ok) {
    retrainButton.textContent = translate("run_retraining");
    retrainButton.disabled = false;
    setMessage(translate("retraining_status_failed"));
    return;
  }

  const payload = await response.json();
  retrainButton.textContent = `${translate("retraining_status")}: ${translate(`status_${payload.status}`)}`;
  await refreshRetrainingJobs();

  if (payload.status === "succeeded") {
    retrainButton.textContent = translate("run_retraining");
    retrainButton.disabled = false;
    setMessage(translate("retraining_succeeded"));
    return;
  }

  if (payload.status === "failed") {
    retrainButton.textContent = translate("run_retraining");
    retrainButton.disabled = false;
    setMessage(payload.message || translate("retraining_failed"));
    return;
  }

  window.setTimeout(() => {
    refreshRetrainingStatus(jobId);
  }, 1000);
}

retrainButton?.addEventListener("click", async () => {
  retrainButton.disabled = true;
  retrainButton.textContent = translate("status_queued");
  setMessage(translate("retraining_started"));

  const response = await fetch("/retrain", {
    method: "POST",
  });

  if (!response.ok) {
    retrainButton.textContent = translate("run_retraining");
    retrainButton.disabled = false;
    setMessage(translate("retraining_failed"));
    return;
  }

  const payload = await response.json();
  await refreshRetrainingJobs();
  await refreshRetrainingStatus(payload.job_id);
});

refreshDriftStatus();
refreshRetrainingJobs();
