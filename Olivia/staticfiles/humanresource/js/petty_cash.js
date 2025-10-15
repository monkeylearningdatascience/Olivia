document.addEventListener('DOMContentLoaded', function () {

    // ===== Helper Function to Get CSRF Token =====
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(function (cookie) {
                const c = cookie.trim();
                if (c.startsWith(name + '=')) cookieValue = decodeURIComponent(c.substring(name.length + 1));
            });
        }
        return cookieValue;
    }

    // ===== Helper function to find the single selected row =====
    function getSelectedRow() {
        const selectedCheckboxes = document.querySelectorAll('.select-entry:checked');
        if (selectedCheckboxes.length === 1) {
            return selectedCheckboxes[0].closest('tr');
        }
        return null;
    }

    // ===== Helper function to display the selection modal dynamically =====
    function showUpdateSelectionModal(action) {
        const modalElement = document.getElementById('updateSelectionModal');
        const modalTitle = document.getElementById('updateSelectionModalLabel');
        const modalBody = document.getElementById('updateSelectionModalBody');
        const modalHeader = document.getElementById('updateSelectionModalHeader');
        const modalOkBtn = document.getElementById('updateSelectionModalOkBtn');

        modalHeader.classList.remove('bg-dark', 'bg-primary', 'bg-danger');
        modalOkBtn.classList.remove('btn-dark', 'btn-primary', 'btn-danger');

        let titleText = 'Invalid Selection';
        let bodyText = '';

        if (action === 'view') {
            titleText = 'View Entry';
            bodyText = 'Please select exactly one record to view.';
            modalHeader.classList.add('bg-dark');
            modalOkBtn.classList.add('btn-dark');
        } else if (action === 'edit') {
            titleText = 'Edit Entry';
            bodyText = 'Please select exactly one record to edit.';
            modalHeader.classList.add('bg-primary');
            modalOkBtn.classList.add('btn-primary');
        } else if (action === 'delete') {
            titleText = 'Delete Entry';
            bodyText = 'Please select at least one record to delete.';
            modalHeader.classList.add('bg-danger');
            modalOkBtn.classList.add('btn-danger');
        }

        modalTitle.innerText = titleText;
        modalBody.innerText = bodyText;

        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }

    // ===== Auto Total Calculation in Add/Edit Cash Modal =====
    const amountInput = document.querySelector('#id_amount');
    const vatInput = document.querySelector('#id_vat');
    const dutyInput = document.querySelector('#id_import_duty');
    const discountInput = document.querySelector('#id_discount');
    const totalInput = document.querySelector('#id_total');

    if (amountInput && vatInput && dutyInput && discountInput && totalInput) {
        function calculateTotal() {
            const amount = parseFloat(amountInput.value) || 0;
            const vat = parseFloat(vatInput.value) || 0;
            const duty = parseFloat(dutyInput.value) || 0;
            const discount = parseFloat(discountInput.value) || 0;

            if (!totalInput.dataset.userEdited) {
                totalInput.value = (amount + vat + duty - discount).toFixed(2);
            }
        }
        [amountInput, vatInput, dutyInput, discountInput].forEach(input => {
            input.addEventListener('input', calculateTotal);
        });

        totalInput.addEventListener('input', function () {
            totalInput.dataset.userEdited = 'true';
        });
    }

    // ===== Calculate total from submitted entries =====
    const activitySelect = document.getElementById('activity');
    const formAmountInput = document.getElementById('id_amount');

    if (activitySelect && formAmountInput) {
        activitySelect.addEventListener('change', function () {
            if (this.value === 'submitted') {
                fetch('/humanresource/get_submitted_total/')
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        formAmountInput.value = data.total;
                        formAmountInput.disabled = true;
                    })
                    .catch(error => {
                        console.error('Error fetching submitted total:', error);
                        formAmountInput.value = '0.00';
                        alert('An error occurred while fetching the total. Please try again.');
                    });
            } else {
                formAmountInput.value = '';
                formAmountInput.disabled = false;
            }
        });
    }


    // ===== Add/Edit Form Submission Logic 🚀 =====
    const cashForm = document.getElementById('cashForm');
    if (cashForm) {
        cashForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const cashModalEl = document.getElementById('cashModal');
            const cashModal = bootstrap.Modal.getInstance(cashModalEl);
            const formData = new FormData(this);
            const actionUrl = this.action;

            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            })
                .then(response => {
                    if (response.ok) {
                        if (cashModal) {
                            cashModal.hide();
                        }
                        location.reload();
                    } else {
                        return response.json().then(data => {
                            console.error('Submission failed:', data);
                            alert('Submission failed. Check the console for details.');
                        });
                    }
                })
                .catch(error => {
                    console.error('Error during fetch:', error);
                    alert('An error occurred. Please try again later.');
                });
        });
    }

    // ===== Select All Checkboxes =====
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function () {
            document.querySelectorAll('.select-entry').forEach(cb => cb.checked = selectAll.checked);
        });
    }

    // ===== Delete Selected Rows with Bootstrap Modal =====
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    let selectedIds = [];

    if (deleteSelectedBtn && confirmDeleteBtn) {
        deleteSelectedBtn.addEventListener('click', function () {
            selectedIds = Array.from(document.querySelectorAll('.select-entry:checked')).map(cb => cb.value);

            if (!selectedIds.length) {
                showUpdateSelectionModal('delete');
                return;
            }
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
            deleteModal.show();
        });

        confirmDeleteBtn.addEventListener('click', function () {
            if (!selectedIds.length) return;

            fetch('/humanresource/petty-cash/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: new URLSearchParams(selectedIds.map(id => ['selected_ids', id]))
            })
                .then(() => {
                    const deleteModalEl = document.getElementById('deleteConfirmModal');
                    const deleteModal = bootstrap.Modal.getInstance(deleteModalEl);
                    deleteModal.hide();
                    location.reload();
                })
                .catch(err => console.error(err));
        });
    }

    // ===== View Selected Attachment (Top Button) =====
    const viewBtn = document.getElementById('viewBtn');
    if (viewBtn) {
        viewBtn.addEventListener('click', function () {
            const selectedRow = getSelectedRow();
            if (!selectedRow) {
                showUpdateSelectionModal('view');
                return;
            }

            const attachmentUrl = selectedRow.dataset.attachment;
            if (attachmentUrl && attachmentUrl.trim() !== "") {
                window.open(attachmentUrl, '_blank');
            } else {
                alert('No attachment available for this record.');
            }
        });
    }

    // ===== Update Selected Record (Top Button) =====
    const updateBtn = document.getElementById('updateBtn');
    if (updateBtn) {
        updateBtn.addEventListener('click', function () {
            const selectedRow = getSelectedRow();
            if (!selectedRow) {
                showUpdateSelectionModal('edit');
                return;
            }

            document.getElementById('cash_id').value = selectedRow.dataset.id || '';
            document.getElementById('id_date').value = selectedRow.dataset.date || '';
            document.getElementById('id_supplier_name').value = selectedRow.dataset.supplier || '';
            document.getElementById('id_department').value = selectedRow.dataset.department || '';
            document.getElementById('id_project_name').value = selectedRow.dataset.project || '';
            document.getElementById('id_item_description').value = selectedRow.dataset.item || '';
            document.getElementById('id_invoice_number').value = selectedRow.dataset.invoice || '';
            document.getElementById('id_amount').value = selectedRow.dataset.amount || '';
            document.getElementById('id_vat').value = selectedRow.dataset.vat || '';
            document.getElementById('id_import_duty').value = selectedRow.dataset.duty || '';
            document.getElementById('id_discount').value = selectedRow.dataset.discount || '';

            const totalInput = document.getElementById('id_total');
            if (totalInput) {
                totalInput.value = selectedRow.dataset.total || '';
                delete totalInput.dataset.userEdited;
            }

            document.getElementById('cashModalLabel').innerText = 'Edit Petty Cash Entry';
            document.getElementById('cashSubmitBtn').innerHTML = '<i class="bi bi-save me-1"></i> Update';
            const cashModal = new bootstrap.Modal(document.getElementById('cashModal'));
            cashModal.show();
        });
    }

    // ===== Reset modal when opening Add mode =====
    const addButtons = document.querySelectorAll('[data-bs-target="#cashModal"]');
    addButtons.forEach(button => {
        button.addEventListener('click', function () {
            const form = document.getElementById('cashForm');
            if (form) {
                form.reset();
                document.getElementById('cash_id').value = '';
                document.getElementById('cashModalLabel').innerText = 'Add Petty Cash Entry';
                document.getElementById('cashSubmitBtn').innerHTML = '<i class="bi bi-save me-1"></i> Save';
            }
        });
    });

    // ===== Table Search / Filter =====
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const filter = this.value.toLowerCase();
            const table = document.getElementById('cashTable');
            if (!table) return;

            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const supplier = row.querySelector('.supplier')?.textContent.toLowerCase() || '';
                const department = row.querySelector('.department')?.textContent.toLowerCase() || '';
                const invoice = row.querySelector('.invoice')?.textContent.toLowerCase() || '';
                const project = row.querySelector('.project')?.textContent.toLowerCase() || '';

                const match = supplier.includes(filter) || department.includes(filter) || invoice.includes(filter) || project.includes(filter);
                row.style.display = match ? '' : 'none';
            });
        });
    }

    // ===== Export to Excel =====
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            exportBtn.disabled = true;
            const originalText = exportBtn.innerHTML;
            exportBtn.innerHTML = '<i class="bi bi-download me-1"></i> Exporting...';

            fetch('/humanresource/export/petty-cash/', {
                method: 'GET',
            })
                .then(response => {
                    exportBtn.disabled = false;
                    exportBtn.innerHTML = originalText;
                    if (!response.ok) {
                        throw new Error('Failed to fetch Excel file: ' + response.statusText);
                    }
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `petty_cash_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_')}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                })
                .catch(err => {
                    console.error('Excel download failed:', err);
                    alert('Failed to download the Excel file. Please try again or contact support.');
                });
        });
    }

    // ===== New: Logic for populating and submitting the update modal =====
    
    // Function to populate the update modal with data
    function populateUpdateModal(balanceData) {
        document.getElementById('balance_id').value = balanceData.id;
        document.getElementById('update_amount').value = balanceData.amount;
        document.getElementById('update_activity').value = balanceData.activity;
        document.getElementById('update_project_name').value = balanceData.project_name;
        
        const updateBalanceModal = new bootstrap.Modal(document.getElementById('updateBalanceModal'));
        updateBalanceModal.show();
    }

    // Event listener for the "Update" button on the card
    const updateCardBtn = document.getElementById('updateCardBtn');
    if (updateCardBtn) {
        updateCardBtn.addEventListener('click', function() {
            fetch('/humanresource/get_latest_balance/')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to fetch the latest balance record.');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    populateUpdateModal(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Could not load balance data for update.');
                });
        });
    }

    // Update Balance Modal Submission Logic
    const updateBalanceForm = document.getElementById('updateBalanceForm');
    const updateModalSubmitBtn = document.getElementById('updateModalSubmitBtn');

    if (updateBalanceForm && updateModalSubmitBtn) {
        updateModalSubmitBtn.addEventListener('click', function() {
            const formData = new FormData(updateBalanceForm);
            const actionUrl = updateBalanceForm.action;

            fetch(actionUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('updateBalanceModal'));
                    modal.hide();
                    location.reload();
                } else {
                    return response.json().then(data => {
                        alert('Submission failed: ' + (data.error || 'Unknown error.'));
                    });
                }
            })
            .catch(error => {
                console.error('Error during update:', error);
                alert('An error occurred. Please try again.');
            });
        });
    }
});