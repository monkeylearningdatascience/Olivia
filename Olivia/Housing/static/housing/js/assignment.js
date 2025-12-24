/* assignment.js - Unit Assignment CRUD operations with auto-population */

// =======================================================
// Global Utilities
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

function showCustomMessageModal(title, bodyHtml, isSuccess = true) {
    const $modal = $('#viewSelectionModal');
    if ($modal.length === 0) {
        alert(`${title}: ${bodyHtml.replace(/<br>/g, '\n')}`);
        return;
    }
    
    const headerClass = isSuccess ? 'bg-success' : 'bg-danger';
    const btnClass = isSuccess ? 'btn-success' : 'btn-danger';
    
    $modal.find('.modal-header').removeClass('bg-success bg-danger bg-primary bg-light').addClass(headerClass);
    $modal.find('#viewSelectionModalLabel').html(title);
    $modal.find('.modal-body').html(bodyHtml);
    
    const $okBtn = $modal.find('.modal-footer button');
    $okBtn.removeClass('btn-outline-secondary btn-primary btn-danger btn-success btn-light btn-secondary')
        .addClass(btnClass).text('OK');
    
    const modalInstance = bootstrap.Modal.getOrCreateInstance($modal[0]);
    modalInstance.show();
}

function getSelectedAssignmentIds() {
    return $('#assignmentTableBody').find('input.select-entry:checked').map(function () {
        return $(this).val();
    }).get();
}

// =======================================================
// Auto-Population Functions
// =======================================================

function filterCompaniesByGroup(groupId) {
    const $companySelect = $('#company');
    
    // Show all options first
    $companySelect.find('option').show();
    
    if (groupId) {
        // Hide options that don't match the selected group
        $companySelect.find('option').each(function () {
            const $option = $(this);
            if ($option.val() !== '') {
                const optionGroupId = $option.data('group');
                if (optionGroupId != groupId) {
                    $option.hide();
                }
            }
        });
    }
    
    // Reset selection
    $companySelect.val('');
}

function fetchAllocationsByCompany(companyId) {
    if (!companyId) {
        clearAllocationFields();
        return;
    }

    // Show loading state
    console.log('Fetching allocations for company:', companyId);

    $.ajax({
        url: '/housing/assignment/get-allocations-by-company/',
        type: 'GET',
        data: { company_id: companyId },
        dataType: 'json',
        timeout: 5000, // 5 second timeout
        success: function (data) {
            console.log('Allocations received:', data);
            
            if (data && data.length > 0) {
                if (data.length === 1) {
                    // Single allocation - show as readonly input
                    const allocation = data[0];
                    $('#allocationId').val(allocation.id);
                    $('#allocationType').hide();
                    $('#allocationTypeInput').val(allocation.allocation_type).show();
                    $('#uuaNumber').val(allocation.uua_number);
                    $('#startDate').val(allocation.start_date);
                    $('#endDate').val(allocation.end_date);
                } else {
                    // Multiple allocations - show as dropdown
                    const $select = $('#allocationType');
                    $select.empty().append('<option value="">Select Allocation...</option>');
                    data.forEach(allocation => {
                        $select.append(`<option value="${allocation.id}" 
                            data-type="${allocation.allocation_type}"
                            data-uua="${allocation.uua_number}"
                            data-start="${allocation.start_date}"
                            data-end="${allocation.end_date}">
                            ${allocation.allocation_type} - ${allocation.uua_number}
                        </option>`);
                    });
                    $('#allocationTypeInput').hide();
                    $select.show();
                }
            } else {
                clearAllocationFields();
                showCustomMessageModal('Info', 'No active allocation found for this company', false);
            }
        },
        error: function (xhr, status, error) {
            console.error('Error fetching allocations:', status, error);
            clearAllocationFields();
            showCustomMessageModal('Error', 'Failed to fetch allocation details: ' + error, false);
        }
    });
}

function handleAllocationSelection() {
    const $selected = $('#allocationType option:selected');
    const allocationId = $selected.val();
    
    if (allocationId) {
        $('#allocationId').val(allocationId);
        $('#uuaNumber').val($selected.data('uua'));
        $('#startDate').val($selected.data('start'));
        $('#endDate').val($selected.data('end'));
    }
}

function populateUnitDetails(unitId) {
    const $selected = $(`#unit option[value="${unitId}"]`);
    
    if ($selected.length) {
        $('#zone').val($selected.data('zone') || '');
        $('#area').val($selected.data('area') || '');
        $('#block').val($selected.data('block') || '');
        $('#building').val($selected.data('building') || '');
        $('#floor').val($selected.data('floor') || '');
    } else {
        clearUnitDetails();
    }
}

function filterUnitsByType(accommodationType) {
    const $unitSelect = $('#unit');
    
    console.log('Filtering units by type:', accommodationType);
    
    // Show all options first
    $unitSelect.find('option').show();
    
    if (accommodationType) {
        let visibleCount = 0;
        let hiddenCount = 0;
        
        // Hide options that don't match the selected type
        $unitSelect.find('option').each(function () {
            const $option = $(this);
            const optionValue = $option.val();
            
            if (optionValue !== '') {
                const unitType = $option.data('type');
                console.log('Unit:', $option.text(), 'Type:', unitType, 'Looking for:', accommodationType);
                
                // Check if unit type starts with accommodation type (e.g., "B (1 * 1)" starts with "B")
                if (unitType && String(unitType).trim().toUpperCase().startsWith(String(accommodationType).trim().toUpperCase())) {
                    $option.show();
                    visibleCount++;
                } else {
                    $option.hide();
                    hiddenCount++;
                }
            }
        });
        
        console.log('Visible units:', visibleCount, 'Hidden units:', hiddenCount);
        
        if (visibleCount === 0) {
            console.warn('No units found for type:', accommodationType);
        }
    }
    
    // Reset selection
    $unitSelect.val('');
    clearUnitDetails();
}

function clearAllocationFields() {
    $('#allocationId').val('');
    $('#allocationType').hide().empty();
    $('#allocationTypeInput').hide().val('');
    $('#uuaNumber').val('');
    $('#startDate').val('');
    $('#endDate').val('');
}

function clearUnitDetails() {
    $('#zone').val('');
    $('#area').val('');
    $('#block').val('');
    $('#building').val('');
    $('#floor').val('');
}

// =======================================================
// Modal Management
// =======================================================

function openAssignmentModal(mode = 'create', assignmentId = null) {
    const $modal = $('#assignmentModal');
    const $form = $('#assignmentForm');
    const $title = $('#assignmentModalLabel');
    const $saveBtn = $('#saveAssignmentBtn');

    $form[0].reset();
    $('#assignmentId').val('');
    clearAllocationFields();

    if (mode === 'create') {
        $title.text('Add New Assignment');
        $saveBtn.text('Save');
        $modal.modal('show');
    } else if (mode === 'update' && assignmentId) {
        $title.text('Update Assignment');
        $saveBtn.text('Update');

        $.ajax({
            url: `/housing/assignment/update/${assignmentId}/`,
            type: 'GET',
            success: function (data) {
                $('#assignmentId').val(data.id);
                $('#allocationId').val(data.allocation_id);
                
                // Set company group and trigger change to filter companies
                $('#companyGroup').val(data.company_group_id);
                filterCompaniesByGroup(data.company_group_id);
                
                // Set company and enable it
                $('#company').val(data.company_id).prop('disabled', false);
                
                // Populate allocation fields
                $('#allocationType').val(data.allocation_type);
                $('#uuaNumber').val(data.uua_number);
                $('#startDate').val(data.start_date);
                $('#endDate').val(data.end_date);
                
                // Set accommodation type and enable it
                $('#accommodationType').append(`<option value="${data.accommodation_type}">${data.accommodation_type}</option>`);
                $('#accommodationType').val(data.accommodation_type).prop('disabled', false);
                
                // Set unit and enable it
                $('#unit').val(data.unit_id).prop('disabled', false);
                
                // Populate unit details
                $('#zone').val(data.zone);
                $('#area').val(data.area);
                $('#block').val(data.block);
                $('#building').val(data.building);
                $('#floor').val(data.floor);

                $modal.modal('show');
            },
            error: function (xhr) {
                showCustomMessageModal('Error', 'Failed to load assignment data', false);
            }
        });
    }
}

// =======================================================
// CRUD Operations
// =======================================================

function handleAssignmentSubmit(e) {
    e.preventDefault();

    const assignmentId = $('#assignmentId').val();
    const isUpdate = !!assignmentId;
    const url = isUpdate 
        ? `/housing/assignment/update/${assignmentId}/`
        : '/housing/assignment/create/';

    const formData = new FormData(document.getElementById('assignmentForm'));

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function (response) {
            if (response.success) {
                $('#assignmentModal').modal('hide');
                showCustomMessageModal(
                    'Success',
                    isUpdate ? 'Assignment updated successfully' : 'Assignment created successfully',
                    true
                );
                setTimeout(() => location.reload(), 1000);
            } else {
                showCustomMessageModal('Error', response.error || 'Operation failed', false);
            }
        },
        error: function (xhr) {
            const errorMsg = xhr.responseJSON?.error || 'An error occurred';
            showCustomMessageModal('Error', errorMsg, false);
        }
    });
}

function deleteSelectedAssignments() {
    const selectedIds = getSelectedAssignmentIds();

    if (selectedIds.length === 0) {
        showCustomMessageModal('Warning', 'Please select at least one assignment to delete', false);
        return;
    }

    if (selectedIds.length > 1) {
        showCustomMessageModal('Warning', 'Please select only one assignment at a time', false);
        return;
    }

    $('#deleteConfirmationModal').modal('show');
}

function confirmDelete() {
    const selectedIds = getSelectedAssignmentIds();

    $.ajax({
        url: '/housing/assignment/delete/',
        type: 'POST',
        data: {
            assignment_id: selectedIds[0],
            csrfmiddlewaretoken: getCSRFToken()
        },
        success: function (response) {
            if (response.success) {
                $('#deleteConfirmationModal').modal('hide');
                showCustomMessageModal('Success', 'Assignment deleted successfully', true);
                setTimeout(() => location.reload(), 1000);
            } else {
                showCustomMessageModal('Error', response.error || 'Delete failed', false);
            }
        },
        error: function (xhr) {
            const errorMsg = xhr.responseJSON?.error || 'An error occurred';
            showCustomMessageModal('Error', errorMsg, false);
        }
    });
}

// =======================================================
// Search Functionality
// =======================================================

function handleSearch() {
    const searchTerm = $('#search').val().toLowerCase();
    $('#assignmentTableBody tr').each(function () {
        const $row = $(this);
        const text = $row.text().toLowerCase();
        $row.toggle(text.includes(searchTerm));
    });
}

// =======================================================
// Select All Functionality
// =======================================================

function handleSelectAll() {
    const isChecked = $('#selectAll').prop('checked');
    $('#assignmentTableBody').find('input.select-entry').prop('checked', isChecked);
}

// =======================================================
// Event Listeners
// =======================================================

$(document).ready(function () {
    // Create button
    $('#addNewAssignmentBtn').on('click', function () {
        openAssignmentModal('create');
    });

    // Update button
    $('#updateAssignmentBtn').on('click', function () {
        const selectedIds = getSelectedAssignmentIds();

        if (selectedIds.length === 0) {
            showCustomMessageModal('Warning', 'Please select an assignment to update', false);
            return;
        }

        if (selectedIds.length > 1) {
            showCustomMessageModal('Warning', 'Please select only one assignment at a time', false);
            return;
        }

        openAssignmentModal('update', selectedIds[0]);
    });

    // Double-click on row to edit
    $('#assignmentTableBody').on('dblclick', 'tr', function () {
        const assignmentId = $(this).find('input.select-entry').val();
        if (assignmentId) {
            openAssignmentModal('update', assignmentId);
        }
    });

    // Form submit
    $('#assignmentForm').on('submit', handleAssignmentSubmit);

    // Delete buttons
    $('#deleteSelectedBtn').on('click', deleteSelectedAssignments);
    $('#confirmDeleteBtn').on('click', confirmDelete);

    // Search
    $('#search').on('keyup', handleSearch);

    // Select all
    $('#selectAll').on('change', handleSelectAll);

    // Company Group change - filter companies
    $('#companyGroup').on('change', function () {
        const groupId = $(this).val();
        filterCompaniesByGroup(groupId);
        clearAllocationFields();
        clearUnitDetails();
    });

    // Company change - fetch allocations
    $('#company').on('change', function () {
        const companyId = $(this).val();
        fetchAllocationsByCompany(companyId);
        clearUnitDetails();
    });

    // Allocation Type dropdown change (when multiple allocations)
    $('#allocationType').on('change', handleAllocationSelection);

    // Accommodation Type change - filter units by type
    $('#accommodationType').on('change', function () {
        const selectedType = $(this).val();
        filterUnitsByType(selectedType);
    });

    // Unit change - populate unit details
    $('#unit').on('change', function () {
        const unitId = $(this).val();
        populateUnitDetails(unitId);
    });

    // Export button
    $('#exportBtn').on('click', function () {
        const searchQuery = $('#search').val();
        let exportUrl = '/housing/assignment/export/';
        if (searchQuery) {
            exportUrl += `?q=${encodeURIComponent(searchQuery)}`;
        }
        window.location.href = exportUrl;
    });
});
