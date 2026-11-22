document.addEventListener('DOMContentLoaded', () => {
    // Mobile Sidebar Toggle
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Modal Triggers
    const openModalBtns = document.querySelectorAll('[data-modal-target]');
    openModalBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = btn.getAttribute('data-modal-target');
            const modal = document.querySelector(modalId);
            if (modal) {
                modal.classList.add('active');
            }
        });
    });

    // Close Modal Triggers
    const closeModalBtns = document.querySelectorAll('[data-modal-close]');
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close Modal on clicking backdrop
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('active');
        }
    });

    // Auto-dismiss alerts after 4 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 4000);
    });

    // Mark All Present Shortcut in Attendance Page
    const markAllPresentBtn = document.getElementById('btnMarkAllPresent');
    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener('click', () => {
            const presentRadios = document.querySelectorAll('input[type="radio"][value="Present"]');
            presentRadios.forEach(radio => radio.checked = true);
        });
    }

    // Live Grade Calculator helper for Score Inputs
    const scoreInputs = document.querySelectorAll('.score-calc-input');
    scoreInputs.forEach(input => {
        const previewSpan = document.getElementById(input.getAttribute('data-preview-id'));
        if (previewSpan) {
            input.addEventListener('input', () => {
                const val = parseFloat(input.value);
                if (isNaN(val)) {
                    previewSpan.textContent = '-';
                    return;
                }
                if (val >= 90) previewSpan.textContent = 'A+ (4.0)';
                else if (val >= 80) previewSpan.textContent = 'A (3.7)';
                else if (val >= 70) previewSpan.textContent = 'B (3.0)';
                else if (val >= 60) previewSpan.textContent = 'C (2.0)';
                else if (val >= 50) previewSpan.textContent = 'D (1.0)';
                else previewSpan.textContent = 'F (0.0)';
            });
        }
    });
});

// Function to populate and open Edit Course Modal
function openEditCourseModal(id, code, name, dept, credits, semester, instructor, description) {
    const modal = document.getElementById('editCourseModal');
    if (!modal) return;

    const form = modal.querySelector('form');
    form.action = `/courses/${id}/update`;

    document.getElementById('edit_course_code').value = code || '';
    document.getElementById('edit_course_name').value = name || '';
    document.getElementById('edit_course_dept').value = dept || '';
    document.getElementById('edit_course_credits').value = credits || 3;
    document.getElementById('edit_course_semester').value = semester || '';
    document.getElementById('edit_course_instructor').value = instructor || '';
    document.getElementById('edit_course_description').value = description || '';

    modal.classList.add('active');
}

// Function to open Score Update Modal
function openUpdateScoreModal(enrollmentId, currentScore, currentStatus, studentName, courseCode, redirectTarget = 'enrollments', studentId = '') {
    const modal = document.getElementById('updateScoreModal');
    if (!modal) return;

    const form = modal.querySelector('form');
    form.action = `/enrollments/${enrollmentId}/update_score`;

    document.getElementById('score_modal_title').textContent = `Update Grade: ${studentName} (${courseCode})`;
    document.getElementById('score_input').value = currentScore !== 'None' && currentScore !== '' ? currentScore : '';
    document.getElementById('status_select').value = currentStatus || 'Enrolled';
    
    const redirInput = document.getElementById('score_redirect_target');
    if (redirInput) redirInput.value = redirectTarget;

    const studentIdInput = document.getElementById('score_student_id');
    if (studentIdInput) studentIdInput.value = studentId;

    // trigger preview update
    const evt = new Event('input');
    document.getElementById('score_input').dispatchEvent(evt);

    modal.classList.add('active');
}
