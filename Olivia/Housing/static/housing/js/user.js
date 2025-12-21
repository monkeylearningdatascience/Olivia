// =======================================================
// housing/js/user.js - FIXED, UPDATED
// =======================================================

// Utility to get CSRF Token
function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenElement) return tokenElement.value;
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show custom message modal
function showCustomMessageModal(title, bodyHtml, isSuccess = true, headerClass = null, btnClass = null, iconClass = null) {
    const $modal = $('#viewSelectionModal');
    if ($modal.length === 0) {
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
        .addClass(finalBtnClass).text('OK');

    const modalInstance = bootstrap.Modal.getOrCreateInstance($modal[0]);
    modalInstance.show();
}

// Populate dropdowns dynamically
function populateDropdown(selectorString, listApiEndpoint, selectedId = null, nameField = 'company_name') {
    const $select = $(selectorString);
    if ($select.length === 0) return;

    $.ajax({
        url: listApiEndpoint,
        type: 'GET',
        dataType: 'json',
        success: function (items) {
            $select.find('option:not(:first)').remove();
            items.forEach(function (item) {
                const id = item.id;
                const name = item[nameField] || item.company_name || item.companyGroupName || item.name || item;
                $select.append(`<option value="${id}">${name}</option>`);
            });
            if (selectedId) $select.val(selectedId);
        },
        error: function (xhr) { console.error("Dropdown load error:", xhr); }
    });
}

// Get selected user ids
function getSelectedUserIds() {
    return $('#usersTableBody').find('input.select-entry:checked').map(function () { return $(this).val(); }).get();
}

// Extract data from table row
function getUserDataFromRow($row) {
    return {
        id: $row.find('input.select-entry').val(),
        username: $row.find('td:eq(1)').text().trim(),
        groupId: $row.find('td:eq(2) span').data('group-id') || '',
        groupName: $row.find('td:eq(2) span').text().trim() || '-',
        companyId: $row.find('td:eq(3) span').data('company-id') || '',
        companyName: $row.find('td:eq(3) span').text().trim() || '-',
        governmentId: $row.find('td:eq(4)').text().trim(),
        idType: $row.find('td:eq(5)').text().trim(),
        neomId: $row.find('td:eq(6)').text().trim(),
        dob: $row.find('td:eq(7)').text().trim(),
        mobile: $row.find('td:eq(8)').text().trim(),
        email: $row.find('td:eq(9)').text().trim(),
        nationality: $row.find('td:eq(10)').text().trim(),
        religion: $row.find('td:eq(11)').text().trim(),
        status: $row.find('td:eq(12)').text().trim(),
    };
}

// Create table row HTML for a user
function createUserRowHtml(userData) {
    const val = v => (v && v !== 'null' && v !== 'undefined' && v !== '-') ? v : '-';
    const groupHtml = userData.group_id ? `<span data-group-id="${userData.group_id}">${val(userData.groupName)}</span>` : '-';
    const companyHtml = userData.company_id ? `<span data-company-id="${userData.company_id}">${val(userData.companyName)}</span>` : '-';
    return `
        <tr class="new-entry">
            <td><input type="checkbox" class="select-entry form-check-input" value="${userData.id}"></td>
            <td>${val(userData.username)}</td>
            <td>${groupHtml}</td>
            <td>${companyHtml}</td>
            <td>${val(userData.government_id)}</td> <td>${val(userData.id_type)}</td>       
            <td>${val(userData.neom_id)}</td> <td>${val(userData.dob)}</td>
            <td>${val(userData.mobile)}</td>
            <td>${val(userData.email)}</td>
            <td>${val(userData.nationality)}</td>
            <td>${val(userData.religion)}</td>
            <td>${val(userData.status)}</td>
        </tr>
    `;
}

// Sort table by ID descending (latest first)
function sortUserTable() {
    const $tbody = $('#usersTableBody');
    const rows = $tbody.find('tr').get();
    const sortableRows = rows.filter(r => !$(r).hasClass('no-results-row-client') && !$(r).hasClass('no-results-row-ajax'));
    sortableRows.sort((a, b) => {
        const idA = parseInt($(a).find('.select-entry').val() || 0);
        const idB = parseInt($(b).find('.select-entry').val() || 0);
        return idB - idA; // latest first
    });
    $tbody.empty().append(sortableRows).append(rows.filter(r => $(r).hasClass('no-results-row-client') || $(r).hasClass('no-results-row-ajax')));

    highlightLatestEntry(); // highlight first row after sorting
}

function highlightLatestEntry() {
    const $tbody = $('#usersTableBody');
    $tbody.find('tr').removeClass('new-entry'); // remove old highlights
    const $firstVisible = $tbody.find('tr:visible:not(.no-results-row-client)').first();
    $firstVisible.addClass('new-entry'); // highlight latest first row
}

// Handle user form submission (create/update)
function handleUserFormSubmission(e) {
    e.preventDefault();
    const CSRF_TOKEN = getCSRFToken();
    const $form = $('#userForm');
    const mode = $form.data('mode') || 'create';
    const userId = $form.data('user-id');

    const CREATE_API = '/housing/user/create/';
    const UPDATE_API = `/housing/user/update/${userId}/`;
    const $saveBtn = $('#saveUserBtn');
    $saveBtn.prop('disabled', true).text(mode === 'update' ? 'Updating...' : 'Saving...');

    if (!$form[0].checkValidity()) {
        $form[0].reportValidity();
        $saveBtn.prop('disabled', false).text(mode === 'update' ? 'Update' : 'Save');
        return false;
    }

    const formData = {
        username: $('#username').val(),
        group_id: $('#groupSelect').val() || null,
        company_id: $('#companySelect').val() || null,
        government_id: $('#governmentId').val(),
        id_type: $('#idType').val(),
        neom_id: $('#neomId').val(),
        dob: $('#dob').val() || null,
        mobile: $('#mobileUser').val(),
        email: $('#emailUser').val(),
        nationality: $('#nationality').val(),
        religion: $('#religion').val(),
        status: $('#status').val(),
    };

    const apiURL = mode === 'update' ? UPDATE_API : CREATE_API;
    const methodType = mode === 'update' ? 'PUT' : 'POST';

    $.ajax({
        url: apiURL,
        type: methodType,
        headers: { 'X-CSRFToken': CSRF_TOKEN },
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function (response) {
            // 1. Reset form and hide the primary user modal
            $form[0].reset();
            const modalEl = document.getElementById('userModal');
            const modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
            modalInstance.hide();

            // 2. Prepare the new/updated user data object
            const newUser = {
                id: response.id || userId,
                username: response.username || formData.username,
                group_id: response.group_id || formData.group_id,
                groupName: response.group_name || $('#groupSelect option:selected').text(),
                company_id: response.company_id || formData.company_id,
                companyName: response.company_name || $('#companySelect option:selected').text(),
                government_id: response.government_id || formData.government_id,
                id_type: response.id_type || formData.id_type,
                neom_id: response.neom_id || formData.neom_id,
                dob: response.dob || formData.dob,
                mobile: response.mobile || formData.mobile,
                email: response.email || formData.email,
                nationality: response.nationality_name || response.nationality || $('#nationality option:selected').text(),
                religion: response.religion || formData.religion,
                status: response.status || formData.status,
            };

            // 3. Update the data table (Create or Update)
            const $tbody = $('#usersTableBody');
            if (mode === 'create') {
                $tbody.find('tr.new-entry').removeClass('new-entry');
                $tbody.prepend(createUserRowHtml(newUser));
                sortUserTable();
            } else {
                const $rowToUpdate = $tbody.find(`input[value="${userId}"]`).closest('tr');
                if ($rowToUpdate.length) {
                    $tbody.find('tr.new-entry').removeClass('new-entry');
                    $rowToUpdate.replaceWith(createUserRowHtml(newUser));
                    sortUserTable();
                }
            }

            // 4. Show the custom success message modal
            // Note: We MUST verify the ID of the modal shown here (e.g., 'customMessageModal')
            showCustomMessageModal('Success! 🎉', `User <strong>${newUser.username}</strong> saved.`, true, 'bg-success', 'btn-success', 'bi-check-circle-fill');

            // 5. 💡 AGGRESSIVE FIX: Attempt standard hide AND force cleanup after 3 seconds
            setTimeout(function () {
                // A. Attempt to hide the modal instance (Best practice)
                const customModalEl = document.getElementById('viewSelectionModal'); // <-- VERIFY ID
                if (customModalEl) {
                    let customModalInstance = bootstrap.Modal.getOrCreateInstance(customModalEl);
                    customModalInstance.hide();
                }

                // B. Brute-Force Cleanup (Necessary if A fails)
                // This removes the leftover class and div that keeps the background dark.
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();

            }, 3000); // 3 seconds delay
        },
        error: function (xhr) {
            let err = `Error (Status ${xhr.status})`;
            try {
                const json = JSON.parse(xhr.responseText);
                err = JSON.stringify(json, null, 2).replace(/"/g, '').replace(/,/g, '<br>');
            } catch (e) { err = xhr.statusText || 'Server error'; }
            showCustomMessageModal('Save Error', `<pre class="text-start">${err}</pre>`, false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
        },
        complete: function () { $saveBtn.prop('disabled', false).text(mode === 'update' ? 'Update' : 'Save'); }
    });
    return false;
}

// -------------------------------------------------------
// Initialize everything on document ready
// -------------------------------------------------------
$(document).ready(function () {
    const $usersTableBody = $('#usersTableBody');
    const $userModal = $('#userModal');
    const $userForm = $('#userForm');
    const $saveUserBtn = $('#saveUserBtn');

    const GROUP_LIST_API = '/housing/groups/list/';
    const COMPANY_LIST_API = '/housing/companies/list/';
    const GET_COMPANIES_API = '/housing/get_companies/';
    const DELETE_API = '/housing/user/delete/';
    const EXPORT_URL = '/housing/user/export/';

    // Add new user
    $('#addNewUserBtn').on('click', function () {
        $userForm[0].reset();
        $userForm.removeData('user-id').data('mode', 'create');
        $('#userModalLabel').text('Add New User');
        $saveUserBtn.text('Save').prop('disabled', false);

        populateDropdown('#groupSelect', GROUP_LIST_API);
        populateDropdown('#companySelect', COMPANY_LIST_API);
        $usersTableBody.find('tr').removeClass('new-entry');
    });

    // Save/submit
    $saveUserBtn.on('click', handleUserFormSubmission);
    $userForm.on('submit', handleUserFormSubmission);

    // Update user
    $('#updateUserBtn').on('click', function () {
        const selectedIds = getSelectedUserIds();
        if (selectedIds.length !== 1) return showCustomMessageModal('Update User', 'Please select exactly one user.', false, 'bg-primary', 'btn-primary', 'bi-pencil');

        const userId = selectedIds[0];
        const $row = $usersTableBody.find(`input[value="${userId}"]`).closest('tr');
        const userData = getUserDataFromRow($row);

        $('#username').val(userData.username);
        $('#governmentId').val(userData.governmentId === '-' ? '' : userData.governmentId);
        $('#idType').val(userData.idType === '-' ? '' : userData.idType);
        $('#neomId').val(userData.neomId === '-' ? '' : userData.neomId);
        $('#dob').val(userData.dob === '-' ? '' : userData.dob);
        $('#mobileUser').val(userData.mobile === '-' ? '' : userData.mobile);
        $('#emailUser').val(userData.email === '-' ? '' : userData.email);
        $('#nationality').val(userData.nationality === '-' ? '' : userData.nationality);
        $('#religion').val(userData.religion === '-' ? '' : userData.religion);
        $('#status').val(userData.status || 'Active');

        $userForm.data('mode', 'update').data('user-id', userId);
        $('#userModalLabel').text('Update User Details');

        populateDropdown('#groupSelect', GROUP_LIST_API, userData.groupId);
        populateDropdown('#companySelect', COMPANY_LIST_API, userData.companyId);

        const modalInstance = bootstrap.Modal.getOrCreateInstance($userModal[0]);
        modalInstance.show();
    });

    // Delete user (modal + ajax)
    $('#deleteSelectedUserBtn').on('click', function () {
        const selectedIds = getSelectedUserIds();
        if (selectedIds.length === 0) return showCustomMessageModal('Delete User', 'Please select at least one user to delete.', false, 'bg-danger', 'btn-danger', 'bi-trash');

        const $deleteModal = $('#deleteConfirmModal');
        $deleteModal.find('.modal-body p:first').html(`Are you sure you want to permanently delete <strong>${selectedIds.length}</strong> user(s)?`);
        bootstrap.Modal.getOrCreateInstance($deleteModal[0]).show();
    });

    $('#confirmDeleteBtn').on('click', function () {
        const ids = getSelectedUserIds();
        const $deleteModal = $('#deleteConfirmModal');
        bootstrap.Modal.getOrCreateInstance($deleteModal[0]).hide();
        $(this).prop('disabled', true).text('Deleting...');

        $.ajax({
            url: DELETE_API,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ ids: ids }),
            headers: { 'X-CSRFToken': getCSRFToken() },
            success: function (res) {
                if (res.success) {
                    ids.forEach(id => $usersTableBody.find(`input[value="${id}"]`).closest('tr').fadeOut(300, function () { $(this).remove(); }));
                    setTimeout(() => {
                        if ($usersTableBody.find('tr:not(.no-results-row-client)').length === 0) {
                            $usersTableBody.html('<tr><td colspan="13" class="text-center text-muted">No user records found</td></tr>');
                        }
                    }, 350);
                    showCustomMessageModal('Deletion Success', res.message, true, 'bg-success', 'btn-success', 'bi-check-circle-fill');
                } else showCustomMessageModal('Deletion Failed', res.error || 'Unknown error', false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
            },
            error: function (xhr) { showCustomMessageModal('Deletion Error', `Could not delete: ${xhr.statusText}`, false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill'); },
            complete: function () { $('#confirmDeleteBtn').prop('disabled', false).text('Confirm Delete'); }
        });
    });

    // Dynamic company loading based on group
    $('#groupSelect').on('change', function () {
        const groupId = $(this).val();
        const $companySelect = $('#companySelect');
        $companySelect.empty().append('<option value="">Select Company...</option>');

        if (groupId) {
            $.ajax({
                url: GET_COMPANIES_API,
                data: { group_id: groupId },
                success: function (data) {
                    data.forEach(company => $companySelect.append(`<option value="${company.id}">${company.company_name}</option>`));
                }
            });
        }
    });

    // Search/filter
    $('#searchUser').on('input', function () {
        const term = $(this).val().toLowerCase().trim();
        let count = 0;
        const $noRow = $usersTableBody.find('tr.no-results-row-client');
        if (term.length === 0) { $usersTableBody.find('tr').show(); $noRow.remove(); return; }

        $usersTableBody.find('tr:not(.no-results-row-client)').each(function () {
            const $r = $(this);
            const text = $r.find('td').map((_, td) => $(td).text()).get().join(' ').toLowerCase();
            if (text.includes(term)) { $r.show(); count++; } else { $r.hide(); }
        });

        if (count === 0 && $noRow.length === 0) $usersTableBody.append('<tr class="no-results-row-client"><td colspan="13" class="text-center text-muted">No records found matching your filter.</td></tr>');
        if (count > 0) $noRow.remove();
    });

    // Export
    $('#exportUserBtn').on('click', function () {
        const $btn = $(this), original = $btn.html();
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Preparing...');
        window.location.href = EXPORT_URL;
        setTimeout(() => $btn.prop('disabled', false).html(original), 2000);
    });

    // Table select all
    const selectAllCheckbox = document.getElementById("selectAllUsers");
    const table = document.querySelector("table");
    table.addEventListener("change", function (e) {
        if (e.target.classList.contains("select-entry")) {
            if (!e.target.checked) selectAllCheckbox.checked = false;
            else {
                const allCheckboxes = table.querySelectorAll(".select-entry");
                const visible = Array.from(allCheckboxes).filter(cb => $(cb).closest('tr').is(':visible') && !$(cb).closest('tr').hasClass('no-results-row-client'));
                selectAllCheckbox.checked = visible.every(cb => cb.checked);
            }
        }
    });
    selectAllCheckbox.addEventListener("change", function () {
        $usersTableBody.find('tr:visible:not(.no-results-row-client) .select-entry').prop('checked', this.checked);
    });

    // Initial sort
    sortUserTable();
});
