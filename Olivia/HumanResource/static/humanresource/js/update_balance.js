// Prevent double execution
if (typeof window.updateBalanceInit === 'undefined') {
    window.updateBalanceInit = true;

    // Get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Open modal and populate fields
    window.openUpdateModal = function(balanceId = '', amount = '', activity = '', projectName = '') {
        document.getElementById('balance_id').value = balanceId;
        document.getElementById('update_amount').value = amount;
        document.getElementById('update_activity').value = activity;
        document.getElementById('update_project_name').value = projectName;

        const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('updateBalanceModal'));
        modal.show();
    }

    // -----------------------------
    // Reset modal fields on close
    // -----------------------------
    const modalEl = document.getElementById('updateBalanceModal');
    modalEl.addEventListener('hidden.bs.modal', function () {
        document.getElementById('updateBalanceForm').reset();
        document.getElementById('update_amount').value = '';
    });

    // Fetch total for 'Submitted to HQ' filtered by project
    async function fetchSubmittedTotal(projectName) {
        if (!projectName) return 0.0;

        try {
            const response = await fetch(`/humanresource/get_submitted_total/?project_name=${projectName}`);
            if (!response.ok) throw new Error('Failed to fetch total');

            const data = await response.json();
            return parseFloat(data.total || 0).toFixed(2);
        } catch (err) {
            console.error(err);
            return 0.0;
        }
    }

    const updateBalanceForm = document.getElementById('updateBalanceForm');
    const updateModalSubmitBtn = document.getElementById('updateModalSubmitBtn');
    const activitySelect = document.getElementById('update_activity');
    const projectSelect = document.getElementById('update_project_name');
    const amountInput = document.getElementById('update_amount');

    // Update amount when activity or project changes
    async function updateAmountIfSubmitted() {
        const activity = activitySelect.value;
        const project = projectSelect.value;

        if (activity === 'submitted' && project) {
            const total = await fetchSubmittedTotal(project);
            amountInput.value = total;
        }
    }

    activitySelect.addEventListener('change', updateAmountIfSubmitted);
    projectSelect.addEventListener('change', updateAmountIfSubmitted);

    // Handle submit
    if (updateModalSubmitBtn && updateBalanceForm) {
        updateModalSubmitBtn.addEventListener('click', async function () {
            // Ensure amount is populated for 'Submitted to HQ'
            await updateAmountIfSubmitted();

            const formData = new FormData(updateBalanceForm);

            if (!formData.get('amount') || !formData.get('activity') || !formData.get('project_name')) {
                alert("Please fill all fields!");
                return;
            }

            fetch(updateBalanceForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modalEl = document.getElementById('updateBalanceModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    modal.hide();
                    location.reload();
                } else {
                    alert('Error: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => {
                console.error(err);
                alert('Submission failed');
            });
        });
    }
}
