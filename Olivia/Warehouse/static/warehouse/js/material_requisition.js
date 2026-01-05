/**
 * Material Requisition Management
 * Complete CRUD operations with multi-item support
 */

// =======================================================
// I. Global State & Configuration
// =======================================================

let currentPage = 1;
const itemsPerPage = 15;
let totalItems = 0;
let allRequisitions = [];
let filteredRequisitions = [];
let selectedRequisitionId = null;
let tempItems = [];  // For multiple items before saving
let allProducts = [];  // Cache for products

// =======================================================
// II. Initialization
// =======================================================

$(document).ready(function() {
    loadRequisitions();
    loadProducts();
    bindEventListeners();
});

function bindEventListeners() {
    // Search
    $('#searchRequisition').on('input', debounce(handleSearch, 300));
    
    // Status Filter
    $('#statusFilter').on('change', handleSearch);
    
    // Buttons
    $('#addNewRequisitionBtn').on('click', handleAddNew);
    $('#updateRequisitionBtn').on('click', handleUpdate);
    $('#deleteSelectedBtn').on('click', handleDelete);
    $('#exportBtn').on('click', handleExport);
    
    // Modal form
    $('#requisitionForm').on('submit', handleSaveRequisition);
    $('#addItemBtn').on('click', addItemToList);
    
    // Pagination
    $('#prevPage').on('click', () => changePage(currentPage - 1));
    $('#nextPage').on('click', () => changePage(currentPage + 1));
}

// =======================================================
// III. Data Loading & Display
// =======================================================

function loadRequisitions() {
    $.ajax({
        url: '/warehouse/api/requisition/list/',
        type: 'GET',
        success: function(response) {
            allRequisitions = response.data;
            filteredRequisitions = allRequisitions;
            totalItems = filteredRequisitions.length;
            currentPage = 1;
            displayRequisitions();
        },
        error: function(xhr, status, error) {
            console.error('Error loading requisitions:', error);
            showMessage('Error', 'Failed to load material requisitions', false);
        }
    });
}

function loadProducts() {
    $.ajax({
        url: '/warehouse/api/products/list/',
        type: 'GET',
        success: function(response) {
            allProducts = response.data;
            populateProductDropdown();
        },
        error: function(xhr, status, error) {
            console.error('Error loading products:', error);
        }
    });
}

function populateProductDropdown() {
    const select = $('#productSelect');
    select.empty();
    select.append('<option value="">Select Product</option>');
    
    allProducts.forEach(product => {
        select.append(`<option value="${product.id}">${product.code} - ${product.name}</option>`);
    });
}

function displayRequisitions() {
    const tbody = $('#requisitionTableBody');
    tbody.empty();
    
    if (filteredRequisitions.length === 0) {
        tbody.append('<tr><td colspan="6" class="text-center text-muted">No requisition records found</td></tr>');
        updatePagination();
        return;
    }
    
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, filteredRequisitions.length);
    const pageData = filteredRequisitions.slice(start, end);
    
    pageData.forEach(req => {
        const statusBadge = getStatusBadge(req.status);
        const row = `
            <tr data-id="${req.id}">
                <td>${req.date}</td>
                <td>${req.department}</td>
                <td>${req.requested_by}</td>
                <td><span class="badge bg-info">${req.items_count} items</span></td>
                <td>${statusBadge}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary btn-sm view-btn" data-id="${req.id}" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-warning btn-sm edit-btn" data-id="${req.id}" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm delete-btn" data-id="${req.id}" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
    
    // Bind row action buttons
    $('.view-btn').on('click', function() {
        viewRequisition($(this).data('id'));
    });
    
    $('.edit-btn').on('click', function() {
        editRequisition($(this).data('id'));
    });
    
    $('.delete-btn').on('click', function() {
        deleteRequisition($(this).data('id'));
    });
    
    updatePagination();
}

function getStatusBadge(status) {
    const badges = {
        'PENDING': '<span class="badge bg-warning text-dark">Pending</span>',
        'APPROVED': '<span class="badge bg-success">Approved</span>',
        'ISSUED': '<span class="badge bg-primary">Issued</span>',
        'REJECTED': '<span class="badge bg-danger">Rejected</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Unknown</span>';
}

// =======================================================
// IV. CRUD Operations
// =======================================================

function handleAddNew() {
    selectedRequisitionId = null;
    tempItems = [];
    $('#requisitionForm')[0].reset();
    $('#requisitionModalLabel').text('Create Material Requisition');
    $('#itemsListCard').show();
    $('#addItemBtnContainer').show();
    renderItemsList();
    bootstrap.Modal.getOrCreateInstance($('#requisitionModal')[0]).show();
}

function handleSaveRequisition(e) {
    e.preventDefault();
    
    if (tempItems.length === 0) {
        showMessage('Error', 'Please add at least one item', false);
        return;
    }
    
    const formData = {
        items: tempItems
    };
    
    const url = selectedRequisitionId 
        ? `/warehouse/api/requisition/update/${selectedRequisitionId}/`
        : '/warehouse/api/requisition/create/';
    
    const method = selectedRequisitionId ? 'PUT' : 'POST';
    
    $.ajax({
        url: url,
        type: method,
        headers: { 'X-CSRFToken': getCSRFToken() },
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(response) {
            showMessage('Success', response.message, true);
            bootstrap.Modal.getInstance($('#requisitionModal')[0]).hide();
            loadRequisitions();
        },
        error: function(xhr, status, error) {
            const errorMsg = xhr.responseJSON?.error || 'Operation failed';
            showMessage('Error', errorMsg, false);
        }
    });
}

function viewRequisition(id) {
    $.ajax({
        url: `/warehouse/api/requisition/detail/${id}/`,
        type: 'GET',
        success: function(data) {
            selectedRequisitionId = id;
            
            // Load items
            tempItems = data.items.map(item => ({
                product_id: item.product_id,
                product_code: item.product_code,
                product_name: item.product_name,
                requested_quantity: item.requested_quantity,
                issued_quantity: item.issued_quantity,
                remarks: item.remarks
            }));
            
            renderItemsList();
            
            // Hide edit controls
            $('#itemsListCard .card-body').find('.btn-danger').hide();
            $('#addItemBtnContainer').hide();
            $('button[type="submit"]').hide();
            
            $('#requisitionModalLabel').text('View Material Requisition');
            bootstrap.Modal.getOrCreateInstance($('#requisitionModal')[0]).show();
        },
        error: function(xhr, status, error) {
            showMessage('Error', 'Failed to load requisition details', false);
        }
    });
}

function editRequisition(id) {
    $.ajax({
        url: `/warehouse/api/requisition/detail/${id}/`,
        type: 'GET',
        success: function(data) {
            selectedRequisitionId = id;
            
            // Load items
            tempItems = data.items.map(item => ({
                product_id: item.product_id,
                product_code: item.product_code,
                product_name: item.product_name,
                requested_quantity: item.requested_quantity,
                issued_quantity: item.issued_quantity,
                remarks: item.remarks
            }));
            
            renderItemsList();
            
            $('#itemsListCard').show();
            $('#addItemBtnContainer').show();
            $('button[type="submit"]').show();
            
            $('#requisitionModalLabel').text('Update Material Requisition');
            bootstrap.Modal.getOrCreateInstance($('#requisitionModal')[0]).show();
        },
        error: function(xhr, status, error) {
            showMessage('Error', 'Failed to load requisition details', false);
        }
    });
}

function handleUpdate() {
    const selectedRows = $('#requisitionTableBody tr.table-active');
    
    if (selectedRows.length === 0) {
        showMessage('Error', 'Please select a requisition to update', false);
        return;
    }
    
    if (selectedRows.length > 1) {
        showMessage('Error', 'Please select only one requisition to update', false);
        return;
    }
    
    const id = selectedRows.first().data('id');
    editRequisition(id);
}

function deleteRequisition(id) {
    if (!confirm('Are you sure you want to delete this requisition?')) {
        return;
    }
    
    $.ajax({
        url: '/warehouse/api/requisition/delete/',
        type: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        contentType: 'application/json',
        data: JSON.stringify({ ids: [id] }),
        success: function(response) {
            showMessage('Success', response.message, true);
            loadRequisitions();
        },
        error: function(xhr, status, error) {
            const errorMsg = xhr.responseJSON?.error || 'Delete failed';
            showMessage('Error', errorMsg, false);
        }
    });
}

function handleDelete() {
    const selectedRows = $('#requisitionTableBody tr.table-active');
    
    if (selectedRows.length === 0) {
        showMessage('Error', 'Please select requisition(s) to delete', false);
        return;
    }
    
    const ids = selectedRows.map(function() {
        return $(this).data('id');
    }).get();
    
    if (!confirm(`Are you sure you want to delete ${ids.length} requisition(s)?`)) {
        return;
    }
    
    $.ajax({
        url: '/warehouse/api/requisition/delete/',
        type: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        contentType: 'application/json',
        data: JSON.stringify({ ids: ids }),
        success: function(response) {
            showMessage('Success', response.message, true);
            loadRequisitions();
        },
        error: function(xhr, status, error) {
            const errorMsg = xhr.responseJSON?.error || 'Delete failed';
            showMessage('Error', errorMsg, false);
        }
    });
}

// =======================================================
// V. Multi-Item Management
// =======================================================

function addItemToList() {
    const productId = $('#productSelect').val();
    const requestedQty = $('#requestedQuantity').val();
    const issuedQty = $('#issuedQuantity').val() || 0;
    const itemRemarks = $('#itemRemarks').val();
    
    if (!productId || !requestedQty) {
        showMessage('Error', 'Please select product and enter requested quantity', false);
        return;
    }
    
    const product = allProducts.find(p => p.id == productId);
    if (!product) {
        showMessage('Error', 'Invalid product selected', false);
        return;
    }
    
    tempItems.push({
        product_id: productId,
        product_code: product.code,
        product_name: product.name,
        requested_quantity: requestedQty,
        issued_quantity: issuedQty,
        remarks: itemRemarks
    });
    
    // Clear fields
    $('#productSelect').val('');
    $('#requestedQuantity').val('');
    $('#issuedQuantity').val('');
    $('#itemRemarks').val('');
    
    renderItemsList();
}

function renderItemsList() {
    const container = $('#itemsList');
    container.empty();
    
    if (tempItems.length === 0) {
        container.append('<p class="text-muted text-center">No items added yet</p>');
        return;
    }
    
    tempItems.forEach((item, index) => {
        const itemHtml = `
            <div class="d-flex justify-content-between align-items-center border-bottom pb-2 mb-2">
                <div>
                    <strong>${item.product_code}</strong> - ${item.product_name}<br>
                    <small class="text-muted">Requested: ${item.requested_quantity} | Issued: ${item.issued_quantity}</small>
                    ${item.remarks ? `<br><small class="text-info">${item.remarks}</small>` : ''}
                </div>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeItem(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.append(itemHtml);
    });
}

function removeItem(index) {
    tempItems.splice(index, 1);
    renderItemsList();
}

// =======================================================
// VI. Search & Filter
// =======================================================

function handleSearch() {
    const searchTerm = $('#searchRequisition').val().toLowerCase();
    const statusFilter = $('#statusFilter').val();
    
    filteredRequisitions = allRequisitions.filter(req => {
        const matchesSearch = !searchTerm || 
            req.department.toLowerCase().includes(searchTerm) ||
            req.requested_by.toLowerCase().includes(searchTerm);
        
        const matchesStatus = !statusFilter || req.status === statusFilter;
        
        return matchesSearch && matchesStatus;
    });
    
    totalItems = filteredRequisitions.length;
    currentPage = 1;
    displayRequisitions();
}

// =======================================================
// VII. Pagination
// =======================================================

function changePage(page) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    displayRequisitions();
}

function updatePagination() {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    $('#currentPage').text(currentPage);
    $('#totalPages').text(totalPages);
    
    $('#prevPage').prop('disabled', currentPage === 1);
    $('#nextPage').prop('disabled', currentPage === totalPages || totalPages === 0);
    
    const start = (currentPage - 1) * itemsPerPage + 1;
    const end = Math.min(currentPage * itemsPerPage, totalItems);
    $('#pageInfo').text(totalItems > 0 ? `Showing ${start}-${end} of ${totalItems}` : 'No records');
}

// =======================================================
// VIII. Export
// =======================================================

function handleExport() {
    window.location.href = '/warehouse/api/requisition/export/';
}

// =======================================================
// IX. Utility Functions
// =======================================================

function getCSRFToken() {
    return $('[name=csrfmiddlewaretoken]').val() || document.cookie.match(/csrftoken=([^;]+)/)?.[1];
}

function showMessage(title, message, isSuccess) {
    alert(`${title}: ${message}`);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Table row selection
$(document).on('click', '#requisitionTableBody tr', function(e) {
    if (!$(e.target).closest('button').length) {
        $(this).toggleClass('table-active');
    }
});
