/**
 * LabStock AI - Main Frontend Utility & Interactive Operations Script
 * Handles navigation, modals, live table search/filtering, AJAX API requests,
 * and academic toast notifications.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Highlight active navigation link
    highlightActiveNavLink();

    // 2. Setup interactive table search and filters
    setupInventorySearchAndFilters();

    // 3. Setup modal close triggers
    setupModalTriggers();

    // 4. Setup form submissions
    setupFormHandlers();

    // 5. Setup anomaly resolution triggers
    setupAnomalyResolutions();
});

/**
 * Highlights current sidebar link based on URL path
 */
function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-link');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
            link.classList.add('active');
        } else if (currentPath === '/' && linkPath === '/') {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Toast Notification Utility
 * @param {string} title
 * @param {string} message
 * @param {string} type ('success', 'warning', 'danger', 'anomaly')
 * @param {number} duration in ms
 */
function showToast(title, message, type = 'success', duration = 4500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = '✓';
    if (type === 'warning') icon = '⚠';
    if (type === 'danger') icon = '✕';
    if (type === 'anomaly') icon = '🚨';

    toast.innerHTML = `
        <div style="font-size: 1.2rem; line-height: 1;">${icon}</div>
        <div style="flex: 1;">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

/**
 * Modal Dialog Open / Close Helpers
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function setupModalTriggers() {
    // Close modal when clicking outside modal-card
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(m => {
                m.classList.remove('active');
            });
            document.body.style.overflow = '';
        }
    });
}

/**
 * Real-Time Table Search and Filter for Inventory
 */
function setupInventorySearchAndFilters() {
    const searchInput = document.getElementById('inventorySearch');
    const deptFilter = document.getElementById('filterDepartment');
    const statusFilter = document.getElementById('filterStatus');
    const tableBody = document.getElementById('inventoryTableBody');
    const countBadge = document.getElementById('inventoryVisibleCount');

    if (!tableBody) return;

    function applyFilters() {
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const selectedDept = (deptFilter ? deptFilter.value : '').toLowerCase();
        const selectedStatus = (statusFilter ? statusFilter.value : '').toLowerCase();

        const rows = tableBody.querySelectorAll('tr[data-item-row]');
        let visibleCount = 0;

        rows.forEach(row => {
            const text = row.innerText.toLowerCase();
            const dept = (row.getAttribute('data-department') || '').toLowerCase();
            const status = (row.getAttribute('data-status') || '').toLowerCase();

            const matchesQuery = !query || text.includes(query);
            const matchesDept = !selectedDept || dept === selectedDept;
            const matchesStatus = !selectedStatus || status === selectedStatus;

            if (matchesQuery && matchesDept && matchesStatus) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        if (countBadge) {
            countBadge.innerText = `Showing ${visibleCount} of ${rows.length} items`;
        }
    }

    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (deptFilter) deptFilter.addEventListener('change', applyFilters);
    if (statusFilter) statusFilter.addEventListener('change', applyFilters);
}

/**
 * Open Modal Form Handlers for Issue & Restock
 */
function prepareIssueModal(itemId, itemName, itemCode, currentStock, unit) {
    const modal = document.getElementById('issueStockModal');
    if (!modal) return;

    document.getElementById('issueItemId').value = itemId;
    document.getElementById('issueItemNameDisplay').innerText = `${itemName} (${itemCode})`;
    document.getElementById('issueStockAvailableDisplay').innerText = `${currentStock} ${unit}`;
    
    const qtyInput = document.getElementById('issueQuantity');
    qtyInput.value = 1;
    qtyInput.max = currentStock;

    openModal('issueStockModal');
}

function prepareRestockModal(itemId, itemName, itemCode, currentStock, unit, batchNo, expiryDate) {
    const modal = document.getElementById('restockModal');
    if (!modal) return;

    document.getElementById('restockItemId').value = itemId;
    document.getElementById('restockItemNameDisplay').innerText = `${itemName} (${itemCode})`;
    document.getElementById('restockStockAvailableDisplay').innerText = `${currentStock} ${unit}`;
    
    const qtyInput = document.getElementById('restockQuantity');
    qtyInput.value = 10;
    document.getElementById('restockBatchNumber').value = batchNo || '';
    document.getElementById('restockExpiryDate').value = expiryDate || '';

    openModal('restockModal');
}

/**
 * Setup AJAX form submissions for Add Item, Issue, and Restock
 */
function setupFormHandlers() {
    // 1. Add Item Form
    const addItemForm = document.getElementById('addItemForm');
    if (addItemForm) {
        addItemForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Registering...';

            const payload = {
                name: document.getElementById('addItemName').value,
                item_code: document.getElementById('addItemCode').value,
                category_id: document.getElementById('addItemCategory').value,
                lab_name: document.getElementById('addItemLabName').value,
                quantity: document.getElementById('addItemQuantity').value,
                unit: document.getElementById('addItemUnit').value,
                minimum_threshold: document.getElementById('addItemThreshold').value,
                unit_cost: document.getElementById('addItemUnitCost').value,
                storage_location: document.getElementById('addItemLocation').value,
                supplier_id: document.getElementById('addItemSupplier').value || null,
                batch_number: document.getElementById('addItemBatch').value || null,
                expiry_date: document.getElementById('addItemExpiry').value || null
            };

            fetch('/api/items', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Save Item';

                if (data.success) {
                    showToast('Item Catalogued', data.message, 'success');
                    closeModal('addItemModal');
                    setTimeout(() => window.location.reload(), 900);
                } else {
                    showToast('Registration Error', data.error || 'Failed to add item.', 'danger');
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Save Item';
                showToast('Network Error', 'Could not connect to the server.', 'danger');
            });
        });
    }

    // 2. Issue Stock Form
    const issueForm = document.getElementById('issueStockForm');
    if (issueForm) {
        issueForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Processing Issue...';

            const itemId = document.getElementById('issueItemId').value;
            const payload = {
                quantity: document.getElementById('issueQuantity').value,
                issued_to: document.getElementById('issueIssuedTo').value,
                purpose: document.getElementById('issuePurpose').value
            };

            fetch(`/api/items/${itemId}/issue`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Confirm Stock Issue';

                if (data.success) {
                    showToast('Stock Issued', data.message, 'success');
                    closeModal('issueStockModal');

                    // If real-time AI anomaly detected, show prominent warning toast
                    if (data.anomaly_detected && data.anomaly) {
                        setTimeout(() => {
                            showToast(
                                '🚨 AI Anomaly Detected!',
                                `Severity: ${data.anomaly.severity}. ${data.anomaly.reason}`,
                                'anomaly',
                                8000
                            );
                        }, 500);
                    }

                    setTimeout(() => window.location.reload(), 1400);
                } else {
                    showToast('Issue Failed', data.error || 'Cannot issue stock.', 'danger');
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Confirm Stock Issue';
                showToast('Error', 'Failed to process issue transaction.', 'danger');
            });
        });
    }

    // 3. Restock Form
    const restockForm = document.getElementById('restockForm');
    if (restockForm) {
        restockForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Adding Stock...';

            const itemId = document.getElementById('restockItemId').value;
            const payload = {
                quantity: document.getElementById('restockQuantity').value,
                supplier_name: document.getElementById('restockSupplierName').value,
                batch_number: document.getElementById('restockBatchNumber').value,
                expiry_date: document.getElementById('restockExpiryDate').value,
                notes: document.getElementById('restockNotes').value
            };

            fetch(`/api/items/${itemId}/restock`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Confirm Restock';

                if (data.success) {
                    showToast('Stock Replenished', data.message, 'success');
                    closeModal('restockModal');
                    setTimeout(() => window.location.reload(), 900);
                } else {
                    showToast('Restock Error', data.error || 'Cannot restock item.', 'danger');
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Confirm Restock';
                showToast('Error', 'Failed to process restock transaction.', 'danger');
            });
        });
    }
}

/**
 * Setup Anomaly Resolution Click Handlers
 */
function setupAnomalyResolutions() {
    document.querySelectorAll('.btn-action-resolve').forEach(btn => {
        btn.addEventListener('click', function () {
            const anomalyId = this.getAttribute('data-anomaly-id');
            if (!anomalyId) return;

            if (!confirm('Mark this anomaly as reviewed and resolved?')) return;

            this.disabled = true;
            this.innerText = 'Resolving...';

            fetch(`/api/anomalies/${anomalyId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('Anomaly Resolved', 'Record flagged as resolved.', 'success');
                    const row = this.closest('tr');
                    if (row) {
                        row.style.opacity = '0.3';
                        this.innerText = 'Resolved';
                    }
                } else {
                    this.disabled = false;
                    this.innerText = 'Resolve';
                    showToast('Error', data.error || 'Failed to resolve anomaly.', 'danger');
                }
            })
            .catch(err => {
                this.disabled = false;
                this.innerText = 'Resolve';
                showToast('Error', 'Network error.', 'danger');
            });
        });
    });
}
