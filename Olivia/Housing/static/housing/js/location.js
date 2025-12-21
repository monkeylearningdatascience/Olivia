// Prevent multiple executions
if (window.locationJsInitialized) {
    return;
}
window.locationJsInitialized = true;

// location.js
function updateUnitLocation() {
    const area = document.getElementById("area")?.value || "";
    const block = document.getElementById("block")?.value || "";
    const building = document.getElementById("building")?.value || "";
    const floor = document.getElementById("floor")?.value || "";

    const parts = [area, block, building, floor].filter(Boolean);
    document.getElementById("unit_location").value = parts.join(" - ");
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".unit-part").forEach(input => {
        input.addEventListener("change", updateUnitLocation);
    });

    // Reset modal form when opened in Add mode
    const unitModalElement = document.getElementById('unitModal');
    if (unitModalElement) {
        unitModalElement.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            // Only reset for Add mode (not Edit)
            if (button && !button.classList.contains('edit-btn')) {
                const form = document.getElementById('unitForm');
                if (form) {
                    form.reset();
                    document.getElementById('unit_location').value = '';
                    document.getElementById('unitModalLabel').innerText = 'Add New Room';
                    const submitBtn = document.getElementById('unitSubmitBtn');
                    if (submitBtn) {
                        submitBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save';
                    }
                }
            }
        });
    }
});
