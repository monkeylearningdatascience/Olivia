// Global utility to get CSRF Token
function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenElement ? tokenElement.value : null;
}

// --- UTILITY: Custom Message Modal (Unchanged) ---
function showCustomMessageModal(title, bodyHtml, isSuccess = true, headerClass = null, btnClass = null, iconClass = null) {
    const $modal = $('#viewSelectionModal');

    if ($modal.length === 0) {
        console.warn("Message modal not found (#viewSelectionModal). Falling back to alert.");
        alert(`${title}:\n${bodyHtml.replace(/<br>/g, '\n').replace(/<\/?(strong|b|pre|code)>/g, '')}`);

        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
        return;
    }
    
    // Determine final classes
    const defaultClasses = 'bg-success bg-danger bg-primary bg-light';
    const finalHeaderClass = headerClass || (isSuccess ? 'bg-success' : 'bg-danger');
    const finalBtnClass = btnClass || (isSuccess ? 'btn-success' : 'btn-danger');
    
    // --- Header Fix ---
    $modal.find('.modal-header')
        .removeClass(defaultClasses)
        .addClass(finalHeaderClass);

    // Set title, including the icon (if provided)
    let finalTitle = title;
    if (iconClass) {
         finalTitle = `<i class="bi ${iconClass} me-2"></i>${title}`;
    }
    $modal.find('#viewSelectionModalLabel').html(finalTitle);

    // Set body content
    $modal.find('.modal-body').html(bodyHtml);

    // --- Footer Button Fix ---
    const $okBtn = $modal.find('.modal-footer button');
    
    $okBtn.removeClass('btn-outline-secondary btn-primary btn-danger btn-success btn-light btn-secondary')
          .addClass(finalBtnClass)
          .text('OK');

    const modalInstance = bootstrap.Modal.getOrCreateInstance($modal[0]);
    modalInstance.show();

    $modal.on('shown.bs.modal', function () {
        if ($('.modal-backdrop').length > 1) {
            $('.modal-backdrop').first().remove();
        }
    });
}
// -----------------------------------------------------------


// --- Populates the main Company Group dropdown (Unchanged) ---
function populateCompanyGroupDropdown(selectorString, listApiEndpoint, selectedGroupId = null) {
    const $select = $(selectorString);
    if ($select.length === 0) return;

    $.ajax({
        url: listApiEndpoint,
        type: 'GET',
        dataType: 'json',
        success: function (groups) {
            $select.find('option:not(:first)').remove();

            groups.forEach(function (group) {
                const newOption = `<option value="${group.id}">${group.company_name}</option>`;
                $select.append(newOption);
            });

            if (selectedGroupId) {
                $select.val(selectedGroupId);
            }
        },
        error: function (xhr, status, error) {
            console.error("Error loading groups for dropdown via AJAX:", status, error);
        }
    });
}
// --------------------------------------------------------------------------------------

// --- UTILITY: Get selected Company IDs (Unchanged) ---
function getSelectedCompanyIds() {
    return $('#companiesTableBody').find('input.select-entry:checked').map(function() {
        return $(this).val();
    }).get();
}

// --- getDataFromRow (Unchanged) ---
function getDataFromRow($row) {
    // Note: td:eq(2) is the Group column
    const group_id = $row.find('td:eq(2) span').data('group-id') || '';

    const data = {
        id: $row.find('input.select-entry').val(),
        companyName: $row.find('td:eq(1)').text().trim(),
        companyGroup: group_id, 
        companyGroupName: $row.find('td:eq(2) span').text().trim() || '-',
        crNumber: $row.find('td:eq(3)').text().trim() === '-' ? '' : $row.find('td:eq(3)').text().trim(),
        vatNumber: $row.find('td:eq(4)').text().trim() === '-' ? '' : $row.find('td:eq(4)').text().trim(),
        contactName: $row.find('td:eq(5)').text().trim() === '-' ? '' : $row.find('td:eq(5)').text().trim(),
        emailAddress: $row.find('td:eq(6)').text().trim() === '-' ? '' : $row.find('td:eq(6)').text().trim(),
        mobile: $row.find('td:eq(7)').text().trim() === '-' ? '' : $row.find('td:eq(7)').text().trim(),
        phone: $row.find('td:eq(8)').text().trim() === '-' ? '' : $row.find('td:eq(8)').text().trim(),
        companyDetails: '', 
        addressText: '',
    };

    return data;
}

// --- createCompanyRowHtml (Unchanged, used by rendering functions) ---
function createCompanyRowHtml(companyData) {
    const groupId = companyData.company_group_id || companyData.companyGroup || '';
    const groupName = companyData.company_group_name || companyData.companyGroupName || '-';
    
    const cr_number = companyData.cr_number || '-';
    const vat_number = companyData.vat_number || '-';
    const contact_name = companyData.contact_name || '-';
    const email_address = companyData.email_address || '-';
    const mobile = companyData.mobile || '-';
    const phone = companyData.phone || '-';

    return `
        <tr class="new-entry">
            <td><input type="checkbox" class="select-entry" value="${companyData.id}"></td>
            <td>${companyData.company_name || companyData.companyName}</td>
            
            <td>
                ${groupId ? `<span data-group-id="${groupId}">${groupName}</span>` : '-'}
            </td>
            
            <td>${cr_number}</td>
            <td>${vat_number}</td>
            <td>${contact_name}</td>
            <td>${email_address}</td>
            <td>${mobile}</td>
            <td>${phone}</td>
        </tr>
    `;
}


// --- handleCompanyFormSubmission (Unchanged) ---
function handleCompanyFormSubmission(e) {
    e.preventDefault(); 
    const CSRF_TOKEN = getCSRFToken();
    const $companyModal = $('#companyModal');
    const $companyForm = $('#companyForm');
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
        phone: $('#phone').val(),
    };

    const companyGroupName = $('#companyGroup option:selected').text().trim();
    
    let newCompanyData = { ...formData, company_group_name: companyGroupName };
    
    let apiURL = mode === 'update' ? UPDATE_API_ENDPOINT : CREATE_API_ENDPOINT;
    let methodType = mode === 'update' ? 'PUT' : 'POST';

    $.ajax({
        url: apiURL,
        type: methodType,
        headers: { 'X-CSRFToken': CSRF_TOKEN },
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function (response) {
            $companyForm[0].reset();
            const modalInstance = bootstrap.Modal.getOrCreateInstance($companyModal[0]);
            modalInstance.hide();

            newCompanyData.id = response.id || companyId;
            newCompanyData.company_group_id = response.company_group_id || newCompanyData.company_group_id;
            newCompanyData.company_group_name = response.company_group_name || newCompanyData.company_group_name;
            
            if (mode === 'create') {
                const $companiesTableBody = $('#companiesTableBody');
                $companiesTableBody.find('tr').removeClass('new-entry');
                
                const newRowHtml = createCompanyRowHtml(newCompanyData);

                // Remove the "No records" row if it exists
                $companiesTableBody.find('tr:first-child td[colspan="9"]').closest('tr').remove();
                
                $companiesTableBody.prepend(newRowHtml);
            } else { 
                const $rowToUpdate = $('#companiesTableBody').find(`input[value="${companyId}"]`).closest('tr');
                if ($rowToUpdate.length) {
                    $('#companiesTableBody tr').removeClass('new-entry');
                    
                    const updatedRowHtml = createCompanyRowHtml(newCompanyData);
                    const $newRow = $(updatedRowHtml);
                    $rowToUpdate.replaceWith($newRow);
                }
            }
            
            const companyName = newCompanyData.company_name;
            const action = mode === 'update' ? 'updated' : 'saved';
            showCustomMessageModal('Success! 🎉', 
                                    `Company **${companyName}** record ${action}. The list has been updated.`, 
                                    true, 
                                    'bg-success', 
                                    'btn-success', 
                                    'bi-check-circle-fill' 
                                    );
        },
        error: function (xhr) {
            console.error('Error operation:', xhr.responseText);
            let errorMessage = `Error (Status: ${xhr.status}): `;
            try {
                const errorJson = JSON.parse(xhr.responseText);
                errorMessage = JSON.stringify(errorJson, null, 2).replace(/"/g, '').replace(/,/g, '<br>');
            } catch (e) {
                errorMessage += xhr.statusText || 'Server did not return a valid response.';
            }

            showCustomMessageModal(`Error ${mode === 'update' ? 'Updating' : 'Saving'} Company`,
                                     `An error occurred. Details:<br><pre class="text-start">${errorMessage}</pre>`, 
                                     false,
                                     'bg-danger',
                                     'btn-danger',
                                     'bi-x-octagon-fill'
                                    );
        },
        complete: function () {
            $saveCompanyBtn.prop('disabled', false).text(mode === 'update' ? 'Update Company' : 'Save Company');
        }
    });
    return false;
}

// --------------------------------------------------------
// --- UTILITY: Validate Selection and Show Modal (Unchanged) ---
// --------------------------------------------------------

function validateSelectionAndShowModal(action, selectedIds) {
    const count = selectedIds.length;
    let titleText = '';
    let bodyText = '';
    let headerClass = '';
    let btnClass = '';
    let iconClass = ''; 
    let validationFailed = false;

    if (action === 'update') {
        titleText = 'Update Company';
        headerClass = 'bg-primary';
        btnClass = 'btn-primary';
        iconClass = 'bi-pencil'; 

        if (count !== 1) {
            bodyText = (count === 0) 
                ? 'Please select **exactly one** company record to update.'
                : 'You can only update **one** company record at a time. Please deselect all others.';
            validationFailed = true;
        }
    } else if (action === 'delete') {
        titleText = 'Delete Companies';
        headerClass = 'bg-danger';
        btnClass = 'btn-danger';
        iconClass = 'bi-trash'; 

        if (count === 0) {
            bodyText = 'Please select **at least one** company record to delete.';
            validationFailed = true;
        }
    }

    if (validationFailed) {
        showCustomMessageModal(
            titleText,
            bodyText,
            false, 
            headerClass,
            btnClass,
            iconClass
        );
        return false;
    }

    return true;
}

// --------------------------------------------------------
// ⭐ AJAX & RENDERING LOGIC (Retained for server-side operations if needed) ⭐
// --------------------------------------------------------

// Function to render the HTML table rows from JSON data
// This is used if data is fetched from the server (e.g., when clearing a server-side search)
const renderCompanyTable = (companies) => {
    const tableBody = document.getElementById("companiesTableBody");
    if (!tableBody) return;

    let html = '';
    if (companies.length === 0) {
        // Use a unique class for the "No records" row
        html = '<tr class="no-results-row-ajax"><td colspan="9" class="text-center text-muted">No company records found matching your search.</td></tr>';
    } else {
        companies.forEach(company => {
            // Re-use the existing function to generate the row HTML
            html += createCompanyRowHtml(company);
        });
    }
    
    tableBody.innerHTML = html;
};

// Function to fetch and render companies from the server
const fetchAndRenderCompanies = (searchTerm = '') => {
    const url = `/housing/company/list/?search=${searchTerm}`;

    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            // Assuming your Django view returns the filtered list under a key like 'companies'
            renderCompanyTable(data.companies || data); 
        })
        .catch(error => {
            console.error('Error fetching companies:', error);
             renderCompanyTable([]); // Clear the table on error
        });
};


// --------------------------------------------------------
// --- Main Ready Function ---
// --------------------------------------------------------
$(document).ready(function () {
    const $companyModal = $('#companyModal');
    const $companyForm = $('#companyForm');
    const $saveCompanyBtn = $('#saveCompanyBtn');
    const $updateCompanyBtn = $('#updateCompanyBtn');
    const $deleteSelectedBtn = $('#deleteSelectedBtn'); 
    
    const $deleteModal = $('#deleteConfirmModal'); 
    const $confirmDeleteBtn = $('#confirmDeleteBtn');   
    
    const $companyTableBody = $('#companiesTableBody');

    const GROUP_LIST_API_ENDPOINT = '/housing/groups/list/';
    const DELETE_COMPANIES_API_ENDPOINT = '/housing/company/delete/'; 

    // --- Search variables ---
    const $searchTableInput = $('#search'); // The input you want to use for filtering
    const searchInput = document.getElementById('searchInput'); // Retaining the old ID for the fetch logic (if still used)
    let searchTimeout = null;

    // --- Initial setup (Unchanged) ---
    $('#addNewCompanyBtn').on('click', function () {
        $companyForm[0].reset();
        $companyForm.removeData('company-id');
        $companyForm.data('mode', 'create');
        $('#companyId').val('');
        $('#companyModalLabel').text('Add New Company');
        $saveCompanyBtn.text('Save Company').prop('disabled', false);
        
        // Remove 'new-entry' class from all rows when adding new
        $('#companiesTableBody tr').removeClass('new-entry');

        populateCompanyGroupDropdown('#companyGroup', GROUP_LIST_API_ENDPOINT);
    });

    $saveCompanyBtn.on('click', handleCompanyFormSubmission);
    $companyForm.on('submit', handleCompanyFormSubmission);

    // --- Update Button Handler (Unchanged) ---
    $updateCompanyBtn.on('click', function () {
        const selectedIds = getSelectedCompanyIds();
        if (!validateSelectionAndShowModal('update', selectedIds)) {
            return; 
        }

        const companyId = selectedIds[0];
        const $row = $companyTableBody.find(`input[value="${companyId}"]`).closest('tr');
        const companyData = getDataFromRow($row);

        $('#companyName').val(companyData.companyName);
        $('#crNumber').val(companyData.crNumber);
        $('#vatNumber').val(companyData.vatNumber);
        $('#contactName').val(companyData.contactName);
        $('#emailAddress').val(companyData.emailAddress);
        $('#mobile').val(companyData.mobile);
        $('#phone').val(companyData.phone);
        // NOTE: companyDetails and addressText are not in the table rows, 
        // they must be fetched via a dedicated AJAX call for update mode if needed.
        // For simplicity, they remain empty here unless fetched.
        $('#companyDetails').val(companyData.companyDetails); 
        $('#addressText').val(companyData.addressText); 

        $companyForm.data('mode', 'update');
        $companyForm.data('company-id', companyId);
        $('#companyModalLabel').text('Update Company Details');
        $saveCompanyBtn.text('Update Company').prop('disabled', false);

        populateCompanyGroupDropdown('#companyGroup', GROUP_LIST_API_ENDPOINT, companyData.companyGroup);

        const modalInstance = bootstrap.Modal.getOrCreateInstance($companyModal[0]);
        modalInstance.show();
    });

    // --- Delete Handlers (Unchanged) ---
    $deleteSelectedBtn.on('click', function(e) {
        e.preventDefault(); 
        const selectedIds = getSelectedCompanyIds();
        
        if (!validateSelectionAndShowModal('delete', selectedIds)) {
            return;
        }

        if ($deleteModal.length === 0) {
            console.error("!!! FATAL ERROR: Delete modal (#deleteConfirmModal) not found in the DOM.");
            showCustomMessageModal('System Error', 'The delete confirmation window could not be loaded. Check console for details.', false, 'bg-danger', 'btn-danger', 'bi-x-octagon-fill');
            return;
        }

        const msg = `Are you sure you want to permanently delete **${selectedIds.length}** selected company record(s)?`;
        $deleteModal.find('.modal-body p:first').html(msg); 
        
        const modalInstance = bootstrap.Modal.getOrCreateInstance($deleteModal[0]);
        modalInstance.show();
    });
    
    $confirmDeleteBtn.on('click', function() {
        const selectedIds = getSelectedCompanyIds();
        
        const modalInstance = bootstrap.Modal.getOrCreateInstance($deleteModal[0]);
        modalInstance.hide();
        $confirmDeleteBtn.prop('disabled', true).text('Deleting...');

        $.ajax({
            url: DELETE_COMPANIES_API_ENDPOINT,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ ids: selectedIds }),
            headers: { 'X-CSRFToken': getCSRFToken() },
            success: function(response) {
                selectedIds.forEach(id => {
                    $(`#companiesTableBody input[value="${id}"]`).closest('tr').remove();
                });
                
                if ($('#companiesTableBody tr').length === 0) {
                    $('#companiesTableBody').html('<tr><td colspan="9" class="text-center text-muted">No company records found</td></tr>');
                }
                
                showCustomMessageModal('Deletion Success', 
                                        response.message, 
                                        true,
                                        'bg-success',
                                        'btn-success',
                                        'bi-check-circle-fill'
                                    );
            },
            error: function(xhr) {
                const errorDetail = xhr.responseJSON ? xhr.responseJSON.error : xhr.statusText;
                showCustomMessageModal('Deletion Error', 
                                        `Could not delete records: ${errorDetail}`, 
                                        false,
                                        'bg-danger',
                                        'btn-danger',
                                        'bi-x-octagon-fill'
                                    );
            },
            complete: function() {
                $confirmDeleteBtn.prop('disabled', false).text('Confirm Delete');
            }
        });
    });

    // --------------------------------------------------------
    // ⭐ CLIENT-SIDE TABLE FILTERING LOGIC ⭐
    // Filters on: Company Name, Group, Contact Name, Email Address, Mobile, Phone
    // --------------------------------------------------------
    if ($searchTableInput.length) {
        // Use the 'input' event for live filtering as the user types
        $searchTableInput.on('input', function() {
            const searchTerm = $(this).val().toLowerCase().trim();
            let rowCount = 0;
            const $noResultsRow = $companyTableBody.find('tr.no-results-row-client');

            // Show all rows if the search term is empty
            if (searchTerm.length === 0) {
                $companyTableBody.find('tr').show();
                $noResultsRow.remove();
                // We stop here to rely on the server-rendered page count
                return;
            }

            // Iterate over all table rows in the tbody (excluding the temporary no-results row)
            $companyTableBody.find('tr:not(.no-results-row-client)').each(function() {
                const $row = $(this);
                const $cells = $row.find('td');

                // Indices of the columns to search (0-based, skipping checkbox at 0):
                // 1: Company Name
                // 2: Group
                // 5: Contact Name
                // 6: Email Address
                // 7: Mobile
                // 8: Phone
                
                // Collect and normalize the text from the target columns
                const companyName = $cells.eq(1).text().toLowerCase();
                const groupName = $cells.eq(2).text().toLowerCase();
                const contactName = $cells.eq(5).text().toLowerCase();
                const emailAddress = $cells.eq(6).text().toLowerCase();
                const mobile = $cells.eq(7).text().toLowerCase();
                const phone = $cells.eq(8).text().toLowerCase();

                // Check if the search term is found in any of the target columns
                const isMatch = (
                    companyName.includes(searchTerm) ||
                    groupName.includes(searchTerm) ||
                    contactName.includes(searchTerm) ||
                    emailAddress.includes(searchTerm) ||
                    mobile.includes(searchTerm) ||
                    phone.includes(searchTerm)
                );

                if (isMatch) {
                    $row.show();
                    rowCount++;
                } else {
                    $row.hide();
                }
            });

            // Handle 'No records found' message for client-side search
            if (rowCount === 0) {
                if ($noResultsRow.length === 0) {
                     // Add the "No results" row if none exists
                     $companyTableBody.append('<tr class="no-results-row-client"><td colspan="9" class="text-center text-muted">No records found matching your current filter.</td></tr>');
                } else {
                    // Show it if it was previously hidden
                    $noResultsRow.show();
                }
            } else {
                // Remove the "No results" row when matches are found
                $noResultsRow.remove();
            }

        });
    }

    // --------------------------------------------------------
    // ⭐ AJAX Search Listener (REMOVED/MODIFIED) ⭐
    // NOTE: If you decide to go back to server-side search, 
    // you must re-implement this, possibly using the $searchTableInput ID.
    // I am commenting out the original block to favor the client-side filter above.
    // --------------------------------------------------------
    /*
    if (searchInput) { // Assumes searchInput is linked to a different ID than #search
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);

            searchTimeout = setTimeout(() => {
                const searchTerm = searchInput.value.trim();
                
                if (searchTerm.length > 0) {
                    fetchAndRenderCompanies(searchTerm);
                } else {
                    window.location.reload(); 
                }
            }, 300); // 300 milliseconds debounce time
        });
    }
    */
    // --------------------------------------------------------

    // --- Final Cleanup (Unchanged) ---
    $('#companiesTableBody tr:not(:first-child)').removeClass('new-entry');

    // =======================================================
    // IX. Export Button (Unchanged)
    // =======================================================
    const exportBtn = document.getElementById("exportBtn");

    if (exportBtn) {
        const COMPANY_EXPORT_URL = "/housing/company/export/"; 
        
        exportBtn.addEventListener("click", () => {
            const originalContent = exportBtn.innerHTML;
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';
            
            window.location.href = COMPANY_EXPORT_URL;
            
            setTimeout(() => {
                exportBtn.disabled = false;
                exportBtn.innerHTML = originalContent;
            }, 2000);
        });
    }
});