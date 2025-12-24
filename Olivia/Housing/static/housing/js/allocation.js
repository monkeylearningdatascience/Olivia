/* allocation.js - Unit Allocation CRUD operations */

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

function getSelectedAllocationIds() {
    return $('#allocationTableBody').find('input.select-entry:checked').map(function () {
        return $(this).val();
    }).get();
}

// =======================================================
// Modal Management
// =======================================================

function openAllocationModal(mode = 'create', allocationId = null) {
    const $modal = $('#allocationModal');
    const $form = $('#allocationForm');
    const $title = $('#allocationModalLabel');
    const $saveBtn = $('#saveAllocationBtn');

    $form[0].reset();
    $('#allocationId').val('');

    if (mode === 'create') {
        $title.text('Add New Allocation');
        $saveBtn.text('Save');
        $modal.modal('show');
    } else if (mode === 'update' && allocationId) {
        $title.text('Update Allocation');
        $saveBtn.text('Update');

        $.ajax({
            url: `/housing/allocation/update/${allocationId}/`,
            type: 'GET',
            success: function (data) {
                $('#allocationId').val(data.id);
                $('#allocationType').val(data.allocation_type);
                $('#uuaNumber').val(data.uua_number);
                $('#companyGroup').val(data.company_group);
                
                // Filter companies based on selected group, then set company value
                filterCompaniesByGroup(data.company_group, data.company);
                
                $('#startDate').val(data.start_date);
                $('#endDate').val(data.end_date);
                $('#aRoomsBeds').val(data.a_rooms_beds);
                $('#bRoomsBeds').val(data.b_rooms_beds);
                $('#cRoomsBeds').val(data.c_rooms_beds);
                $('#dRoomsBeds').val(data.d_rooms_beds);
                $('#allocationStatus').val(data.allocation_status);
                $('#securityDeposit').val(data.security_deposit);
                $('#advancePayment').val(data.advance_payment);

                $modal.modal('show');
            },
            error: function (xhr) {
                showCustomMessageModal('Error', 'Failed to load allocation data', false);
            }
        });
    }
}

function filterCompaniesByGroup(groupId, selectedCompanyId = null) {
    const $companySelect = $('#company');
    
    console.log('Filtering companies for group ID:', groupId);
    
    // Show all options first
    $companySelect.find('option').show();
    
    if (groupId) {
        let hiddenCount = 0;
        let visibleCount = 0;
        
        // Hide options that don't match the selected group
        $companySelect.find('option').each(function () {
            const $option = $(this);
            const optionValue = $option.val();
            
            if (optionValue !== '') {
                const optionGroupId = $option.data('group');
                console.log('Company:', $option.text(), 'Group ID:', optionGroupId, 'Selected Group:', groupId);
                
                if (optionGroupId != groupId) {
                    $option.hide();
                    hiddenCount++;
                } else {
                    visibleCount++;
                }
            }
        });
        
        console.log('Visible companies:', visibleCount, 'Hidden companies:', hiddenCount);
    }
    
    // Set the selected company if provided, otherwise reset
    if (selectedCompanyId) {
        $companySelect.val(selectedCompanyId);
    } else {
        $companySelect.val('');
    }
}

// =======================================================
// CRUD Operations
// =======================================================

function handleAllocationSubmit(e) {
    e.preventDefault();

    const allocationId = $('#allocationId').val();
    const isUpdate = !!allocationId;
    const url = isUpdate 
        ? `/housing/allocation/update/${allocationId}/`
        : '/housing/allocation/create/';

    const formData = new FormData(document.getElementById('allocationForm'));

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function (response) {
            if (response.success) {
                $('#allocationModal').modal('hide');
                showCustomMessageModal(
                    'Success',
                    isUpdate ? 'Allocation updated successfully' : 'Allocation created successfully',
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

function deleteSelectedAllocations() {
    const selectedIds = getSelectedAllocationIds();

    if (selectedIds.length === 0) {
        showCustomMessageModal('Warning', 'Please select at least one allocation to delete', false);
        return;
    }

    if (selectedIds.length > 1) {
        showCustomMessageModal('Warning', 'Please select only one allocation at a time', false);
        return;
    }

    $('#deleteConfirmationModal').modal('show');
}

function confirmDelete() {
    const selectedIds = getSelectedAllocationIds();

    $.ajax({
        url: '/housing/allocation/delete/',
        type: 'POST',
        data: {
            allocation_id: selectedIds[0],
            csrfmiddlewaretoken: getCSRFToken()
        },
        success: function (response) {
            if (response.success) {
                $('#deleteConfirmationModal').modal('hide');
                showCustomMessageModal('Success', 'Allocation deleted successfully', true);
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
    $('#allocationTableBody tr').each(function () {
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
    $('#allocationTableBody').find('input.select-entry').prop('checked', isChecked);
}

// =======================================================
// Event Listeners
// =======================================================

$(document).ready(function () {
    // Create button
    $('#addNewAllocationBtn').on('click', function () {
        openAllocationModal('create');
    });

    // Update button
    $('#updateAllocationBtn').on('click', function () {
        const selectedIds = getSelectedAllocationIds();

        if (selectedIds.length === 0) {
            showCustomMessageModal('Warning', 'Please select an allocation to update', false);
            return;
        }

        if (selectedIds.length > 1) {
            showCustomMessageModal('Warning', 'Please select only one allocation at a time', false);
            return;
        }

        openAllocationModal('update', selectedIds[0]);
    });

    // Double-click on row to edit
    $('#allocationTableBody').on('dblclick', 'tr', function () {
        const allocationId = $(this).find('input.select-entry').val();
        if (allocationId) {
            openAllocationModal('update', allocationId);
        }
    });

    // Form submit
    $('#allocationForm').on('submit', handleAllocationSubmit);

    // Delete buttons
    $('#deleteSelectedBtn').on('click', deleteSelectedAllocations);
    $('#confirmDeleteBtn').on('click', confirmDelete);

    // Search
    $('#search').on('keyup', handleSearch);

    // Select all
    $('#selectAll').on('change', handleSelectAll);

    // Company group filter - on modal open and on change
    $('#companyGroup').on('change', function () {
        const groupId = $(this).val();
        filterCompaniesByGroup(groupId);
    });

    // Filter companies when modal opens
    $('#allocationModal').on('shown.bs.modal', function () {
        const groupId = $('#companyGroup').val();
        const currentCompany = $('#company').val(); // Preserve current selection
        if (groupId) {
            filterCompaniesByGroup(groupId, currentCompany);
        }
    });

    // Export button
    $('#exportBtn').on('click', function () {
        const searchQuery = $('#search').val();
        let exportUrl = '/housing/allocation/export/';
        if (searchQuery) {
            exportUrl += `?q=${encodeURIComponent(searchQuery)}`;
        }
        window.location.href = exportUrl;
    });
});
