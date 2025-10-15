document.addEventListener("DOMContentLoaded", function () {
    // Modal References
    const unitModalElement = document.getElementById("unitModal");
    const unitModal = unitModalElement ? new bootstrap.Modal(unitModalElement) : null;
    const unitForm = document.getElementById("unitForm");
    const unitModalLabel = document.getElementById("unitModalLabel");

    // Import Modal References
    const importUnitModalElement = document.getElementById("importUnitModal");
    const importUnitModal = importUnitModalElement ? new bootstrap.Modal(importUnitModalElement) : null;
    const importUnitForm = document.getElementById("importUnitForm");
    const importSubmitBtn = document.getElementById("importSubmitBtn");
    const importLoadingIndicator = document.getElementById("importLoadingIndicator");

    // =========================================================================
    // Selection Error Modal References (ADAPTED TO REUSE viewSelectionModal HTML)
    // =========================================================================
    // Use the actual IDs from the provided modal HTML
    const selectionErrorModalElement = document.getElementById("viewSelectionModal");
    const selectionErrorModal = selectionErrorModalElement ? new bootstrap.Modal(selectionErrorModalElement) : null;

    // Get the dynamic elements we need to change content
    const selectionErrorModalLabel = document.getElementById("viewSelectionModalLabel");
    const selectionErrorModalBody = selectionErrorModalElement ? selectionErrorModalElement.querySelector(".modal-body") : null;
    const selectionErrorModalHeader = selectionErrorModalElement ? selectionErrorModalElement.querySelector(".modal-header") : null;
    const selectionErrorModalOkBtn = selectionErrorModalElement ? selectionErrorModalElement.querySelector(".modal-footer .btn") : null;
    // =========================================================================


    // Table/Selection References
    const selectAll = document.getElementById("selectAll");
    const tableBody = document.getElementById("unitsTableBody");

    // Action Button References
    const addNewUnitBtn = document.getElementById("addNewUnitBtn");
    const updateUnitBtn = document.getElementById("updateUnitBtn");
    const deleteBtn = document.getElementById("deleteSelectedBtn");
    const exportBtn = document.getElementById("exportBtn");
    const importBtn = document.getElementById("viewBtn");

    // Search References (NEW)
    const searchInput = document.getElementById("search");
    let searchTimeout = null;

    // Delete Modal elements
    const deleteConfirmModalElement = document.getElementById("deleteConfirmModal");
    const deleteConfirmModal = deleteConfirmModalElement ? new bootstrap.Modal(deleteConfirmModalElement) : null;
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");

    let selectedUnitIds = []; // Stores IDs for update or delete

    // Helper to get CSRF token
    const getCsrfToken = () => document.querySelector('[name=csrfmiddlewaretoken]').value;


    // =======================================================
    // HELPER FUNCTION: DYNAMIC SELECTION MODAL (REUSING PETTY CASH LOGIC/HTML)
    // =======================================================
    function showSelectionErrorModal(action, customBodyText = '') {
        if (!selectionErrorModal) {
            console.error("Error: Selection Modal (ID: viewSelectionModal) not found in the DOM.");
            return;
        }

        // Cleanup existing classes/styles
        if (selectionErrorModalHeader) {
            selectionErrorModalHeader.classList.remove('bg-light', 'bg-primary', 'bg-danger', 'bg-success');
        }
        if (selectionErrorModalOkBtn) {
            selectionErrorModalOkBtn.classList.remove('btn-outline-secondary', 'btn-primary', 'btn-danger', 'btn-success');
        }

        let titleText = 'Invalid Selection';
        let bodyText = customBodyText; // Default to custom text if provided
        let headerClass = 'bg-light';
        let btnClass = 'btn-outline-secondary';
        let iconClass = 'bi-exclamation-triangle-fill';

        if (action === 'update') {
            titleText = 'Update Room';
            bodyText = 'Please select exactly one room to update.';
            headerClass = 'bg-primary';
            btnClass = 'btn-primary';
            iconClass = 'bi-pencil';
        } else if (action === 'delete') {
            titleText = 'Delete Rooms';
            bodyText = 'Please select at least one room to delete.';
            headerClass = 'bg-danger';
            btnClass = 'btn-danger';
            iconClass = 'bi-trash';
        } else if (action === 'import-success') {
            titleText = 'Import Successful';
            // bodyText is already set by customBodyText
            headerClass = 'bg-success';
            btnClass = 'btn-success';
            iconClass = 'bi-check-circle-fill';
        } else if (action === 'import-error') {
            titleText = 'Import Failed';
            // bodyText is already set by customBodyText
            headerClass = 'bg-danger';
            btnClass = 'btn-danger';
            iconClass = 'bi-x-octagon-fill';
        }


        // Apply content and styles
        if (selectionErrorModalLabel) {
            // Replaces the content with the icon and title
            selectionErrorModalLabel.innerHTML = `<i class="bi ${iconClass} me-2"></i>${titleText}`;
        }
        if (selectionErrorModalBody) {
            selectionErrorModalBody.innerText = bodyText;
        }
        if (selectionErrorModalHeader) {
            selectionErrorModalHeader.classList.add(headerClass);
        }
        if (selectionErrorModalOkBtn) {
            selectionErrorModalOkBtn.classList.add(btnClass);
        }

        selectionErrorModal.show();
    }


    // =======================================================
    // I. TABLE RENDERING AND SEARCH LOGIC (NEW)
    // =======================================================

    // Function to render the HTML table rows from JSON data
    const renderUnitTable = (units) => {
        const tableBody = document.getElementById("unitsTableBody");
        if (!tableBody) return;

        let html = '';
        units.forEach(unit => {
            // NOTE: You must ensure the field names (unit.unit_number, unit.zone, etc.) 
            // match the fields returned by your Django view's .values() call.
            html += `
                                <tr>
                                    <td><input type="checkbox" class="select-entry" value="${unit.id}"></td>
                                    <td>${unit.unit_number || ''}</td>
                                    <td>${unit.bed_number || ''}</td>
                                    <td>${unit.unit_location || ''}</td>
                                    <td>${unit.zone || ''}</td>
                                    <td>${unit.accomodation_type || ''}</td>
                                    <td>${unit.wave || ''}</td>
                                    <td>${unit.area || ''}</td>
                                    <td>${unit.block || ''}</td>
                                    <td>${unit.building || ''}</td>
                                    <td>${unit.floor || ''}</td>
                                    <td>${unit.occupancy_status || ''}</td>
                                    <td>${unit.room_physical_status || ''}</td>
                                </tr>
                    `;
        });
        tableBody.innerHTML = html;
        updateButtonStates(); // Re-check selection states after redrawing
    };

    // Function to fetch and render units from the server
    const fetchAndRenderUnits = (searchTerm = '') => {
        // IMPORTANT: The URL must point to your units list view
        const url = `/housing/units/?search=${searchTerm}`;

        fetch(url, {
            method: 'GET',
            headers: {
                // This header tells Django it's an AJAX request
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
                // Data received from Django is filtered and ready to render
                renderUnitTable(data.units);
            })
            .catch(error => {
                console.error('Error fetching units:', error);
                // Optionally display an error message
            });
    };

    // Search Input Listener (Debounced)
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            // Clear the previous timeout
            clearTimeout(searchTimeout);

            // Set a new timeout (wait 300ms after the last keypress)
            searchTimeout = setTimeout(() => {
                const searchTerm = searchInput.value;
                // If there's a search term, run the AJAX search.
                // If the term is empty, we reload the whole page to get pagination back (simple approach).
                if (searchTerm.length > 0) {
                    fetchAndRenderUnits(searchTerm);
                } else {
                    window.location.reload(); // Simple way to clear search and restore pagination
                }
            }, 300); // 300 milliseconds debounce time
        });
    }

    // =======================================================
    // II. MODAL STATE MANAGEMENT (Initialization and Cleanup)
    // =======================================================

    // Reset unit modal state when it's closed (Create/Update Modal)
    if (unitModalElement) {
        unitModalElement.addEventListener('hidden.bs.modal', function () {
            unitForm.reset();

            // Reset to Create mode defaults
            unitModalLabel.innerHTML = '<i class="bi bi-building-add me-2"></i>Add New Room';

            // Remove hidden ID input if it exists (used for update)
            const hiddenId = document.getElementById('unit_id_hidden');
            if (hiddenId) {
                hiddenId.remove();
            }
        });
    }

    // =======================================================
    // III. BUTTON STATE AND CHECKBOX LISTENERS
    // =======================================================

    // Function to check how many units are selected and update selected IDs
    const updateButtonStates = () => {
        const checkedCount = document.querySelectorAll(".select-entry:checked").length;
        selectedUnitIds = Array.from(document.querySelectorAll(".select-entry:checked")).map(cb => cb.value);
    };

    // Attach listener to all checkboxes and the table body for delegation
    if (tableBody) {
        tableBody.addEventListener('change', (e) => {
            if (e.target.classList.contains('select-entry')) {
                updateButtonStates();
            }
        });
    }

    if (selectAll) {
        selectAll.addEventListener("change", function () {
            document.querySelectorAll(".select-entry").forEach(cb => cb.checked = selectAll.checked);
            updateButtonStates();
        });
    }

    // Initial check on load
    updateButtonStates();


    // =======================================================
    // IV. CREATE MODE SETUP
    // =======================================================

    if (addNewUnitBtn && unitModal) {
        addNewUnitBtn.addEventListener('click', () => {
            unitModal.show();
        });
    }


    // =======================================================
    // V. UPDATE MODE SETUP (FETCH & POPULATE)
    // =======================================================
    if (updateUnitBtn && unitModal) {
        updateUnitBtn.addEventListener('click', async (e) => {
            if (selectedUnitIds.length !== 1) {
                e.preventDefault();
                // --- Use dynamic helper for selection error ---
                showSelectionErrorModal('update');
                return;
            }

            const unitId = selectedUnitIds[0];
            console.log(`Attempting to fetch data for Unit ID: ${unitId}`);

            try {
                const response = await fetch(`/housing/units/update/${unitId}/`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                if (!response.ok) {
                    console.error("AJAX Fetch failed. Response status:", response.status, response.statusText);
                    throw new Error(`Failed to fetch unit data (Status: ${response.status}).`);
                }

                const unitData = await response.json();
                console.log("Unit data received successfully:", unitData);


                // 1. Change modal to Update mode
                unitModalLabel.innerHTML = '<i class="bi bi-pencil me-2"></i>Update Room';

                // 2. Change form action to the specific update URL
                unitForm.action = `/housing/units/update/${unitId}/`;

                // 3. Add a hidden input field for the ID
                let hiddenInput = document.getElementById('unit_id_hidden');
                if (!hiddenInput) {
                    hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'unit_id';
                    hiddenInput.id = 'unit_id_hidden';
                    unitForm.appendChild(hiddenInput);
                }
                hiddenInput.value = unitId;


                // 4. Populate form fields
                for (const key in unitData) {
                    const input = unitForm.querySelector(`[name="${key}"]`);
                    if (input) {
                        if (input.tagName === 'SELECT') {
                            const option = Array.from(input.options).find(opt => opt.value === unitData[key]);
                            if (option) {
                                input.value = unitData[key];
                            } else {
                                input.value = '';
                            }
                        } else {
                            input.value = unitData[key] || '';
                        }
                    }
                }

                // 5. Recalculate and set unit_location
                recalculateLocationForDisplay();

                // 6. Show the modal
                unitModal.show();

            } catch (error) {
                console.error("Critical Error during Unit Update Setup:", error);
                alert("Could not load unit data for update. See console for details.");
            }
        });
    }


    // =======================================================
    // VI. FORM SUBMISSION (Handles both Create and Update)
    // =======================================================
    if (unitForm) {
        unitForm.addEventListener("submit", function (e) {
            e.preventDefault();

            fetch(unitForm.action, {
                method: "POST",
                body: new FormData(unitForm),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrfToken()
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        if (unitModal) unitModal.hide();
                        unitForm.reset();
                        window.location.reload();
                    } else {
                        alert("Error: " + (data.error || "Could not save unit."));
                    }
                })
                .catch(err => {
                    console.error("AJAX Error:", err);
                    alert("A network error occurred. Check the console for details.");
                });
        });
    }

    // =======================================================
    // VII. IMPORT LOGIC (New Feature) - UPDATED FOR MODAL FEEDBACK
    // =======================================================

    // 1. Open Import Modal when Import button is clicked
    if (importBtn && importUnitModal) {
        importBtn.addEventListener('click', () => {
            if (importLoadingIndicator) importLoadingIndicator.classList.add('d-none');
            if (importSubmitBtn) importSubmitBtn.removeAttribute('disabled');
            importUnitForm.reset();
            importUnitModal.show();
        });
    }

    // 2. Handle Import Form Submission
    if (importUnitForm) {
        importUnitForm.addEventListener("submit", function (e) {
            e.preventDefault();

            // Show loading indicator and disable button
            if (importLoadingIndicator) importLoadingIndicator.classList.remove('d-none');
            if (importSubmitBtn) importSubmitBtn.setAttribute('disabled', 'true');

            fetch(importUnitForm.action, {
                method: "POST",
                body: new FormData(importUnitForm),
            })
                .then(res => res.json())
                .then(data => {
                    // Hide loading elements
                    if (importLoadingIndicator) importLoadingIndicator.classList.add('d-none');
                    if (importSubmitBtn) importSubmitBtn.removeAttribute('disabled');
                    
                    // Hide the file upload modal
                    if (importUnitModal) importUnitModal.hide();

                    if (data.success) {
                        // SUCCESS: Show the results in the modal
                        const message = `${data.count} records processed and imported successfully.`;
                        
                        // Show success message in the dynamic modal
                        showSelectionErrorModal('import-success', message); 

                        // Reload the page only after the user closes the modal
                        selectionErrorModalElement.addEventListener('hidden.bs.modal', function handler() {
                            window.location.reload();
                            selectionErrorModalElement.removeEventListener('hidden.bs.modal', handler);
                        }, { once: true });

                    } else {
                        // SERVER ERROR: Show the error in the modal
                        const errorMsg = "File could not be processed. Details: " + (data.error || "Unknown server error.");
                        showSelectionErrorModal('import-error', errorMsg);
                    }
                })
                .catch(err => {
                    // NETWORK ERROR: Show the network error in the modal
                    if (importLoadingIndicator) importLoadingIndicator.classList.add('d-none');
                    if (importSubmitBtn) importSubmitBtn.removeAttribute('disabled');
                    if (importUnitModal) importUnitModal.hide();

                    console.error("Import AJAX Error:", err);
                    const errorMsg = "A network error occurred during import. Check the console for details.";
                    showSelectionErrorModal('import-error', errorMsg);
                });
        });
    }

    // =======================================================
    // VIII. DELETE LOGIC 
    // =======================================================

    // Open Modal when "Delete Selected" is clicked
    if (deleteBtn && deleteConfirmModal) {
        deleteBtn.addEventListener("click", function (e) {
            // These lines are CRITICAL and correct to prevent double modals.
            e.preventDefault();
            e.stopPropagation();

            if (!selectedUnitIds.length) {
                // Case 1: Nothing selected (Show dynamic error modal)
                showSelectionErrorModal('delete'); // This shows "Please select at least one room to delete."
            } else {
                // Case 2: Items are selected (Show Confirmation Modal: delete_modal)
                deleteConfirmModal.show(); // This shows "Are you sure you want to delete..."
            }
        });
    }

    // Confirm Delete Logic (Attached to Modal's 'Delete' button)
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener("click", function () {
            if (!selectedUnitIds.length) return;

            deleteConfirmModal.hide();

            fetch("/housing/units/delete/", {
                method: "POST",
                body: JSON.stringify({ ids: selectedUnitIds }),
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert("Delete failed: " + (data.error || "Unknown error."));
                    }
                })
                .catch(err => {
                    console.error("Delete AJAX Error:", err);
                    alert("A network error occurred. Check the console for details.");
                });
        });
    }

    // =======================================================
    // IX. Export Button
    // =======================================================
    if (exportBtn) {
        exportBtn.addEventListener("click", () => window.location.href = "/housing/units/export/");
    }

    // =======================================================
    // X. Unit Location Calculation
    // =======================================================
    const recalculateLocationForDisplay = () => {
        const areaEl = document.getElementById('area');
        const blockEl = document.getElementById('block');
        const buildingEl = document.getElementById('building');
        const floorEl = document.getElementById('floor');
        const unitLocationEl = document.getElementById('unit_location');

        if (areaEl && blockEl && buildingEl && floorEl && unitLocationEl) {
            const parts = [areaEl.value, blockEl.value, buildingEl.value, floorEl.value].filter(Boolean);
            unitLocationEl.value = parts.join('-').trim();
        }
    };

    // Attach listeners only if the form exists
    if (unitForm) {
        unitForm.querySelectorAll('.unit-part').forEach(select => {
            select.addEventListener('change', recalculateLocationForDisplay);
        });
    }
});