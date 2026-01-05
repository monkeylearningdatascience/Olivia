/* receiving.js
   Complete warehouse receiving management
   - CRUD operations via AJAX
   - Search and filter
   - Import/Export functionality
   - Pagination
*/

// =======================================================
// I. Global Variables & Pagination
// =======================================================

let allReceivingData = []; // Store all data
let currentPage = 1;
const itemsPerPage = 15;
let tempItems = []; // Store items to be saved
let selectAllPages = false; // Track if all pages are selected

// =======================================================
// II. Global Utilities & CSRF Token
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

function formatDate(dateString) {
    if (!dateString || dateString === 'null' || dateString === 'undefined' || dateString === '-') {
        return '-';
    }
    
    try {
        // Parse the date (handles YYYY-MM-DD, MM/DD/YYYY, etc.)
        const date = new Date(dateString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return dateString; // Return original if invalid
        }
        
        // Format as DD/MM/YYYY
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        return `${day}/${month}/${year}`;
    } catch (e) {
        return dateString; // Return original on error
    }
}

function showMessage(title, message, isSuccess = true) {
    const $modal = $('#messageModal');
    const headerClass = isSuccess ? 'bg-success text-white' : 'bg-danger text-white';
    
    $modal.find('.modal-header').removeClass('bg-success bg-danger text-white').addClass(headerClass);
    $modal.find('.modal-title').text(title);
    $modal.find('#messageModalBody').html(message);
    
    const modalInstance = bootstrap.Modal.getOrCreateInstance($modal[0]);
    modalInstance.show();
}

// =======================================================
// II. Load Data & Populate Dropdowns
// =======================================================

function loadReceivingData(callback) {
    // Load all data by fetching all pages
    let allData = [];
    let currentApiPage = 1;
    const pageSize = 500; // Load 500 records per API call
    
    // Check if table has actual data rows (not "No records found" message)
    const tableHasData = $('#receivingTableBody tr').length > 0 && 
                         $('#receivingTableBody tr').first().find('td').length > 1;
    
    function loadPage() {
        $.ajax({
            url: '/warehouse/api/receiving/list/',
            type: 'GET',
            dataType: 'json',
            timeout: 60000, // 60 second timeout per page
            data: {
                page: currentApiPage,
                page_size: pageSize
            },
            success: function(response) {
                console.log(`Loaded page ${currentApiPage}: ${response.data.length} records`);
                
                // Add data from this page
                allData = allData.concat(response.data);
                
                // Check if there are more pages
                if (currentApiPage < response.total_pages) {
                    currentApiPage++;
                    // Only show progress message if table doesn't have data rows
                    if (!tableHasData) {
                        const progress = Math.round((allData.length / response.total) * 100);
                        $('#receivingTableBody').html(`
                            <tr>
                                <td colspan="27" class="text-center">
                                    <i class="fas fa-spinner fa-spin me-2"></i>
                                    Loading data... ${allData.length} of ${response.total} records (${progress}%)
                                </td>
                            </tr>
                        `);
                    }
                    loadPage(); // Load next page
                } else {
                    // All pages loaded
                    console.log('All data loaded:', allData.length, 'records');
                    allReceivingData = allData;
                    currentPage = 1;
                    renderReceivingTable();
                    if (callback) callback(true, allData);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error loading receiving data:', error, 'Status:', status);
                console.error('Response:', xhr.responseText);
                
                let errorMessage = 'Error loading data. Please refresh the page.';
                if (status === 'timeout') {
                    errorMessage = 'Loading data timed out. Please refresh the page or contact support.';
                }
                
                $('#receivingTableBody').html(`
                    <tr>
                        <td colspan="27" class="text-center text-danger">
                            ${errorMessage}
                        </td>
                    </tr>
                `);
                if (callback) callback(false, null);
            }
        });
    }
    
    // Start loading from first page
    loadPage();
}

function renderReceivingTable() {
    const $tbody = $('#receivingTableBody');
    $tbody.empty();
    
    console.log('Rendering table with', allReceivingData.length, 'records'); // Debug log
    
    if (!allReceivingData || allReceivingData.length === 0) {
        $tbody.html('<tr><td colspan="27" class="text-center text-muted">No receiving records found</td></tr>');
        updatePaginationInfo(0, 0, 0);
        return;
    }
    
    // Calculate pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, allReceivingData.length);
    const pageData = allReceivingData.slice(startIndex, endIndex);
    
    console.log('Rendering page', currentPage, '- showing records', startIndex, 'to', endIndex); // Debug log
    
    // Render rows for current page
    pageData.forEach((receiving, index) => {
        try {
            const row = createReceivingRow(receiving);
            $tbody.append(row);
        } catch (err) {
            console.error('Error rendering row', index, ':', err, receiving);
        }
    });
    
    // Update pagination info
    updatePaginationInfo(startIndex + 1, endIndex, allReceivingData.length);
    updatePaginationButtons();
}

function createReceivingRow(receiving) {
    const val = v => (v && v !== 'null' && v !== 'undefined') ? v : '-';
    const purchaseTypeLabel = receiving.purchase_type === 'LOCAL' ? 'Local Purchase' : 'Head Quarters';
    
    // Calculate totals if items exist
    let totalAmount = 0;
    if (receiving.items && receiving.items.length > 0) {
        receiving.items.forEach(item => {
            const subtotal = item.quantity * item.unit_price;
            const vatAmount = subtotal * (item.vat_percentage / 100);
            totalAmount += subtotal + vatAmount;
        });
    }
    
    // For now, showing first item or empty cells
    const firstItem = receiving.items && receiving.items.length > 0 ? receiving.items[0] : {};
    
    return `
        <tr data-id="${receiving.id}">
            <td><input type="checkbox" class="select-entry form-check-input" value="${receiving.id}"></td>
            <td>${formatDate(receiving.date)}</td>
            <td>${val(receiving.pr_number)}</td>
            <td>${val(receiving.po_number)}</td>
            <td>${formatDate(receiving.po_date)}</td>
            <td>${val(receiving.grn_number)}</td>
            <td>${val(receiving.invoice_number)}</td>
            <td>${val(firstItem.category_name)}</td>
            <td>${val(firstItem.item_code)}</td>
            <td>${val(firstItem.item_description)}</td>
            <td style="display: none;">${val(firstItem.model_number)}</td>
            <td style="display: none;">${val(firstItem.serial_number)}</td>
            <td style="display: none;">${val(firstItem.country_of_origin)}</td>
            <td>${val(firstItem.uom)}</td>
            <td style="display: none;">${val(firstItem.quantity)}</td>
            <td style="display: none;">${val(firstItem.unit_price)}</td>
            <td style="display: none;">${val(firstItem.subtotal)}</td>
            <td style="display: none;">${val(firstItem.vat_percentage)}</td>
            <td style="display: none;">${val(firstItem.vat_amount)}</td>
            <td style="display: none;">${totalAmount.toFixed(2)}</td>
            <td>${val(receiving.supplier_name)}</td>
            <td>${purchaseTypeLabel}</td>
            <td>${val(receiving.department)}</td>
            <td style="display: none;">${formatDate(firstItem.production_date)}</td>
            <td style="display: none;">${formatDate(firstItem.expiry_date)}</td>
            <td>${val(firstItem.product_life)}</td>
            <td>${val(firstItem.product_status)}</td>
        </tr>
    `;
}

// Supplier is now a text field, not a dropdown
// function loadSuppliers() - removed as supplier is text input

// =======================================================
// III. Pagination Functions
// =======================================================

function updatePaginationInfo(start, end, total) {
    $('#paginationInfo').text(`Showing ${start} to ${end} of ${total} entries`);
}

function updatePaginationButtons() {
    const totalPages = Math.ceil(allReceivingData.length / itemsPerPage);
    
    // Update Previous button
    if (currentPage <= 1) {
        $('#prevPageBtn').addClass('disabled');
    } else {
        $('#prevPageBtn').removeClass('disabled');
    }
    
    // Update Next button
    if (currentPage >= totalPages) {
        $('#nextPageBtn').addClass('disabled');
    } else {
        $('#nextPageBtn').removeClass('disabled');
    }
}

function goToPage(page) {
    const totalPages = Math.ceil(allReceivingData.length / itemsPerPage);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    selectAllPages = false; // Reset when changing pages
    $('#selectAll').prop('checked', false);
    renderReceivingTable();
}

// =======================================================
// III-B. Multiple Items Management
// =======================================================

function addItemToList() {
    // Validate required item fields
    const uom = $('#uom').val().trim();
    const quantity = parseFloat($('#quantity').val());
    const unitPrice = parseFloat($('#unitPrice').val());
    
    if (!uom || !quantity || !unitPrice) {
        showMessage('Validation Error', 'Please fill in UOM, Quantity, and Unit Price for the item.', false);
        return;
    }
    
    // Collect item data
    const item = {
        category: $('#category').val(),
        item_code: $('#itemCode').val(),
        item_description: $('#itemDescription').val(),
        model_number: $('#modelNumber').val(),
        serial_number: $('#serialNumber').val(),
        country_of_origin: $('#countryOfOrigin').val(),
        uom: uom,
        quantity: quantity,
        unit_price: unitPrice,
        vat_percentage: parseFloat($('#vat').val()) || 0,
        production_date: $('#productionDate').val(),
        expiry_date: $('#expiryDate').val()
    };
    
    // Calculate total
    item.total = (item.quantity * item.unit_price * (1 + item.vat_percentage / 100)).toFixed(2);
    
    // Add to temp items array
    tempItems.push(item);
    
    // Clear item fields
    clearItemFields();
    
    // Render items list
    renderItemsList();
    
    showMessage('Success', 'Item added to the list. Click "Save All Items" to save.', true);
}

function clearItemFields() {
    $('#category').val('');
    $('#itemCode').val('');
    $('#itemDescription').val('');
    $('#modelNumber').val('');
    $('#serialNumber').val('');
    $('#countryOfOrigin').val('');
    $('#uom').val('');
    $('#quantity').val('');
    $('#unitPrice').val('');
    $('#vat').val('0');
    $('#productionDate').val('');
    $('#expiryDate').val('');
}

function renderItemsList() {
    const $tbody = $('#itemsListBody');
    $tbody.empty();
    
    if (tempItems.length === 0) {
        $tbody.html('<tr><td colspan="12" class="text-center text-muted">No items added yet</td></tr>');
        return;
    }
    
    tempItems.forEach((item, index) => {
        const row = `
            <tr>
                <td>${index + 1}</td>
                <td>${item.category || '-'}</td>
                <td>${item.item_code || '-'}</td>
                <td>${item.item_description || '-'}</td>
                <td>${item.model_number || '-'}</td>
                <td>${item.serial_number || '-'}</td>
                <td>${item.uom}</td>
                <td>${item.quantity}</td>
                <td>${item.unit_price}</td>
                <td>${item.vat_percentage}%</td>
                <td>${item.total}</td>
                <td>
                    <button type="button" class="btn btn-danger btn-sm" onclick="removeItem(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        $tbody.append(row);
    });
}

function removeItem(index) {
    tempItems.splice(index, 1);
    renderItemsList();
}

function saveAllItems() {
    // Validate header fields
    const date = $('#receiveDate').val();
    const grnNumber = $('#grnNumber').val();
    const supplier = $('#supplier').val();
    const purchaseType = $('#purchaseType').val();
    
    if (!date || !grnNumber || !supplier || !purchaseType) {
        showMessage('Validation Error', 'Please fill in all required receiving information fields (Date, GRN No, Supplier, Purchase Type).', false);
        return;
    }
    
    if (tempItems.length === 0) {
        showMessage('Validation Error', 'Please add at least one item before saving.', false);
        return;
    }
    
    // Prepare data
    const receivingData = {
        date: date,
        pr_number: $('#prNumber').val(),
        po_number: $('#poNumber').val(),
        po_date: $('#poDate').val(),
        grn_number: grnNumber,
        invoice_number: $('#invoiceNumber').val(),
        supplier: supplier,
        purchase_type: purchaseType,
        department: $('#department').val(),
        status: $('#status').val(),
        remarks: $('#remarks').val(),
        items: tempItems
    };
    
    // Send to server
    $.ajax({
        url: '/warehouse/api/receiving/create/',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(receivingData),
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        success: function(response) {
            showMessage('Success', 'All items have been saved successfully!', true);
            $('#receivingModal').modal('hide');
            loadReceivingData();
            tempItems = [];
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || 'Failed to save items. Please try again.';
            showMessage('Error', errorMsg, false);
        }
    });
}

function updateSingleItem() {
    // Validate required fields
    const date = $('#receiveDate').val();
    const grnNumber = $('#grnNumber').val();
    const supplier = $('#supplier').val();
    const purchaseType = $('#purchaseType').val();
    const uom = $('#uom').val();
    const quantity = $('#quantity').val();
    const unitPrice = $('#unitPrice').val();
    
    if (!date || !grnNumber || !supplier || !purchaseType) {
        showMessage('Validation Error', 'Please fill in all required receiving information fields.', false);
        return;
    }
    
    if (!uom || !quantity || !unitPrice) {
        showMessage('Validation Error', 'Please fill in UOM, Quantity, and Unit Price.', false);
        return;
    }
    
    const receivingId = $('#receivingId').val();
    
    // Prepare update data
    const updateData = {
        date: date,
        pr_number: $('#prNumber').val(),
        po_number: $('#poNumber').val(),
        po_date: $('#poDate').val(),
        grn_number: grnNumber,
        invoice_number: $('#invoiceNumber').val(),
        supplier: supplier,
        purchase_type: purchaseType,
        department: $('#department').val(),
        status: $('#status').val(),
        remarks: $('#remarks').val(),
        // Item details
        category: $('#category').val(),
        item_code: $('#itemCode').val(),
        item_description: $('#itemDescription').val(),
        model_number: $('#modelNumber').val(),
        serial_number: $('#serialNumber').val(),
        country_of_origin: $('#countryOfOrigin').val(),
        uom: uom,
        quantity: parseFloat(quantity),
        unit_price: parseFloat(unitPrice),
        vat_percentage: parseFloat($('#vat').val()) || 0,
        production_date: $('#productionDate').val() || null,
        expiry_date: $('#expiryDate').val() || null
    };
    
    $('#updateSingleItemBtn').prop('disabled', true).html('<i class=\"fas fa-spinner fa-spin me-1\"></i> Updating...');
    
    // Send update request
    $.ajax({
        url: `/warehouse/api/receiving/update/${receivingId}/`,
        type: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(updateData),
        headers: {
            'X-CSRFToken': getCSRFToken()
        },
        success: function(response) {
            showMessage('Success', 'Receiving updated successfully!', true);
            $('#receivingModal').modal('hide');
            loadReceivingData();
        },
        error: function(xhr) {
            const errorMsg = xhr.responseJSON?.error || 'Failed to update. Please try again.';
            showMessage('Error', errorMsg, false);
        },
        complete: function() {
            $('#updateSingleItemBtn').prop('disabled', false).html('<i class=\"fas fa-save me-1\"></i> Update');
        }
    });
}

// =======================================================
// IV. Form Submission (Create/Update)
// =======================================================

function handleReceivingFormSubmission(e) {
    e.preventDefault();
    
    const mode = $('#receivingForm').data('mode') || 'create';
    const receivingId = $('#receivingId').val();
    
    const formData = {
        date: $('#receiveDate').val(),
        pr_number: $('#prNumber').val(),
        po_number: $('#poNumber').val(),
        po_date: $('#poDate').val() || null,
        grn_number: $('#grnNumber').val(),
        invoice_number: $('#invoiceNumber').val(),
        supplier: $('#supplier').val(),
        purchase_type: $('#purchaseType').val(),
        department: $('#department').val(),
        status: $('#status').val(),
        remarks: $('#remarks').val(),
        // Item details
        category: $('#category').val(),
        item_code: $('#itemCode').val(),
        item_description: $('#itemDescription').val(),
        model_number: $('#modelNumber').val(),
        serial_number: $('#serialNumber').val(),
        country_of_origin: $('#countryOfOrigin').val(),
        uom: $('#uom').val(),
        quantity: $('#quantity').val() ? parseFloat($('#quantity').val()) : null,
        unit_price: $('#unitPrice').val() ? parseFloat($('#unitPrice').val()) : null,
        vat_percentage: $('#vat').val() ? parseFloat($('#vat').val()) : 0,
        production_date: $('#productionDate').val() || null,
        expiry_date: $('#expiryDate').val() || null
    };
    
    const url = mode === 'update' ? `/warehouse/api/receiving/update/${receivingId}/` : '/warehouse/api/receiving/create/';
    const method = mode === 'update' ? 'PUT' : 'POST';
    
    $('#saveReceivingBtn').prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i> Saving...');
    
    $.ajax({
        url: url,
        type: method,
        headers: { 'X-CSRFToken': getCSRFToken() },
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            showMessage('Success', mode === 'update' ? 'Receiving updated successfully!' : 'Receiving created successfully!', true);
            $('#receivingForm')[0].reset();
            bootstrap.Modal.getOrCreateInstance($('#receivingModal')[0]).hide();
            loadReceivingData();
        },
        error: function(xhr, status, error) {
            const errorMsg = xhr.responseJSON?.error || 'An error occurred while saving.';
            showMessage('Error', errorMsg, false);
        },
        complete: function() {
            $('#saveReceivingBtn').prop('disabled', false).html('<i class="fas fa-save me-1"></i> Save');
        }
    });
}

// =======================================================
// V. Update & Delete Operations
// =======================================================

function handleUpdateReceiving() {
    const $selectedRows = $('#receivingTableBody tr').filter(function() {
        return $(this).find('input.select-entry:checked').length > 0;
    });
    
    if ($selectedRows.length === 0) {
        showMessage('Selection Required', 'Please select a receiving record to update.', false);
        return;
    }
    
    if ($selectedRows.length > 1) {
        showMessage('Multiple Selection', 'Please select only one record to update.', false);
        return;
    }
    
    const receivingId = $selectedRows.first().data('id');
    
    // Load receiving data
    $.ajax({
        url: `/warehouse/api/receiving/detail/${receivingId}/`,
        type: 'GET',
        success: function(data) {
            populateReceivingForm(data);
            $('#receivingForm').data('mode', 'update').data('receiving-id', receivingId);
            $('#receivingModalLabel').text('Update Receiving');
            
            // Hide create mode elements, show update mode elements
            $('#addItemBtnContainer').hide();
            $('#itemsListCard').hide();
            $('#saveAllItemsBtn').hide();
            $('#updateSingleItemBtn').show();
            
            bootstrap.Modal.getOrCreateInstance($('#receivingModal')[0]).show();
        },
        error: function(xhr, status, error) {
            showMessage('Error', 'Failed to load receiving data.', false);
        }
    });
}

function populateReceivingForm(data) {
    $('#receivingId').val(data.id);
    $('#receiveDate').val(data.date);
    $('#prNumber').val(data.pr_number);
    $('#poNumber').val(data.po_number);
    $('#poDate').val(data.po_date);
    $('#grnNumber').val(data.grn_number);
    $('#invoiceNumber').val(data.invoice_number);
    $('#supplier').val(data.supplier);
    $('#purchaseType').val(data.purchase_type);
    $('#department').val(data.department);
    $('#status').val(data.status);
    $('#remarks').val(data.remarks);
    
    // Populate item fields if available
    if (data.item) {
        $('#category').val(data.item.category);
        $('#itemCode').val(data.item.item_code);
        $('#itemDescription').val(data.item.item_description);
        $('#modelNumber').val(data.item.model_number);
        $('#serialNumber').val(data.item.serial_number);
        $('#countryOfOrigin').val(data.item.country_of_origin);
        $('#uom').val(data.item.uom);
        $('#quantity').val(data.item.quantity);
        $('#unitPrice').val(data.item.unit_price);
        $('#vat').val(data.item.vat_percentage);
        $('#productionDate').val(data.item.production_date);
        $('#expiryDate').val(data.item.expiry_date);
    }
}

function handleDeleteReceiving() {
    let selectedIds = [];
    
    // If select all pages is enabled, get all IDs
    if (selectAllPages) {
        selectedIds = allReceivingData.map(item => item.id);
    } else {
        // Otherwise, get only checked IDs on current page
        $('#receivingTableBody tr').each(function() {
            const $checkbox = $(this).find('input.select-entry:checked');
            if ($checkbox.length > 0) {
                selectedIds.push($(this).data('id'));
            }
        });
    }
    
    if (selectedIds.length === 0) {
        showMessage('Selection Required', 'Please select at least one receiving record to delete.', false);
        return;
    }
    
    // Update confirmation message
    const confirmMessage = selectAllPages 
        ? `Are you sure you want to delete ALL ${selectedIds.length} receiving records? This action cannot be undone.`
        : `Are you sure you want to delete ${selectedIds.length} selected receiving record(s)?`;
    
    $('#deleteConfirmModal .modal-body p').text(confirmMessage);
    bootstrap.Modal.getOrCreateInstance($('#deleteConfirmModal')[0]).show();
    
    $('#confirmDeleteBtn').off('click').on('click', function() {
        const $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i> Deleting...');
        
        $.ajax({
            url: '/warehouse/api/receiving/delete/',
            type: 'DELETE',
            headers: { 'X-CSRFToken': getCSRFToken() },
            contentType: 'application/json',
            data: JSON.stringify({ ids: selectedIds }),
            success: function(response) {
                // Close modal first
                bootstrap.Modal.getOrCreateInstance($('#deleteConfirmModal')[0]).hide();
                
                // Show loading in table
                $('#receivingTableBody').html('<tr><td colspan="27" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Reloading data...</td></tr>');
                
                // Reset select all flag
                selectAllPages = false;
                $('#selectAll').prop('checked', false);
                
                // Reload data
                loadReceivingData();
                
                // Show success message after short delay
                setTimeout(function() {
                    showMessage('Success', 'Receiving record(s) deleted successfully!', true);
                }, 500);
            },
            error: function(xhr, status, error) {
                showMessage('Error', 'Failed to delete receiving record(s).', false);
            },
            complete: function() {
                $btn.prop('disabled', false).html('<i class="fas fa-check me-1"></i> Yes, Delete');
            }
        });
    });
}

// =======================================================
// VI. Import & Export
// =======================================================

function handleImport(e) {
    e.preventDefault();
    
    const fileInput = $('#importFile')[0];
    if (!fileInput.files || fileInput.files.length === 0) {
        showMessage('No File Selected', 'Please select a file to import.', false);
        return;
    }
    
    const file = fileInput.files[0];
    const fileName = file.name;
    
    // Disable submit button and show loading
    const $submitBtn = $('#importReceivingForm button[type="submit"]');
    $submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-1"></i> Importing...');
    
    // Show progress message
    $('#importReceivingModal .modal-body').prepend(`
        <div class="alert alert-info" id="importProgress">
            <i class="fas fa-spinner fa-spin me-2"></i>
            Importing data from ${fileName}... Please wait.
        </div>
    `);
    
    const formData = new FormData($('#importReceivingForm')[0]);
    
    $.ajax({
        url: '/warehouse/api/receiving/import/',
        type: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            console.log('Import response:', response);
            console.log('Imported count:', response.count);
            
            let message = response.message || `Successfully imported ${response.count} receiving record(s)!`;
            let isSuccess = true;
            
            // If there are errors, show them
            if (response.errors) {
                message += '<br><br><strong>Errors:</strong><br>' + response.errors.replace(/\n/g, '<br>');
                isSuccess = response.count > 0; // Partial success if some records imported
            }
            
            // Close modal immediately
            $('#importReceivingForm')[0].reset();
            $('#importProgress').remove();
            bootstrap.Modal.getOrCreateInstance($('#importReceivingModal')[0]).hide();
            
            // Show loading in table
            $('#receivingTableBody').html(`
                <tr>
                    <td colspan="27" class="text-center">
                        <i class="fas fa-spinner fa-spin me-2"></i>
                        Loading ${response.count} records... This may take a moment.
                    </td>
                </tr>
            `);
            
            // Show success message
            showMessage('Import Successful', message + '<br><br>Loading data into table...', isSuccess);
            
            // Load data in background with timeout handling
            const loadStartTime = Date.now();
            loadReceivingData(function(success, data) {
                const loadTime = ((Date.now() - loadStartTime) / 1000).toFixed(1);
                console.log('Data reload complete. Success:', success, 'Records:', data ? data.length : 0, 'Time:', loadTime + 's');
                
                if (success && data && data.length > 0) {
                    // Data loaded successfully
                    console.log(`Successfully loaded ${data.length} records in ${loadTime} seconds`);
                } else if (!success) {
                    // Timeout or error occurred
                    showMessage('Data Loading Issue', 
                        'Import was successful but loading the data is taking longer than expected. ' +
                        'Please refresh the page to see your imported records.', 
                        false);
                }
            });
        },
        error: function(xhr, status, error) {
            console.error('Import error:', error);
            console.error('Response:', xhr.responseText);
            
            let errorMsg = 'Failed to import data.';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMsg = xhr.responseJSON.error;
            } else if (xhr.responseText) {
                try {
                    const errData = JSON.parse(xhr.responseText);
                    errorMsg = errData.error || errorMsg;
                } catch (e) {
                    errorMsg += ' (Server error)';
                }
            }
            
            $('#importProgress').remove();
            showMessage('Import Error', errorMsg, false);
        },
        complete: function() {
            $submitBtn.prop('disabled', false).html('<i class="fas fa-upload me-1"></i> Import');
        }
    });
}

function handleExport() {
    window.location.href = '/warehouse/api/receiving/export/';
}

// =======================================================
// VII. Search Functionality
// =======================================================

function handleSearch() {
    const searchTerm = $('#searchReceiving').val().toLowerCase();
    
    if (!searchTerm) {
        // If search is empty, show all data with pagination
        currentPage = 1;
        renderReceivingTable();
        return;
    }
    
    // Filter data based on search term
    const filteredData = allReceivingData.filter(receiving => {
        const searchableText = [
            receiving.date,
            receiving.pr_number,
            receiving.po_number,
            receiving.grn_number,
            receiving.invoice_number,
            receiving.supplier_name,
            receiving.department,
            receiving.status,
            receiving.purchase_type
        ].join(' ').toLowerCase();
        
        return searchableText.includes(searchTerm);
    });
    
    // Temporarily replace allReceivingData for rendering
    const originalData = allReceivingData;
    allReceivingData = filteredData;
    currentPage = 1;
    renderReceivingTable();
    allReceivingData = originalData;
}

// =======================================================
// VIII. Document Ready & Event Handlers
// =======================================================

$(document).ready(function() {
    // Load initial data
    loadReceivingData();
    
    // Add New Receiving
    $('#addNewReceivingBtn').on('click', function() {
        $('#receivingForm')[0].reset();
        $('#receivingForm').data('mode', 'create').removeData('receiving-id');
        $('#receivingId').val('');
        $('#receivingModalLabel').text('Add New Receiving');
        tempItems = []; // Clear temp items
        renderItemsList(); // Clear items list display
        
        // Show create mode elements
        $('#addItemBtnContainer').show();
        $('#itemsListCard').show();
        $('#saveAllItemsBtn').show();
        $('#updateSingleItemBtn').hide();
    });
    
    // Add Item button
    $('#addItemBtn').on('click', addItemToList);
    
    // Save All Items button
    $('#saveAllItemsBtn').on('click', saveAllItems);
    
    // Update Single Item button
    $('#updateSingleItemBtn').on('click', updateSingleItem);
    
    // Form submission - disable default form submit
    $('#receivingForm').on('submit', function(e) {
        e.preventDefault();
        // Form submission now handled by Save All Items button
    });
    
    // Update button
    $('#updateReceivingBtn').on('click', handleUpdateReceiving);
    
    // Delete button
    $('#deleteSelectedBtn').on('click', handleDeleteReceiving);
    
    // Import
    $('#importReceivingForm').on('submit', handleImport);
    
    // Export
    $('#exportBtn').on('click', handleExport);
    
    // Search
    $('#searchReceiving').on('keyup', handleSearch);
    
    // Pagination buttons
    $('#prevPageBtn').on('click', function(e) {
        e.preventDefault();
        goToPage(currentPage - 1);
    });
    
    $('#nextPageBtn').on('click', function(e) {
        e.preventDefault();
        goToPage(currentPage + 1);
    });
    
    // Select all functionality
    $('#selectAll').on('change', function() {
        const isChecked = $(this).prop('checked');
        const $checkbox = $(this);
        
        // If checking and there are more records than visible
        if (isChecked && allReceivingData.length > itemsPerPage) {
            // Show modal confirmation
            const message = `All ${allReceivingData.length} records will be selected for deletion. Do you want to continue?`;
            $('#selectAllMessage').text(message);
            bootstrap.Modal.getOrCreateInstance($('#selectAllConfirmModal')[0]).show();
            
            // Uncheck temporarily until confirmed
            $checkbox.prop('checked', false);
        } else {
            // For unchecking or small datasets, just apply directly
            selectAllPages = isChecked;
            $('.select-entry').prop('checked', isChecked);
        }
    });
    
    // Handle select all confirmation
    $('#confirmSelectAllBtn').on('click', function() {
        selectAllPages = true;
        $('#selectAll').prop('checked', true);
        $('.select-entry').prop('checked', true);
        bootstrap.Modal.getOrCreateInstance($('#selectAllConfirmModal')[0]).hide();
    });
    
    // Handle select all cancellation
    $('#cancelSelectAllBtn').on('click', function() {
        selectAllPages = false;
        $('#selectAll').prop('checked', false);
        $('.select-entry').prop('checked', false);
    });
});
