/* PO Workspace — vanilla JS for progress polling and story review. */

/* Poll the session status endpoint and update the progress step list. */
function pollSessionStatus(sessionId, intervalMs) {
  const tick = function () {
    fetch("/sessions/" + sessionId + "/status")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        updateSteps(data);
        if (data.status === "awaiting_review") {
          window.location.href = "/sessions/" + sessionId + "/review";
          return;
        }
        if (data.status === "error") {
          showError(data.error || "The pipeline failed.");
          return;
        }
        setTimeout(tick, intervalMs);
      })
      .catch(function () { setTimeout(tick, intervalMs); });
  };
  tick();
}

function updateSteps(data) {
  const completed = data.completed_nodes || [];
  const current = data.current_node;
  const items = document.querySelectorAll("#progress-steps li[data-node]");
  items.forEach(function (li) {
    const node = li.getAttribute("data-node");
    const icon = li.querySelector(".step-icon");
    if (completed.indexOf(node) !== -1 && node !== current) {
      icon.textContent = "✓";
      icon.style.color = "var(--green)";
    } else if (node === current) {
      icon.textContent = "●";
      icon.style.color = "var(--amber)";
    } else {
      icon.textContent = "○";
      icon.style.color = "var(--gray)";
    }
  });
}

function showError(message) {
  const box = document.getElementById("error-box");
  const msg = document.getElementById("error-message");
  if (box && msg) {
    msg.textContent = message;
    box.style.display = "block";
  }
}

/* Review page: manage approve/edit/remove state across story cards. */
function initReviewPage(sessionId) {
  const approved = new Set();
  const removed = new Set();
  const edits = {};

  const cards = Array.prototype.slice.call(document.querySelectorAll(".story-card"));
  const total = cards.length;

  function refreshCounter() {
    const counter = document.getElementById("approve-counter");
    const submit = document.getElementById("btn-submit");
    counter.textContent = approved.size + " of " + total + " stories approved";
    submit.disabled = approved.size === 0;
  }

  cards.forEach(function (card) {
    const id = card.getAttribute("data-story-id");

    card.querySelector(".btn-approve").addEventListener("click", function () {
      approved.add(id);
      card.style.borderColor = "var(--green)";
      refreshCounter();
    });

    card.querySelector(".btn-remove").addEventListener("click", function () {
      approved.delete(id);
      removed.add(id);
      card.style.opacity = "0.4";
      card.style.textDecoration = "line-through";
      refreshCounter();
    });

    const editForm = card.querySelector(".edit-form");
    card.querySelector(".btn-edit").addEventListener("click", function () {
      editForm.style.display = editForm.style.display === "none" ? "block" : "none";
    });

    card.querySelector(".btn-save").addEventListener("click", function () {
      edits[id] = {
        title: card.querySelector(".edit-title").value,
        description: card.querySelector(".edit-description").value,
        given: card.querySelector(".edit-given").value,
        when: card.querySelector(".edit-when").value,
        then: card.querySelector(".edit-then").value
      };
      card.querySelector(".story-title").textContent = edits[id].title;
      card.querySelector(".story-description").textContent = edits[id].description;
      editForm.style.display = "none";
    });
  });

  document.getElementById("btn-approve-all").addEventListener("click", function () {
    cards.forEach(function (card) {
      const id = card.getAttribute("data-story-id");
      if (!removed.has(id)) {
        approved.add(id);
        card.style.borderColor = "var(--green)";
      }
    });
    refreshCounter();
  });

  document.getElementById("btn-submit").addEventListener("click", function () {
    submitApprovedStories(sessionId, approved, edits);
  });

  const rejectModal = document.getElementById("reject-modal");
  document.getElementById("btn-reject").addEventListener("click", function () {
    rejectModal.style.display = "block";
  });
  document.getElementById("btn-cancel-reject").addEventListener("click", function () {
    rejectModal.style.display = "none";
  });
  document.getElementById("btn-confirm-reject").addEventListener("click", function () {
    submitRejection(sessionId);
  });

  refreshCounter();
}

/* Collect approved stories (with edits applied) and POST them. */
function submitApprovedStories(sessionId, approvedSet, edits) {
  const stories = [];
  document.querySelectorAll(".story-card").forEach(function (card) {
    const id = card.getAttribute("data-story-id");
    if (!approvedSet.has(id)) { return; }
    const story = { id: id };
    story.title = card.querySelector(".story-title").textContent;
    story.description = card.querySelector(".story-description").textContent;
    if (edits[id]) {
      const ac = [edits[id].given, edits[id].when, edits[id].then].filter(Boolean);
      if (ac.length) { story.acceptance_criteria = ac; }
    }
    stories.push(story);
  });

  fetch("/sessions/" + sessionId + "/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved_stories: stories, feedback: null })
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.redirect) { window.location.href = data.redirect; }
    });
}

/* POST rejection feedback and follow the redirect. */
function submitRejection(sessionId) {
  const feedback = document.getElementById("reject-feedback").value;
  fetch("/sessions/" + sessionId + "/reject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback: feedback })
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.redirect) { window.location.href = data.redirect; }
    });
}
