// UX interface — vanilla JS for progress polling, tabbed review, approve/reject.

function pollSessionStatus(sessionId, intervalMs) {
  const interval = intervalMs || 1500;
  const tick = () => {
    fetch(`/sessions/${sessionId}/status`)
      .then((r) => r.json())
      .then((data) => {
        updateSteps(data.completed_nodes || [], data.current_node);
        if (data.status === "awaiting_review") {
          window.location.href = `/sessions/${sessionId}/review`;
        } else if (data.status === "error") {
          const el = document.getElementById("error-box");
          if (el) {
            el.style.display = "block";
            el.textContent = "Error: " + (data.error || "unknown");
          }
        } else {
          setTimeout(tick, interval);
        }
      })
      .catch(() => setTimeout(tick, interval));
  };
  tick();
}

function updateSteps(completed, current) {
  document.querySelectorAll("[data-node]").forEach((li) => {
    const node = li.getAttribute("data-node");
    li.classList.remove("active", "done");
    if (completed.includes(node)) {
      li.classList.add("done");
    } else if (node === current) {
      li.classList.add("active");
    }
  });
}

function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  if (!buttons.length) return;
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const panel = document.querySelector(`[data-panel="${tab}"]`);
      if (panel) panel.classList.add("active");
    });
  });
}

function initReviewPage(sessionId) {
  const approveBtn = document.getElementById("approve-btn");
  if (approveBtn) {
    approveBtn.addEventListener("click", () => submitApproved(sessionId));
  }
  const rejectBtn = document.getElementById("reject-btn");
  if (rejectBtn) {
    rejectBtn.addEventListener("click", () => {
      document.getElementById("reject-box").style.display = "block";
    });
  }
  const submitReject = document.getElementById("submit-reject");
  if (submitReject) {
    submitReject.addEventListener("click", () => submitRejection(sessionId));
  }
}

function submitApproved(sessionId) {
  fetch(`/sessions/${sessionId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.redirect) window.location.href = data.redirect;
    });
}

function submitRejection(sessionId) {
  const feedback = document.getElementById("feedback").value;
  fetch(`/sessions/${sessionId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback: feedback }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.redirect) window.location.href = data.redirect;
    });
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  const review = document.querySelector("[data-review-session]");
  if (review) initReviewPage(review.getAttribute("data-review-session"));
  const progress = document.querySelector("[data-progress-session]");
  if (progress) pollSessionStatus(progress.getAttribute("data-progress-session"));
});
