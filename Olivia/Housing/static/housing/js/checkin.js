/* checkin.js - Check-In/Check-Out CRUD operations */

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
    const modal = $('#viewSelectionModal');
    modal.find('.modal-title').text(title);
    modal.find('.modal-body p').html(bodyHtml);
    modal.modal('show');
}

function getSelectedCheckinIds() {
    return $('#checkinTableBody').find('input.select-entry:checked').map(function () {
        return $(this).val();
    }).get();
}

// =======================================================
// Modal Management
// =======================================================

function openCheckinModal(mode = 'create', checkinId = null) {
    const $modal = $('#checkinModal');
    const $form = $('#checkinForm');
    const $title = $('#checkinModalLabel');
    const $saveBtn = $('#saveCheckinBtn');

    $form[0].reset();
    $('#checkinId').val('');
    
    // Clear all auto-populated fields
    $('#allocationType, #uuaNumber, #allocationCode, #companyGroup, #company, #startDate, #endDate, #accomodationType, #unitNumber, #unitLocationCode, #govtIdNumber, #idType, #neomId, #dob, #mobileNumber, #email, #nationality, #religion, #occupancyStatus, #actualStayDuration').val('');

    if (mode === 'create') {
        $title.text('Add Check-In/Check-Out');
        $saveBtn.text('Save');
        // Disable checkout field in create mode
        $('#actualCheckoutDatetime').prop('disabled', true).val('');
        // Show dropdown, hide readonly field
        $('#reservation').show().prop('disabled', false).prop('required', true);
        $('#reservationReadonly').hide();
        $('#reservationValue').removeAttr('name');
        $('#reservation').attr('name', 'reservation');
        $modal.modal('show');
    } else if (mode === 'update' && checkinId) {
        $title.text('Update Check-In/Check-Out');
        $saveBtn.text('Update');

        $.ajax({
            url: `/housing/checkin/update/${checkinId}/`,
            type: 'GET',
            success: function (data) {
                $('#checkinId').val(data.id);
                
                // Hide dropdown, show readonly field with reservation username
                $('#reservation').hide().prop('required', false).removeAttr('name');
                $('#reservationReadonly').val(data.reservation_username || '').show();
                $('#reservationValue').val(data.reservation).attr('name', 'reservation');
                
                $('#actualCheckinDatetime').val(data.actual_checkin_datetime);
                $('#actualCheckoutDatetime').val(data.actual_checkout_datetime);
                $('#actualStayDuration').val(data.actual_stay_duration);
                $('#remarks').val(data.remarks || '');
                
                // Populate all auto-populated fields from reservation data
                $('#allocationType').val(data.allocation_type || '');
                $('#uuaNumber').val(data.uua_number || '');
                $('#allocationCode').val(data.allocation_code || '');
                $('#companyGroup').val(data.company_group || '');
                $('#company').val(data.company || '');
                $('#startDate').val(data.start_date || '');
                $('#endDate').val(data.end_date || '');
                $('#accomodationType').val(data.accomodation_type || '');
                $('#unitNumber').val(data.unit || '');
                $('#unitLocationCode').val(data.unit_location || '');
                $('#govtIdNumber').val(data.govt_id || '');
                $('#idType').val(data.id_type || '');
                $('#neomId').val(data.neom_id || '');
                $('#dob').val(data.dob || '');
                $('#mobileNumber').val(data.mobile || '');
                $('#email').val(data.email || '');
                $('#nationality').val(data.nationality || '');
                $('#religion').val(data.religion || '');
                $('#occupancyStatus').val(data.occupancy_status || '');
                
                // Enable checkout field in update mode
                $('#actualCheckoutDatetime').prop('disabled', false);

                $modal.modal('show');
            },
            error: function (xhr) {
                showCustomMessageModal('Error', 'Failed to load check-in/check-out data', false);
            }
        });
    }
}

function showReservationInfo() {
    const $selected = $('#reservation option:selected');
    const selectedValue = $selected.val();
    
    console.log('showReservationInfo called, selected value:', selectedValue);
    
    if (selectedValue) {
        // Auto-populate all fields from reservation data
        const allocationType = $selected.attr('data-allocation-type') || '';
        const uua = $selected.attr('data-uua') || '';
        const allocationCode = $selected.attr('data-allocation-code') || '';
        const companyGroup = $selected.attr('data-company-group') || '';
        const company = $selected.attr('data-company') || '';
        const startDate = $selected.attr('data-start-date') || '';
        const endDate = $selected.attr('data-end-date') || '';
        const accomType = $selected.attr('data-accom-type') || '';
        const unit = $selected.attr('data-unit') || '';
        const unitLocation = $selected.attr('data-unit-location') || '';
        const govtId = $selected.attr('data-govt-id') || '';
        const idType = $selected.attr('data-id-type') || '';
        const neomId = $selected.attr('data-neom-id') || '';
        const dob = $selected.attr('data-dob') || '';
        const mobile = $selected.attr('data-mobile') || '';
        const email = $selected.attr('data-email') || '';
        const nationality = $selected.attr('data-nationality') || '';
        const religion = $selected.attr('data-religion') || '';
        const occupancyStatus = $selected.attr('data-occupancy-status') || '';
        
        console.log('Populating fields with data:', { 
            allocationType, uua, company, unit, 
            companyGroup, startDate, endDate, dob, nationality
        });
        
        // Populate all fields
        $('#allocationType').val(allocationType);
        $('#uuaNumber').val(uua);
        $('#allocationCode').val(allocationCode);
        $('#companyGroup').val(companyGroup);
        $('#company').val(company);
        $('#startDate').val(startDate);
        $('#endDate').val(endDate);
        $('#accomodationType').val(accomType);
        $('#unitNumber').val(unit);
        $('#unitLocationCode').val(unitLocation);
        $('#govtIdNumber').val(govtId);
        $('#idType').val(idType);
        $('#neomId').val(neomId);
        $('#dob').val(dob);
        $('#mobileNumber').val(mobile);
        $('#email').val(email);
        $('#nationality').val(nationality);
        $('#religion').val(religion);
        $('#occupancyStatus').val(occupancyStatus);
        
        console.log('Fields populated successfully');
    } else {
        console.log('No reservation selected, clearing fields');
        // Clear all fields if no reservation selected
        $('#allocationType, #uuaNumber, #allocationCode, #companyGroup, #company, #startDate, #endDate, #accomodationType, #unitNumber, #unitLocationCode, #govtIdNumber, #idType, #neomId, #dob, #mobileNumber, #email, #nationality, #religion, #occupancyStatus').val('');
    }
}

function calculateActualDuration() {
    const checkinDatetime = $('#actualCheckinDatetime').val();
    const checkoutDatetime = $('#actualCheckoutDatetime').val();
    
    if (checkinDatetime && checkoutDatetime) {
        const checkinDate = new Date(checkinDatetime);
        const checkoutDate = new Date(checkoutDatetime);
        
        if (checkoutDate > checkinDate) {
            const diffTime = Math.abs(checkoutDate - checkinDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            $('#actualStayDuration').val(diffDays);
        } else {
            $('#actualStayDuration').val('');
        }
    } else {
        $('#actualStayDuration').val('');
    }
}

// =======================================================
// CRUD Operations
// =======================================================

function handleCheckinSubmit(e) {
    e.preventDefault();

    const checkinId = $('#checkinId').val();
    const isUpdate = !!checkinId;
    const url = isUpdate 
        ? `/housing/checkin/update/${checkinId}/`
        : '/housing/checkin/create/';

    const formData = new FormData(document.getElementById('checkinForm'));
    
    // Debug: Log all form data
    console.log('Form data being submitted:');
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function (response) {
            if (response.success) {
                $('#checkinModal').modal('hide');
                showCustomMessageModal(
                    'Success',
                    isUpdate ? 'Check-in/check-out updated successfully' : 'Check-in/check-out created successfully',
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

function deleteSelectedCheckins() {
    const selectedIds = getSelectedCheckinIds();

    if (selectedIds.length === 0) {
        showCustomMessageModal('Warning', 'Please select at least one record to delete', false);
        return;
    }

    if (selectedIds.length > 1) {
        showCustomMessageModal('Warning', 'Please select only one record at a time', false);
        return;
    }

    $('#deleteConfirmationModal').modal('show');
}

function confirmDelete() {
    const selectedIds = getSelectedCheckinIds();

    $.ajax({
        url: '/housing/checkin/delete/',
        type: 'POST',
        data: {
            checkin_id: selectedIds[0],
            csrfmiddlewaretoken: getCSRFToken()
        },
        success: function (response) {
            if (response.success) {
                $('#deleteConfirmationModal').modal('hide');
                showCustomMessageModal('Success', 'Check-in/check-out deleted successfully', true);
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
    $('#checkinTableBody tr').each(function () {
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
    $('#checkinTableBody').find('input.select-entry').prop('checked', isChecked);
}

// =======================================================
// Event Listeners
// =======================================================

$(document).ready(function () {
    // Create button
    $('#addNewCheckinBtn').on('click', function () {
        openCheckinModal('create');
    });

    // Update button
    $('#updateCheckinBtn').on('click', function () {
        const selectedIds = getSelectedCheckinIds();

        if (selectedIds.length === 0) {
            showCustomMessageModal('Warning', 'Please select a record to update', false);
            return;
        }

        if (selectedIds.length > 1) {
            showCustomMessageModal('Warning', 'Please select only one record at a time', false);
            return;
        }

        openCheckinModal('update', selectedIds[0]);
    });

    // Double-click on row to edit
    $('#checkinTableBody').on('dblclick', 'tr', function () {
        const checkinId = $(this).find('input.select-entry').val();
        if (checkinId) {
            openCheckinModal('update', checkinId);
        }
    });

    // Form submit
    $('#checkinForm').on('submit', handleCheckinSubmit);

    // Delete buttons
    $('#deleteSelectedBtn').on('click', deleteSelectedCheckins);
    $('#confirmDeleteBtn').on('click', confirmDelete);

    // Search
    $('#search').on('keyup', handleSearch);

    // Select all
    $('#selectAll').on('change', handleSelectAll);

    // Reservation change - use direct DOM event to ensure it fires
    $(document).on('change', '#reservation', function() {
        console.log('Reservation dropdown changed');
        showReservationInfo();
    });
    
    // Calculate actual duration when checkout datetime changes
    $(document).on('change', '#actualCheckoutDatetime', calculateActualDuration);
    $(document).on('change', '#actualCheckinDatetime', calculateActualDuration);

    // Export button
    $('#exportBtn').on('click', function () {
        const searchQuery = $('#search').val();
        let exportUrl = '/housing/checkin/export/';
        if (searchQuery) {
            exportUrl += `?q=${encodeURIComponent(searchQuery)}`;
        }
        window.location.href = exportUrl;
    });
});
