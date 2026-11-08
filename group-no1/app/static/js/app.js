/**
 * Group No1 — Global Lost & Found Management System
 * Interactive Client Script
 * Handles modal popups, multi-file previews, dynamic search, and mobile navigation.
 */

document.addEventListener("DOMContentLoaded", () => {
    initMobileNav();
    initAlerts();
    initModalHandlers();
    initUnreadNotificationsPolling();
});

/* ==========================================================================
   Mobile Navigation Toggle
   ========================================================================== */
function initMobileNav() {
    const toggle = document.querySelector(".nav-toggle");
    const navLinks = document.querySelector(".nav-links");

    if (toggle && navLinks) {
        toggle.addEventListener("click", () => {
            const isExpanded = navLinks.classList.toggle("active");
            toggle.setAttribute("aria-expanded", isExpanded);
        });
    }
}

/* ==========================================================================
   Alerts Management
   ========================================================================== */
function initAlerts() {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        // Auto dismiss after 6 seconds if not manually closed
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = "0";
                alert.style.transform = "translateY(-10px)";
                alert.style.transition = "all 0.3s ease";
                setTimeout(() => alert.remove(), 300);
            }
        }, 6000);
    });
}

function dismissAlert(button) {
    const alert = button.closest(".alert");
    if (alert) {
        alert.remove();
    }
}

/* ==========================================================================
   Image Preview with Client-Side Management
   ========================================================================== */
// DataTransfer object to manage selected files for removal before submit
let selectedFilesList = [];

function previewImages(input) {
    const previewContainer = document.getElementById("imagePreview");
    if (!previewContainer) return;

    previewContainer.innerHTML = "";
    selectedFilesList = Array.from(input.files || []);

    if (selectedFilesList.length === 0) return;

    selectedFilesList.forEach((file, index) => {
        if (!file.type.startsWith("image/")) {
            showAlert("Only image files (PNG, JPG, JPEG, GIF, WEBP) are allowed.", "error");
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const wrap = document.createElement("div");
            wrap.className = "preview-thumb-wrap";
            wrap.dataset.index = index;

            const img = document.createElement("img");
            img.src = e.target.result;
            img.alt = file.name;

            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "preview-remove-btn";
            removeBtn.innerHTML = "&times;";
            removeBtn.title = "Remove image";
            removeBtn.onclick = () => removeSelectedFile(index, input);

            wrap.appendChild(img);
            wrap.appendChild(removeBtn);
            previewContainer.appendChild(wrap);
        };
        reader.readAsDataURL(file);
    });
}

function removeSelectedFile(indexToRemove, inputElement) {
    selectedFilesList = selectedFilesList.filter((_, idx) => idx !== indexToRemove);

    // Sync files back to input using DataTransfer
    const dt = new DataTransfer();
    selectedFilesList.forEach((file) => dt.items.add(file));
    inputElement.files = dt.files;

    // Refresh previews
    previewImages(inputElement);
}

/* ==========================================================================
   Item Detail Modal
   ========================================================================== */
function openItemModal(itemId) {
    const modal = document.getElementById("itemModal");
    const modalBody = document.getElementById("modalBody");
    if (!modal || !modalBody) return;

    // Show loading indicator
    modalBody.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⏳</div>
            <p style="color: #64748b;">Loading item details...</p>
        </div>
    `;
    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";

    // Fetch details from API
    fetch(`/api/items/${itemId}`)
        .then((res) => {
            if (!res.ok) throw new Error("Item not found or unavailable.");
            return res.json();
        })
        .then((item) => {
            renderModalItemDetails(item);
        })
        .catch((err) => {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 2rem 1rem;">
                    <p style="color: #e53e3e; font-weight: 600; margin-bottom: 1rem;">${err.message}</p>
                    <button class="btn btn-secondary btn-sm" onclick="closeModal()">Close</button>
                </div>
            `;
        });
}

function renderModalItemDetails(item) {
    const modalBody = document.getElementById("modalBody");
    if (!modalBody) return;

    // Safe string escaping helper
    const escapeHtml = (str) => {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    modalBody.innerHTML = `
        <div style="margin-bottom: 1.2rem;">
            <img src="${item.image_url}" alt="${escapeHtml(item.name)}" 
                 style="width: 100%; max-height: 320px; object-fit: cover; border-radius: 12px;">
        </div>

        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.8rem;">
            <h2 style="color: #667eea; font-size: 1.6rem; margin: 0;">${escapeHtml(item.name)}</h2>
            <span class="badge badge-status-${item.status}">${escapeHtml(item.status_label)}</span>
        </div>

        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;">
            <span class="badge">📁 ${escapeHtml(item.category)}</span>
            <span class="badge">📍 ${escapeHtml(item.location)}</span>
            <span class="badge">📅 ${escapeHtml(item.date_found)}</span>
            <span class="badge badge-finder">👤 Found by ${escapeHtml(item.finder_name)}</span>
        </div>

        <div style="margin: 1.2rem 0; padding: 1rem; background: #f8fafc; border-radius: 10px; border-left: 4px solid #667eea;">
            <h4 style="color: #334155; margin-bottom: 0.4rem; font-size: 0.95rem;">Public Description</h4>
            <p style="color: #475569; font-size: 0.95rem; white-space: pre-wrap;">${escapeHtml(item.description)}</p>
        </div>

        <div style="display: flex; gap: 1rem; margin-top: 1.5rem; flex-wrap: wrap;">
            <a href="/items/${item.id}" class="btn btn-secondary" style="flex: 1;">
                Full Details Page
            </a>
            <a href="/items/${item.id}/claim" class="btn btn-primary" style="flex: 2;">
                Claim This Item
            </a>
        </div>
    `;
}

function closeModal() {
    const modal = document.getElementById("itemModal");
    if (modal) {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    }
}

function initModalHandlers() {
    // Backdrop click
    window.addEventListener("click", (e) => {
        const modal = document.getElementById("itemModal");
        if (e.target === modal) {
            closeModal();
        }
    });

    // Escape key
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeModal();
        }
    });
}

/* ==========================================================================
   Unread Notifications Dynamic Badge
   ========================================================================== */
function initUnreadNotificationsPolling() {
    const badge = document.getElementById("navNotificationBadge");
    if (!badge) return;

    function fetchCount() {
        fetch("/api/notifications/unread-count")
            .then((res) => {
                if (res.ok) return res.json();
                return null;
            })
            .then((data) => {
                if (data && typeof data.unread_count === "number") {
                    if (data.unread_count > 0) {
                        badge.textContent = data.unread_count;
                        badge.style.display = "inline-block";
                    } else {
                        badge.style.display = "none";
                    }
                }
            })
            .catch(() => {});
    }

    // Fetch immediately and poll every 60 seconds
    fetchCount();
    setInterval(fetchCount, 60000);
}

/* ==========================================================================
   Toast / Dynamic Alert Helper
   ========================================================================== */
function showAlert(message, type = "info") {
    let container = document.getElementById("flashContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "flashContainer";
        document.querySelector(".container").prepend(container);
    }

    const alert = document.createElement("div");
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
        <button class="alert-close" onclick="dismissAlert(this)">&times;</button>
    `;
    container.appendChild(alert);

    setTimeout(() => {
        if (alert && alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}
