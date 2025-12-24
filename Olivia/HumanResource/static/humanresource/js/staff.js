document.addEventListener('DOMContentLoaded', function () {
  const addNewBtn = document.getElementById('addNewStaffBtn');
  const updateBtn = document.getElementById('updateStaffBtn');
  const deleteBtn = document.getElementById('deleteSelectedBtn');
  const exportBtn = document.getElementById('exportBtn');
  const selectAll = document.getElementById('selectAll');
  const tableBody = document.getElementById('staffTableBody');
  const staffForm = document.getElementById('staffForm');
  const staffModalEl = document.getElementById('staffModal');
  const staffModalHeader = document.getElementById('staffModalHeader');
  const deleteConfirmHeader = document.getElementById('deleteConfirmModalHeader');
  // Use getOrCreateInstance instead of new bootstrap.Modal
  const getStaffModal = () => staffModalEl ? bootstrap.Modal.getOrCreateInstance(staffModalEl) : null;

  const setStaffHeader = (mode = 'create') => {
    if (!staffModalHeader) return;
    staffModalHeader.classList.remove('bg-dark', 'bg-danger', 'bg-primary');
    staffModalHeader.classList.add('modal-header', 'border-0');
    staffModalHeader.classList.add(mode === 'update' ? 'bg-primary' : 'bg-primary');
  };

  const setDeleteHeader = () => {
    if (!deleteConfirmHeader) return;
    deleteConfirmHeader.classList.remove('bg-dark', 'bg-primary', 'bg-success');
    deleteConfirmHeader.classList.add('modal-header', 'border-0', 'bg-danger');
  };

  let selectedIds = [];

  const getCsrf = () => document.querySelector('[name=csrfmiddlewaretoken]').value;

  function updateSelection() {
    selectedIds = Array.from(document.querySelectorAll('.select-entry:checked')).map(cb => cb.value);
  }

  if (tableBody) {
    tableBody.addEventListener('change', function (e) {
      if (e.target.classList.contains('select-entry')) updateSelection();
    });
  }

  if (selectAll) {
    selectAll.addEventListener('change', function () {
      document.querySelectorAll('.select-entry').forEach(cb => cb.checked = selectAll.checked);
      updateSelection();
    });
  }

  if (addNewBtn && staffModalEl) {
    addNewBtn.addEventListener('click', function () {
      // reset form for create
      staffForm.reset();
      document.getElementById('employee_id').value = '';
      document.getElementById('staffModalLabel').innerText = 'Add Staff';
      setStaffHeader('create');
      // hide photo preview
      const preview = document.getElementById('photoPreview');
      if (preview) { preview.src = ''; preview.classList.add('d-none'); }
      getStaffModal().show();
    });
  }

  if (updateBtn) {
    updateBtn.addEventListener('click', async function (e) {
      updateSelection();
      if (selectedIds.length !== 1) {
        // show selection modal
        const sel = document.getElementById('viewSelectionModal');
        if (sel) bootstrap.Modal.getOrCreateInstance(sel).show();
        return;
      }
      const id = selectedIds[0];
      try {
        const url = `/humanresource/staff/update/${id}/?_=${Date.now()}`;
        const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' } });
        if (!res.ok) {
          const text = await res.text().catch(() => '');
          console.error('Update fetch failed', { url, status: res.status, statusText: res.statusText, body: text?.slice?.(0, 200) });
          throw new Error(`HTTP ${res.status} ${res.statusText}`);
        }
        const contentType = res.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) {
          const text = await res.text();
          console.error('Non-JSON response for update endpoint', { url, text: text?.slice?.(0, 200) });
          throw new Error('Non-JSON response (possibly redirected to login)');
        }
        const data = await res.json();
        // populate form safely
        const setValue = (elemId, value) => {
          const el = document.getElementById(elemId);
          if (!el) {
            console.warn('Missing form element:', elemId);
            return;
          }
          // Skip file inputs - they can't be programmatically set for security reasons
          if (el.type === 'file') {
            console.log('Skipping file input:', elemId);
            return;
          }
          el.value = value ?? '';
        };

        setValue('employee_id', data.id);
        setValue('id_staffid', data.staffid);
        setValue('id_full_name', data.full_name);
        setValue('id_position', data.position);
        setValue('id_department', data.department);
        setValue('id_manager', data.manager);
        setValue('id_nationality', data.nationality);
        setValue('id_email', data.email);
        setValue('id_iqama_number', data.iqama_number);
        setValue('id_passport_number', data.passport_number);
        setValue('id_gender', data.gender);
        setValue('id_location', data.location);
        setValue('id_start_date', data.start_date);
        // show existing photo preview if available
        const preview = document.getElementById('photoPreview');
        if (preview) {
          if (data.photo_url) {
            preview.src = data.photo_url;
            preview.classList.remove('d-none');
          } else {
            preview.src = '';
            preview.classList.add('d-none');
          }
        }
        setValue('id_employment_status', data.employment_status || 'active');
        document.getElementById('staffModalLabel').innerText = 'Update Staff';
        setStaffHeader('update');
        const modal = getStaffModal();
        if (modal) modal.show();
      } catch (err) {
        console.error('Update load error:', err);
        alert(`Could not load staff record for update.\n${err?.message || ''}`);
      }
    });
  }

  if (staffForm) {
    staffForm.addEventListener('submit', function (e) {
      e.preventDefault();
      // Clear previous errors
      const errorsContainer = document.getElementById('formErrorsContainer');
      const errorsList = document.getElementById('formErrorsList');
      if (errorsContainer) {
        errorsContainer.classList.add('d-none');
        errorsList.innerHTML = '';
      }
      
      const formData = new FormData(staffForm);
      fetch(staffForm.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        }
      })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          const modal = getStaffModal();
          if (modal) modal.hide();
          window.location.reload();
        } else {
          // Handle field-level errors
          if (data.errors) {
            const errorsList = document.getElementById('formErrorsList');
            if (errorsList) {
              errorsList.innerHTML = '';
              for (const [field, messages] of Object.entries(data.errors)) {
                if (Array.isArray(messages)) {
                  messages.forEach(msg => {
                    const li = document.createElement('li');
                    li.textContent = `${field}: ${msg}`;
                    errorsList.appendChild(li);
                  });
                }
              }
              const errorsContainer = document.getElementById('formErrorsContainer');
              if (errorsContainer) {
                errorsContainer.classList.remove('d-none');
              }
            }
          } else {
            alert('Error saving staff');
          }
        }
      }).catch(err => {
        console.error(err);
        alert('Network error');
      });
    });
  }

  // Photo input preview (client-side)
  const photoInput = document.getElementById('id_photo');
  if (photoInput) {
    photoInput.addEventListener('change', function (e) {
      const file = e.target.files && e.target.files[0];
      const preview = document.getElementById('photoPreview');
      if (file && preview) {
        const reader = new FileReader();
        reader.onload = function (ev) {
          preview.src = ev.target.result;
          preview.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
        // clear any pre-existing photo_url hidden value
        const hiddenUrl = document.getElementById('id_photo_url');
        if (hiddenUrl) hiddenUrl.value = '';
      }
    });
  }

  if (deleteBtn) {
    deleteBtn.addEventListener('click', function () {
      updateSelection();
      if (!selectedIds.length) {
        const sel = document.getElementById('viewSelectionModal');
        if (sel) bootstrap.Modal.getOrCreateInstance(sel).show();
        return;
      }
      const confirmModalEl = document.getElementById('deleteConfirmModal');
      const confirmModal = confirmModalEl ? bootstrap.Modal.getOrCreateInstance(confirmModalEl) : null;
      setDeleteHeader();
      if (confirmModal) confirmModal.show();

      const confirmBtn = document.getElementById('confirmDeleteBtn');
      if (confirmBtn) {
        confirmBtn.onclick = function () {
          console.log('NEW DELETE CODE RUNNING - Selected IDs:', selectedIds);
          
          if (!selectedIds || selectedIds.length === 0) {
            alert('No items selected for deletion');
            return;
          }
          
          // Create URLSearchParams for the data
          const params = new URLSearchParams();
          selectedIds.forEach(id => {
            params.append('selected_ids', id);
          });
          params.append('csrfmiddlewaretoken', getCsrf());
          params.append('action', 'delete');
          
          console.log('NEW CODE: Sending data:', params.toString());
          
          fetch('/humanresource/staff/', {
            method: 'POST',
            body: params,
            headers: {
              'X-Requested-With': 'XMLHttpRequest',
              'Content-Type': 'application/x-www-form-urlencoded',
            }
          })
          .then(r => {
            console.log('Response status:', r.status);
            if (!r.ok) {
              throw new Error(`HTTP ${r.status}: ${r.statusText}`);
            }
            return r.json();
          })
          .then(data => {
            console.log('Response data:', data);
            if (data.success) {
              window.location.reload();
            } else {
              alert('Delete failed: ' + (data.message || 'Unknown error'));
            }
          }).catch(err => {
            console.error('Error:', err);
            alert('Error: ' + err.message);
          });
        };
      }
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener('click', function () {
      window.location.href = '/humanresource/export/staff/';
    });
  }

  // Search/Filter Functionality
  const searchInput = document.getElementById('search');
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      const searchTerm = this.value.toLowerCase();
      const rows = document.querySelectorAll('#staffTableBody tr');
      let visibleCount = 0;

      rows.forEach(row => {
        // Get all text content from the row
        const textContent = row.textContent.toLowerCase();
        
        // Show row if search term is empty or matches any part of the row
        if (searchTerm === '' || textContent.includes(searchTerm)) {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });

      // Show "no results" message if all rows are hidden
      const noResultsRow = document.querySelector('#staffTableBody tr[data-no-results]');
      if (visibleCount === 0) {
        // If there's no existing "no results" row, we could add one dynamically
        // For now, just hide the table content
      }
    });
  }

  // Import Staff Form Handler
  const importStaffForm = document.getElementById('importStaffForm');
  const importStaffLoadingIndicator = document.getElementById('importStaffLoadingIndicator');
  const importStaffSubmitBtn = document.getElementById('importStaffSubmitBtn');
  const importStaffModalEl = document.getElementById('importStaffModal');
  const getImportStaffModal = () => importStaffModalEl ? bootstrap.Modal.getOrCreateInstance(importStaffModalEl) : null;

  if (importStaffForm) {
    importStaffForm.addEventListener('submit', function (e) {
      e.preventDefault();
      
      if (importStaffLoadingIndicator) {
        importStaffLoadingIndicator.classList.remove('d-none');
      }
      if (importStaffSubmitBtn) {
        importStaffSubmitBtn.disabled = true;
      }
      
      const formData = new FormData(importStaffForm);
      
      fetch(importStaffForm.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        }
      })
      .then(r => r.json())
      .then(data => {
        if (importStaffLoadingIndicator) {
          importStaffLoadingIndicator.classList.add('d-none');
        }
        if (importStaffSubmitBtn) {
          importStaffSubmitBtn.disabled = false;
        }
        
        if (data.success) {
          alert(`Import successful!\nImported: ${data.imported}\nUpdated: ${data.updated}\n${data.message}`);
          const modal = getImportStaffModal();
          if (modal) modal.hide();
          importStaffForm.reset();
          window.location.reload();
        } else {
          alert(`Import failed: ${data.error}`);
        }
      })
      .catch(err => {
        console.error(err);
        if (importStaffLoadingIndicator) {
          importStaffLoadingIndicator.classList.add('d-none');
        }
        if (importStaffSubmitBtn) {
          importStaffSubmitBtn.disabled = false;
        }
        alert('Network error during import');
      });
    });
  }

  // Manager Form Handler
  const managerForm = document.getElementById('managerForm');
  const managerModalEl = document.getElementById('managerModal');
  const getManagerModal = () => managerModalEl ? bootstrap.Modal.getOrCreateInstance(managerModalEl) : null;

  if (managerForm) {
    managerForm.addEventListener('submit', function (e) {
      e.preventDefault();
      
      const errorsContainer = document.getElementById('managerFormErrorsContainer');
      const errorsList = document.getElementById('managerFormErrorsList');
      if (errorsContainer) {
        errorsContainer.classList.add('d-none');
        errorsList.innerHTML = '';
      }
      
      const formData = new FormData(managerForm);
      const managerId = document.getElementById('manager_id').value;
      const url = managerId ? `/humanresource/manager/update/${managerId}/` : '/humanresource/manager/create/';
      
      fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        }
      })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          const modal = getManagerModal();
          if (modal) modal.hide();
          alert(data.message);
          window.location.reload();
        } else {
          alert('Error: ' + (data.message || 'Failed to save manager'));
        }
      }).catch(err => {
        console.error(err);
        alert('Network error');
      });
    });
  }

});
