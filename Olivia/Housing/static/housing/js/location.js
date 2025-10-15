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

// ===== Reset modal when opening Add mode =====
    const addButtons = document.querySelectorAll('[data-bs-target="#unitModal"]');
    addButtons.forEach(button => {
        button.addEventListener('click', function () {
            const form = document.getElementById('unitForm');
            if (form) {
                form.reset(); // reset all inputs
                document.getElementById('unit_location').value = ''; // clear location field
                document.getElementById('unitModalLabel').innerText = 'Add New Room';
                document.getElementById('unitSubmitBtn').innerHTML = '<i class="bi bi-save me-1"></i> Save';
            }
        });
    });
});
