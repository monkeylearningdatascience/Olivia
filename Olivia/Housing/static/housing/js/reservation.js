/* reservation.js - Reservation CRUD operations */

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
    const $modalTitle = $modal.find('.modal-title');
    const $modalBody = $modal.find('.modal-body');
    const $modalHeader = $modal.find('.modal-header');
    
    // Remove previous color classes
    $modalHeader.removeClass('bg-success bg-danger');
    
    // Set title and body
    $modalTitle.text(title);
    $modalBody.html(bodyHtml);
    
    // Set header color based on success/failure
    if (isSuccess) {
        $modalHeader.addClass('bg-success text-white');
        $modalTitle.addClass('text-white');
    } else {
        $modalHeader.addClass('bg-danger text-white');
        $modalTitle.addClass('text-white');
    }
    
    // Show the modal
    const modalInstance = bootstrap.Modal.getOrCreateInstance($modal[0]);
    modalInstance.show();
}

function getSelectedReservationIds() {
    return $('#reservationTableBody').find('input.select-entry:checked').map(function () {
        return $(this).val();
    }).get();
}

// =======================================================
// Modal Management
// =======================================================

function openReservationModal(mode = 'create', reservationId = null) {
    const $modal = $('#reservationModal');
    const $form = $('#reservationForm');
    const $title = $('#reservationModalLabel');
    const $saveBtn = $('#saveReservationBtn');

    $form[0].reset();
    $('#reservationId').val('');
    $('#userInfo').hide();

    if (mode === 'create') {
        $title.text('Add New Reservation');
        $saveBtn.text('Save');
        $modal.modal('show');
    } else if (mode === 'update' && reservationId) {
        $title.text('Update Reservation');
        $saveBtn.text('Update');

        $.ajax({
            url: `/housing/reservation/update/${reservationId}/`,
            type: 'GET',
            success: function (data) {
                $('#reservationId').val(data.id);
                $('#assignment').val(data.assignment).trigger('change');
                
                // Populate assignment fields
                $('#allocationType').val(data.allocation_type || '');
                $('#uuaNumber').val(data.uua_number || '');
                $('#companyGroup').val(data.company_group_name || '');
                $('#companyGroupId').val(data.company_group || '');
                $('#company').val(data.company_name || '');
                $('#companyId').val(data.company || '');
                $('#startDate').val(data.start_date || '');
                $('#endDate').val(data.end_date || '');
                $('#accomodationType').val(data.accomodation_type || '');
                $('#unitNumber').val(data.unit || '');
                $('#unitLocationCode').val(data.unit_location_code || '');
                
                // Populate housing user fields
                $('#housingUser').val(data.housing_user);
                $('#govtId').val(data.govt_id_number || '');
                $('#idType').val(data.id_type || '');
                $('#neomId').val(data.neom_id || '');
                $('#dob').val(data.dob || '');
                $('#mobileNumber').val(data.mobile_number || '');
                $('#email').val(data.email || '');
                $('#nationality').val(data.nationality || '');
                $('#religion').val(data.religion || '');
                
                // Populate reservation fields
                $('#intendedCheckinDate').val(data.intended_checkin_date);
                $('#intendedCheckoutDate').val(data.intended_checkout_date);
                $('#intendedStayDuration').val(data.intended_stay_duration || '');
                $('#occupancyStatus').val(data.occupancy_status);
                $('#remarks').val(data.remarks || '');

                $modal.modal('show');
            },
            error: function (xhr) {
                showCustomMessageModal('Error', 'Failed to load reservation data', false);
            }
        });
    }
}

function showUserInfo() {
    const $selected = $('#housingUser option:selected');
    if ($selected.val()) {
        // Auto-populate user fields
        $('#govtId').val($selected.data('govid') || '');
        $('#idType').val($selected.data('idtype') || '');
        $('#neomId').val($selected.data('neomid') || '');
        $('#dob').val($selected.data('dob') || '');
        $('#mobileNumber').val($selected.data('mobile') || '');
        $('#email').val($selected.data('email') || '');
        $('#nationality').val($selected.data('nationality') || '');
        $('#religion').val($selected.data('religion') || '');
    } else {
        // Clear user fields
        $('#govtId, #idType, #neomId, #dob, #mobileNumber, #email, #nationality, #religion').val('');
    }
}

function showAssignmentInfo() {
    const $selected = $('#assignment option:selected');
    if ($selected.val()) {
        // Auto-populate assignment fields
        $('#allocationType').val($selected.data('allocation-type') || '');
        $('#uuaNumber').val($selected.data('uua') || '');
        $('#companyGroup').val($selected.data('group') || '');
        $('#companyGroupId').val($selected.data('group-id') || '');
        $('#company').val($selected.data('company') || '');
        $('#companyId').val($selected.data('company-id') || '');
        $('#startDate').val($selected.data('start-date') || '');
        $('#endDate').val($selected.data('end-date') || '');
        $('#accomodationType').val($selected.data('accom-type') || '');
        $('#unitLocationCode').val($selected.data('location-code') || '');
        
        // Set unit number dropdown to the selected unit
        const unitId = $selected.data('unit-id');
        if (unitId) {
            $('#unitNumber').val(unitId);
        }
    } else {
        // Clear assignment fields
        $('#allocationType, #uuaNumber, #companyGroup, #companyGroupId, #company, #companyId').val('');
        $('#startDate, #endDate, #accomodationType, #unitLocationCode').val('');
        $('#unitNumber').val('');
    }
}

function calculateStayDuration() {
    const checkinDate = $('#intendedCheckinDate').val();
    const checkoutDate = $('#intendedCheckoutDate').val();
    
    if (checkinDate && checkoutDate) {
        const checkin = new Date(checkinDate);
        const checkout = new Date(checkoutDate);
        
        if (checkout > checkin) {
            const diffTime = Math.abs(checkout - checkin);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            $('#intendedStayDuration').val(diffDays);
        } else {
            $('#intendedStayDuration').val('');
        }
    } else {
        $('#intendedStayDuration').val('');
    }
}

// =======================================================
// CRUD Operations
// =======================================================

function handleReservationSubmit(e) {
    e.preventDefault();

    const reservationId = $('#reservationId').val();
    const isUpdate = !!reservationId;
    const url = isUpdate 
        ? `/housing/reservation/update/${reservationId}/`
        : '/housing/reservation/create/';

    const formData = new FormData(document.getElementById('reservationForm'));

    $.ajax({
        url: url,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: { 'X-CSRFToken': getCSRFToken() },
        success: function (response) {
            if (response.success) {
                $('#reservationModal').modal('hide');
                showCustomMessageModal(
                    'Success',
                    isUpdate ? 'Reservation updated successfully' : 'Reservation created successfully',
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

function deleteSelectedReservations() {
    const selectedIds = getSelectedReservationIds();

    if (selectedIds.length === 0) {
        showCustomMessageModal('Warning', 'Please select at least one reservation to delete', false);
        return;
    }

    if (selectedIds.length > 1) {
        showCustomMessageModal('Warning', 'Please select only one reservation at a time', false);
        return;
    }

    $('#deleteConfirmationModal').modal('show');
}

function confirmDelete() {
    const selectedIds = getSelectedReservationIds();

    $.ajax({
        url: '/housing/reservation/delete/',
        type: 'POST',
        data: {
            reservation_id: selectedIds[0],
            csrfmiddlewaretoken: getCSRFToken()
        },
        success: function (response) {
            if (response.success) {
                $('#deleteConfirmationModal').modal('hide');
                showCustomMessageModal('Success', 'Reservation deleted successfully', true);
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
    $('#reservationTableBody tr').each(function () {
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
    $('#reservationTableBody').find('input.select-entry').prop('checked', isChecked);
}

// =======================================================
// Event Listeners
// =======================================================

$(document).ready(function () {
    // Create button
    $('#addNewReservationBtn').on('click', function () {
        openReservationModal('create');
    });

    // Update button
    $('#updateReservationBtn').on('click', function () {
        const selectedIds = getSelectedReservationIds();

        if (selectedIds.length === 0) {
            showCustomMessageModal('Warning', 'Please select a reservation to update', false);
            return;
        }

        if (selectedIds.length > 1) {
            showCustomMessageModal('Warning', 'Please select only one reservation at a time', false);
            return;
        }

        openReservationModal('update', selectedIds[0]);
    });

    // Double-click on row to edit
    $('#reservationTableBody').on('dblclick', 'tr', function () {
        const reservationId = $(this).find('input.select-entry').val();
        if (reservationId) {
            openReservationModal('update', reservationId);
        }
    });

    // Form submit
    $('#reservationForm').on('submit', handleReservationSubmit);

    // Delete buttons
    $('#deleteSelectedBtn').on('click', deleteSelectedReservations);
    $('#confirmDeleteBtn').on('click', confirmDelete);

    // Search
    $('#search').on('keyup', handleSearch);

    // Select all
    $('#selectAll').on('change', handleSelectAll);

    // Housing user change
    $('#housingUser').on('change', showUserInfo);

    // Assignment change
    $('#assignment').on('change', showAssignmentInfo);

    // Date changes for calculating duration
    $('#intendedCheckinDate, #intendedCheckoutDate').on('change', calculateStayDuration);

    // Export button
    $('#exportBtn').on('click', function () {
        const searchQuery = $('#search').val();
        let exportUrl = '/housing/reservation/export/';
        if (searchQuery) {
            exportUrl += `?q=${encodeURIComponent(searchQuery)}`;
        }
        window.location.href = exportUrl;
    });
});
