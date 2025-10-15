// Global utility to get CSRF Token
function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenElement ? tokenElement.value : null; 
}

// --- NEW FUNCTION: Populates the main Company Group dropdown using the working API ---
function populateCompanyGroupDropdown(selectElement, listApiEndpoint) {
    const $select = $(selectElement);

    $.ajax({
        url: listApiEndpoint,
        type: 'GET',
        dataType: 'json',
        success: function(groups) {
            // Preserve the first option ("Select Group...")
            const selectedValue = $select.val(); // Remember the currently selected value (for editing)
            $select.find('option:not(:first)').remove(); 
            
            groups.forEach(function(group) {
                const newOption = `<option value="${group.id}">${group.company_name}</option>`;
                $select.append(newOption);
            });
            
            // Re-select the value if one was selected before reloading
            if (selectedValue) {
                $select.val(selectedValue);
            }

            console.log(`Company Group dropdown populated with ${groups.length} items via AJAX.`);
        },
        error: function(xhr, status, error) {
            console.error("Error loading groups for dropdown via AJAX:", status, error);
        }
    });
}
// --------------------------------------------------------------------------------------


$(document).ready(function() {
    // --- Caching Selectors and Constants ---
    const CSRF_TOKEN = getCSRFToken();

    // Company (Main) Modal Selectors
    const $companyModal = $('#companyModal');
    const $companyForm = $('#companyForm');
    const $companiesTableBody = $('#companiesTableBody');
    const $saveCompanyBtn = $('#saveCompanyBtn');
    const $companyGroupSelect = $('#companyGroup'); // Dropdown in the main company modal
    const COMPANY_API_ENDPOINT = '/housing/companies/create/'; 

    // Company Group Modal Selectors
    const $companyGroupModal = $('#companyGroupModal');
    const $companyGroupForm = $('#companyGroupForm');
    const $saveGroupBtn = $('#saveGroupBtn');
    const $existingGroupsList = $('#existingGroupsList'); // Container for listing existing groups
    // CRITICAL: Ensure these URLs match your Django urls.py exactly!
    const GROUP_API_ENDPOINT = '/housing/groups/create/'; 
    const GROUP_LIST_API_ENDPOINT = '/housing/groups/list/'; 
    // const GROUP_DELETE_API_ENDPOINT = '/api/groups/delete/'; // Placeholder for future delete

    // --- INITIAL DATA LOAD ---
    // CRITICAL: Call the new function to load the dropdown on page load
    populateCompanyGroupDropdown($companyGroupSelect, GROUP_LIST_API_ENDPOINT);
    // -------------------------


    // --- 1. Company (Main) Modal Logic ---

    // Handle Modal Opening/Reset
    $('#addNewCompanyBtn').on('click', function() {
        $companyForm[0].reset();
        $('#companyId').val('');
        $('#companyModalLabel').text('Add New Company');
        $saveCompanyBtn.text('Save Company').prop('disabled', false);
        // Ensure dropdown is freshly loaded when adding new company (optional)
        populateCompanyGroupDropdown($companyGroupSelect, GROUP_LIST_API_ENDPOINT);
    });

    // Handle Company Form Submission (Create/Update)
    $companyForm.on('submit', function(e) {
        e.preventDefault();
        $saveCompanyBtn.prop('disabled', true).text('Saving...');

        // Collect form data
        const formData = {
            company_name: $('#companyName').val(),
            company_group: $('#companyGroup').val() || null, 
            company_details: $('#companyDetails').val(),
            cr_number: $('#crNumber').val(),
            vat_number: $('#vatNumber').val(),
            address_text: $('#addressText').val(),
            contact_name: $('#contactName').val(),
            email_address: $('#emailAddress').val(),
            mobile: $('#mobile').val(),
            phone: $('#phone').val(),
        };

        // AJAX Request for saving Company
        $.ajax({
            url: COMPANY_API_ENDPOINT,
            type: 'POST', 
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log('Company saved successfully:', response);
                addNewRowToTable(response);
                $companyModal.modal('hide');
                $companyForm[0].reset();
                alert('Company record saved successfully!'); 
            },
            error: function(xhr) {
                console.error('Error saving company:', xhr.responseText);
                let errorMessage = `Error (Status: ${xhr.status}): `;
                try {
                    const errorJson = JSON.parse(xhr.responseText);
                    errorMessage += errorJson.error || JSON.stringify(errorJson, null, 2); 
                } catch (e) {
                    errorMessage += xhr.statusText;
                }
                
                alert('Error saving company:\n' + errorMessage);
            },
            complete: function() {
                $saveCompanyBtn.prop('disabled', false).text('Save Company');
            }
        });
    });

    // Function to dynamically add a new row
    function addNewRowToTable(company) {
        if ($companiesTableBody.find('tr').length === 1 && $companiesTableBody.find('tr td').attr('colspan') === '10') {
            $companiesTableBody.empty();
        }

        const groupName = company.company_group_name || company.company_group || '-';
        
        const newRow = `
            <tr data-id="${company.id}">
                <td><input type="checkbox" class="select-entry" value="${company.id}"></td>
                <td>${company.company_name}</td>
                <td>${groupName}</td>
                <td>${company.cr_number || '-'}</td>
                <td>${company.vat_number || '-'}</td>
                <td>${company.contact_name || '-'}</td>
                <td>${company.email_address || '-'}</td>
                <td>${company.mobile || '-'}</td>
                <td>${company.phone || '-'}</td>
                <td class="text-center">
                    <span class="badge bg-secondary" data-bs-toggle="tooltip" 
                             title="${company.company_details || 'No details provided'}">
                             View
                    </span>
                </td>
            </tr>
        `;

        $companiesTableBody.prepend(newRow);
    }
    
    // --- 2. Company Group Modal Logic ---

    // Function to fetch and display existing groups (for the list in the group modal)
    function loadExistingGroups() {
        $existingGroupsList.html('<li class="list-group-item text-center text-muted">Loading groups...</li>');
        
        $.ajax({
            url: GROUP_LIST_API_ENDPOINT,
            type: 'GET',
            success: function(groups) {
                $existingGroupsList.empty();

                if (groups.length === 0) {
                    $existingGroupsList.html('<li class="list-group-item text-center text-muted">No groups found. Create one above!</li>');
                    return;
                }

                groups.forEach(group => {
                    const listItem = `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            ${group.company_name}
                            <div>
                                <button type="button" class="btn btn-sm btn-outline-danger delete-group-btn" data-id="${group.id}">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </li>
                    `;
                    $existingGroupsList.append(listItem);
                });
            },
            error: function(xhr) {
                console.error("Error loading groups. Status: " + xhr.status, xhr);
                $existingGroupsList.html(`<li class="list-group-item text-center text-danger">Error loading groups (Status: ${xhr.status}). Check console.</li>`);
            }
        });
    }

    // Handle Group Modal Opening/Reset
    $companyGroupModal.on('show.bs.modal', function () {
        $companyGroupForm[0].reset();
        $('#companyGroupId').val('');
        $('#groupName').focus(); // Focus on the input
        $('#companyGroupModalLabel').html('<i class="bi bi-people-fill me-2"></i>Manage Company Groups');
        $saveGroupBtn.text('Save Group').prop('disabled', false);

        // Load existing groups for the list when the modal opens
        loadExistingGroups();
    });

    // Handle Company Group Form Submission (Saves to CompanyGroup DB)
    $companyGroupForm.on('submit', function(e) {
        e.preventDefault();
        $saveGroupBtn.prop('disabled', true).text('Saving...');

        const formData = {
            company_name: $('#groupName').val(),
        };
        
        $.ajax({
            url: GROUP_API_ENDPOINT,
            type: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            },
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log('Group saved successfully:', response);
                
                // 1. ADD NEW GROUP TO DROPDOWN (via the new function)
                // We'll call the populate function to refresh the *entire* list, 
                // ensuring the new group is added in the correct alphabetical order (if Django orders it).
                populateCompanyGroupDropdown($companyGroupSelect, GROUP_LIST_API_ENDPOINT);

                // 2. Automatically select the newly created group (must happen AFTER population)
                $companyGroupSelect.val(response.id); 

                // 3. Close the group modal and notify user
                $companyGroupModal.modal('hide');
                alert(`Company Group "${response.company_name}" created and selected.`);
                
                // 4. Reset the form after success
                $companyGroupForm[0].reset();
            },
            error: function(xhr) {
                console.error('Error saving group:', xhr.responseText);
                let errorMsg = `Error (Status: ${xhr.status}): `;
                try {
                    const errorJson = JSON.parse(xhr.responseText);
                    errorMsg += errorJson.error || JSON.stringify(errorJson, null, 2);
                } catch (e) {
                    errorMsg += xhr.statusText;
                }
                alert('Error saving Group: ' + errorMsg);
            },
            complete: function() {
                // Re-enable button after success or failure
                $saveGroupBtn.prop('disabled', false).text('Save Group');
            }
        });
    });
});