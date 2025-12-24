/* company.js
   Complete, updated, self-contained.
   - Robust select-all / delegation
   - Create / Update / Delete (AJAX)
   - Client-side search
   - Populate group dropdown
   - Modal messages
   - CSRF helper
*/

// =======================================================
// I. Global Utilities
// =======================================================

function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenElement) return tokenElement.value;

    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            const c = cookie.trim();
            if (c.startsWith('csrftoken=')) {
                cookieValue = decodeURIComponent(c.substring('csrftoken='.length));
            }
        });
    }
    return cookieValue;
}

function showCustomMessageModal(title, bodyHtml, isSuccess = true, headerClass = null, btnClass = null, iconClass = null) {
    const $modal = $('#viewSelectionModal');

    if ($modal.length === 0) {
        console.warn("Message modal not found (#viewSelectionModal). Falling back to alert.");
        alert(`${title}:\n${bodyHtml.replace(/<br>/g, '\n').replace(/<\/?(strong|b|pre|code)>/g, '')}`);
        return;
    }

    const defaultClasses = 'bg-success bg-danger bg-primary bg-light';
    const finalHeaderClass = headerClass || (isSuccess ? 'bg-success' : 'bg-danger');
    const finalBtnClass = btnClass || (isSuccess ? 'btn-success' : 'btn-danger');

    $modal.find('.modal-header').removeClass(defaultClasses).addClass(finalHeaderClass);

    let finalTitle = title;
    if (iconClass) finalTitle = `<i class="bi ${iconClass} me-2"></i>${title}`;
    $modal.find('#viewSelectionModalLabel').html(finalTitle);

    $modal.find('.modal-body').html(bodyHtml);

    const $okBtn = $modal.find('.modal-footer button');
    $okBtn.removeClass('btn-outline-secondary btn-primary btn-danger btn-success btn-light btn-secondary')
        .addClass(finalBtnClass)
        .text('OK');

    const modalInstance = bootstrap.Modal.getOrCreateInstance($modal[0]);
    modalInstance.show();

    // ensure single backdrop
    $modal.on('shown.bs.modal', function () {
        if ($('.modal-backdrop').length > 1) $('.modal-backdrop').first().remove();
    });
}

function populateCompanyGroupDropdown(selectorString, listApiEndpoint, selectedGroupId = null) {
    const $select = $(selectorString);
    if ($select.length === 0) return;

    $.ajax({
        url: listApiEndpoint,
        type: 'GET',
        dataType: 'json',
        success: function (groups) {
            $select.find('option:not(:first)').remove();
            groups.forEach(group => {
                const gId = group.id || group;
                const gName = group.company_name || group.name || group;
                $select.append(`<option value="${gId}">${gName}</option>`);
            });
            if (selectedGroupId) $select.val(selectedGroupId);
        },
        error: function (xhr, status, error) {
            console.error("Error loading groups for dropdown:", status, error);
        }
    });
}

function getSelectedCompanyIds() {
    return $('#companiesTableBody').find('input.select-entry:checked').map(function () {
        return $(this).val();
    }).get();
}

function getDataFromRow($row) {
    const group_id = $row.find('td:eq(2) span').data('group-id') || '';
    return {
        id: $row.find('input.select-entry').val(),
        companyName: $row.find('td:eq(1)').text().trim(),
        companyGroup: group_id,
        companyGroupName: $row.find('td:eq(2) span').text().trim() || '-',
        crNumber: $row.find('td:eq(3)').text().trim(),
        vatNumber: $row.find('td:eq(4)').text().trim(),
        contactName: $row.find('td:eq(5)').text().trim(),
        emailAddress: $row.find('td:eq(6)').text().trim(),
        mobile: $row.find('td:eq(7)').text().trim(),
        phone: $row.find('td:eq(8)').text().trim(),
        companyDetails: '',
        addressText: ''
    };
}

function createCompanyRowHtml(companyData) {
    const groupId = companyData.company_group_id || companyData.companyGroup || '';
    const groupName = companyData.company_group_name || companyData.companyGroupName || '-';
    const val = v => (v && v !== 'null' && v !== 'undefined') ? v : '-';

    return `
        <tr class="new-entry">
            <td><input type="checkbox" class="select-entry form-check-input" value="${companyData.id}"></td>
            <td>${val(companyData.company_name || companyData.companyName)}</td>
            <td>${groupId ? `<span data-group-id="${groupId}">${groupName}</span>` : '-'}</td>
            <td>${val(companyData.cr_number || companyData.crNumber)}</td>
            <td>${val(companyData.vat_number || companyData.vatNumber)}</td>
            <td>${val(companyData.contact_name || companyData.contactName)}</td>
            <td>${val(companyData.email_address || companyData.emailAddress)}</td>
            <td>${val(companyData.mobile)}</td>
            <td>${val(companyData.phone)}</td>
        </tr>
    `;
}

// =======================================================
// II. Form Submission (Create/Update)
// =======================================================

function handleCompanyFormSubmission(e) {
    e.preventDefault();
    const CSRF_TOKEN = getCSRFToken();
    const $companyForm = $('#companyForm');
    const $companyModal = $('#companyModal');
    const $saveCompanyBtn = $('#saveCompanyBtn');

    const mode = $companyForm.data('mode') || 'create';
    const companyId = $companyForm.data('company-id');

    const CREATE_API_ENDPOINT = '/housing/company/create/';
    const UPDATE_API_ENDPOINT = `/housing/company/update/${companyId}/`;

    $saveCompanyBtn.prop('disabled', true).text(mode === 'update' ? 'Updating...' : 'Saving...');

    if (!$companyForm[0].checkValidity()) {
        $companyForm[0].reportValidity();
        $saveCompanyBtn.prop('disabled', false).text(mode === 'update' ? 'Update Company' : 'Save Company');
        return false;
    }

    const formData = {
        company_name: $('#companyName').val(),
        company_group_id: $('#companyGroup').val() || null,
        company_details: $('#companyDetails').val(),
        cr_number: $('#crNumber').val(),
        vat_number: $('#vatNumber').val(),
        address_text: $('#addressText').val(),
        contact_name: $('#contactName').val(),
        email_address: $('#emailAddress').val(),
        mobile: $('#mobile').val(),
        phone: $('#phone').val()
    };

    const companyGroupName = $('#companyGroup option:selected').text().trim();
    let newCompanyData = { ...formData, company_group_name: companyGroupName };

    $.ajax({
        url: mode === 'update' ? UPDATE_API_ENDPOINT : CREATE_API_ENDPOINT,
        type: mode === 'update' ? 'PUT' : 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN },
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function (response) {
            $companyForm[0].reset();
            bootstrap.Modal.getOrCreateInstance($companyModal[0]).hide();
            newCompanyData.id = response.id || companyId;

            const $companiesTableBody = $('#companiesTableBody');
            $companiesTableBody.find('tr').removeClass('new-entry');

            if (mode === 'create') {
                $companiesTableBody.find('tr.no-results-row-client, tr.no-results-row-ajax').remove();
                const newRowHtml = createCompanyRowHtml(newCompanyData);
                $companiesTableBody.prepend(newRowHtml);
            } else {
                const $rowToUpdate = $companiesTableBody.find(`input[value="${companyId}"]`).closest('tr');
                if ($rowToUpdate.length) {
                    const updatedRowHtml = createCompanyRowHtml(newCompanyData);
                    $rowToUpdate.replaceWith(updatedRowHtml);
                }
            }

            // ensure select-all header is updated after new rows added
            updateSelectAllState();

            showCustomMessageModal('Success! 🎉',
                `Company **${newCompanyData.company_name}** record ${mode === 'update' ? 'updated' : 'saved'}.`,
                true, 'bg-success', 'btn-success', 'bi-check-circle-fill');
        },
        error: function (xhr) {
            let errorMessage = `Error (Status: ${xhr.status}): ${xhr.statusText || 'Server Error'}`;
            try {
                const json = JSON.parse(xhr.responseText);
                if (json && typeof json === 'object') errorMessage = JSON.stringify(json, null, 2);
            } catch (err) { /* ignore parse */ }

            showCustomMessageModal(`Error ${mode === 'update' ? 'Updating' : 'Saving'} Company`,
                `An error occurred.<br><pre class="text-start">${errorMessage}</pre>`,
                false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
        },
        complete: function () {
            $saveCompanyBtn.prop('disabled', false).text(mode === 'update' ? 'Update Company' : 'Save Company');
        }
    });
    return false;
}

// --- Selection Validator ---
function validateSelectionAndShowModal(action, selectedIds) {
    const count = selectedIds.length;
    let titleText = '', bodyText = '', headerClass = '', btnClass = '', iconClass = '', validationFailed = false;

    if (action === 'update') {
        titleText = 'Update Company';
        headerClass = 'bg-primary';
        btnClass = 'btn-primary';
        iconClass = 'bi-pencil';
        if (count !== 1) {
            bodyText = count === 0 ? 'Please select **exactly one** company.' : 'You can only update **one** company at a time.';
            validationFailed = true;
        }
    } else if (action === 'delete') {
        titleText = 'Delete Companies';
        headerClass = 'bg-danger';
        btnClass = 'btn-danger';
        iconClass = 'bi-trash';
        if (count === 0) {
            bodyText = 'Please select **at least one** company to delete.';
            validationFailed = true;
        }
    }

    if (validationFailed) {
        showCustomMessageModal(titleText, bodyText, false, headerClass, btnClass, iconClass);
        return false;
    }
    return true;
}

// =======================================================
// III. Utility: Select-all state updater (keeps header checkbox synced)
// =======================================================
function updateSelectAllState() {
    const $companyTableBody = $('#companiesTableBody');
    const $selectAllCheckbox = $('#selectAll');
    const total = $companyTableBody.find('input.select-entry').length;
    const checked = $companyTableBody.find('input.select-entry:checked').length;

    // If there are no rows, uncheck and disable Select All (optional)
    if (total === 0) {
        $selectAllCheckbox.prop('checked', false).prop('indeterminate', false);
        return;
    }

    if (checked === 0) {
        $selectAllCheckbox.prop('checked', false).prop('indeterminate', false);
    } else if (checked === total) {
        $selectAllCheckbox.prop('checked', true).prop('indeterminate', false);
    } else {
        $selectAllCheckbox.prop('checked', false).prop('indeterminate', true);
    }
}

// =======================================================
// IV. Main Initialization
// =======================================================
$(document).ready(function () {
    console.log('company.js loaded');

    const $companyModal = $('#companyModal');
    const $companyForm = $('#companyForm');
    const $saveCompanyBtn = $('#saveCompanyBtn');
    const $updateCompanyBtn = $('#updateCompanyBtn');
    const $deleteSelectedBtn = $('#deleteSelectedBtn');
    const $deleteModal = $('#deleteConfirmModal');
    const $confirmDeleteBtn = $('#confirmDeleteBtn');
    const $companyTableBody = $('#companiesTableBody');
    const $searchTableInput = $('#search');

    const GROUP_LIST_API_ENDPOINT = '/housing/groups/list/';
    const DELETE_COMPANIES_API_ENDPOINT = '/housing/company/delete/';

    // Add New Company
    $('#addNewCompanyBtn').on('click', function () {
        $companyForm[0].reset();
        $companyForm.removeData('company-id').data('mode', 'create');
        $('#companyModalLabel').text('Add New Company');
        $saveCompanyBtn.text('Save Company').prop('disabled', false);
        $companyTableBody.find('tr').removeClass('new-entry');
        populateCompanyGroupDropdown('#companyGroup', GROUP_LIST_API_ENDPOINT);
    });

    // Save/Submit Form
    $saveCompanyBtn.on('click', handleCompanyFormSubmission);
    $companyForm.on('submit', handleCompanyFormSubmission);

    // Update Company
    $updateCompanyBtn.on('click', function () {
        const selectedIds = getSelectedCompanyIds();
        if (!validateSelectionAndShowModal('update', selectedIds)) return;

        const companyId = selectedIds[0];
        const UPDATE_API_ENDPOINT = `/housing/company/update/${companyId}/`;
        
        // Fetch full company details from server
        $.ajax({
            url: UPDATE_API_ENDPOINT,
            type: 'GET',
            dataType: 'json',
            success: function (companyData) {
                // Populate all form fields with data from server
                $('#companyName').val(companyData.company_name || '');
                $('#crNumber').val(companyData.cr_number || '');
                $('#vatNumber').val(companyData.vat_number || '');
                $('#contactName').val(companyData.contact_name || '');
                $('#emailAddress').val(companyData.email_address || '');
                $('#mobile').val(companyData.mobile || '');
                $('#phone').val(companyData.phone || '');
                $('#companyDetails').val(companyData.company_details || '');
                $('#addressText').val(companyData.address_text || '');

                $companyForm.data('mode', 'update').data('company-id', companyId);
                $('#companyModalLabel').text('Update Company Details');
                $saveCompanyBtn.text('Update Company').prop('disabled', false);

                populateCompanyGroupDropdown('#companyGroup', GROUP_LIST_API_ENDPOINT, companyData.company_group_id);
                bootstrap.Modal.getOrCreateInstance($companyModal[0]).show();
            },
            error: function (xhr) {
                let errorMessage = `Error fetching company details (Status: ${xhr.status})`;
                showCustomMessageModal('Error Loading Company',
                    `Could not load company details.<br>${errorMessage}`,
                    false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
            }
        });
    });

    // Delete Companies (open confirmation)
    $deleteSelectedBtn.on('click', function (e) {
        e.preventDefault();
        const selectedIds = getSelectedCompanyIds();
        if (!validateSelectionAndShowModal('delete', selectedIds)) return;

        const msg = `Are you sure you want to permanently delete **${selectedIds.length}** selected company record(s)?`;
        $deleteModal.find('.modal-body p:first').html(msg);
        bootstrap.Modal.getOrCreateInstance($deleteModal[0]).show();
    });

    // Confirm Delete
    $confirmDeleteBtn.on('click', function () {
        const selectedIds = getSelectedCompanyIds();
        bootstrap.Modal.getOrCreateInstance($deleteModal[0]).hide();
        $confirmDeleteBtn.prop('disabled', true).text('Deleting...');

        $.ajax({
            url: DELETE_COMPANIES_API_ENDPOINT,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ ids: selectedIds }),
            headers: { 'X-CSRFToken': getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    selectedIds.forEach(id => {
                        $(`#companiesTableBody input[value="${id}"]`).closest('tr').fadeOut(300, function () { $(this).remove(); });
                    });

                    setTimeout(() => {
                        if ($companyTableBody.find('tr').length === 0) {
                            $companyTableBody.html('<tr><td colspan="9" class="text-center text-muted">No company records found</td></tr>');
                        }
                        // after DOM changes, ensure select all state updates
                        updateSelectAllState();
                    }, 350);

                    showCustomMessageModal('Deletion Success', response.message, true, 'bg-success', 'btn-success', 'bi-check-circle-fill');
                } else {
                    showCustomMessageModal('Deletion Failed', response.error, false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
                }
            },
            error: function (xhr) {
                const errorDetail = xhr.responseJSON?.error || xhr.statusText || 'Unknown error';
                showCustomMessageModal('Deletion Error', `Could not delete records: ${errorDetail}`, false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
            },
            complete: function () {
                $confirmDeleteBtn.prop('disabled', false).text('Confirm Delete');
            }
        });
    });

    // Client side search
    $searchTableInput.on('input', function () {
        const searchTerm = $(this).val().toLowerCase().trim();
        let rowCount = 0;
        const $noResultsRow = $companyTableBody.find('tr.no-results-row-client');

        if (!searchTerm) {
            $companyTableBody.find('tr').show();
            $noResultsRow.remove();
            return;
        }

        $companyTableBody.find('tr:not(.no-results-row-client)').each(function () {
            const $row = $(this);
            const textContent = $row.find('td:eq(1),td:eq(2),td:eq(5),td:eq(6),td:eq(7),td:eq(8)').text().toLowerCase();
            if (textContent.includes(searchTerm)) { $row.show(); rowCount++; } else { $row.hide(); }
        });

        if (rowCount === 0 && !$noResultsRow.length) {
            $companyTableBody.append('<tr class="no-results-row-client"><td colspan="9" class="text-center text-muted">No records found matching your current filter.</td></tr>');
        } else {
            $noResultsRow.remove();
        }
    });

    // Export
    const exportBtn = document.getElementById("exportBtn");
    if (exportBtn) {
        exportBtn.addEventListener("click", () => {
            const originalContent = exportBtn.innerHTML;
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';
            window.location.href = "/housing/company/export/";
            setTimeout(() => { exportBtn.disabled = false; exportBtn.innerHTML = originalContent; }, 2000);
        });
    }

    // cleanup and initial select-all state
    $companyTableBody.find('tr:not(:first-child)').removeClass('new-entry');
    updateSelectAllState();

    // --- Select All / Delegated checkbox handling ---
    const $selectAllCheckbox = $('#selectAll');

    // header checkbox toggles all row checkboxes
    $selectAllCheckbox.on('change', function () {
        const isChecked = $(this).is(':checked');
        // operate only on checkboxes inside table body
        $companyTableBody.find('input.select-entry').prop('checked', isChecked).trigger('change');
        // updateSelectAllState(); // not necessary because change handlers will call it
    });

    // delegate change for dynamic row checkboxes
    $companyTableBody.on('change', 'input.select-entry', function () {
        // keep select-all in sync
        updateSelectAllState();
    });

    // =======================================================
    // Company Group Management
    // =======================================================
    const $companyGroupModal = $('#companyGroupModal');
    const $companyGroupForm = $('#companyGroupForm');
    const $saveGroupBtn = $('#saveGroupBtn');
    const GROUP_CREATE_API_ENDPOINT = '/housing/groups/create/';

    // Open Company Group Modal
    $('#viewGroupBtn').on('click', function () {
        $companyGroupForm[0].reset();
        $('#companyGroupId').val('');
        $('#groupName').focus();
    });

    // Save Company Group
    $saveGroupBtn.on('click', function (e) {
        e.preventDefault();
        
        if (!$companyGroupForm[0].checkValidity()) {
            $companyGroupForm[0].reportValidity();
            return false;
        }

        const groupName = $('#groupName').val().trim();
        if (!groupName) {
            showCustomMessageModal('Validation Error', 'Please enter a company group name.', false, 'bg-warning', 'btn-warning', 'bi-exclamation-triangle-fill');
            return false;
        }

        $saveGroupBtn.prop('disabled', true).text('Saving...');

        $.ajax({
            url: GROUP_CREATE_API_ENDPOINT,
            type: 'POST',
            headers: { 'X-CSRFToken': getCSRFToken() },
            contentType: 'application/json',
            data: JSON.stringify({ company_name: groupName }),
            success: function (response) {
                $companyGroupForm[0].reset();
                bootstrap.Modal.getOrCreateInstance($companyGroupModal[0]).hide();
                
                showCustomMessageModal('Success! 🎉',
                    `Company Group **${groupName}** has been created successfully.`,
                    true, 'bg-success', 'btn-success', 'bi-check-circle-fill');
                
                // Refresh the company group dropdown in the company form
                populateCompanyGroupDropdown('#companyGroup', GROUP_LIST_API_ENDPOINT);
            },
            error: function (xhr) {
                let errorMessage = `Error (Status: ${xhr.status}): ${xhr.statusText || 'Server Error'}`;
                try {
                    const json = JSON.parse(xhr.responseText);
                    if (json && typeof json === 'object') errorMessage = JSON.stringify(json, null, 2);
                } catch (err) { /* ignore parse */ }

                showCustomMessageModal('Error Creating Group',
                    `An error occurred.<br><pre class="text-start">${errorMessage}</pre>`,
                    false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
            },
            complete: function () {
                $saveGroupBtn.prop('disabled', false).text('Save');
            }
        });
        return false;
    });

    // Also handle form submission via Enter key
    $companyGroupForm.on('submit', function (e) {
        e.preventDefault();
        $saveGroupBtn.click();
        return false;
    });

    // Debugging helper (uncomment to log)
    // $(document).on('click', '#selectAll, input.select-entry', function(){ console.log('selectAll:', $('#selectAll').is(':checked'), 'checkedCount:', getSelectedCompanyIds().length); });
});
