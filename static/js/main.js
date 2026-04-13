// Main JavaScript for School Portal

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            
            // Animate hamburger lines
            const lines = hamburger.querySelectorAll('span');
            if (navMenu.classList.contains('active')) {
                lines[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                lines[1].style.opacity = '0';
                lines[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                lines[0].style.transform = 'none';
                lines[1].style.opacity = '1';
                lines[2].style.transform = 'none';
            }
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navMenu && navMenu.classList.contains('active') && 
            !navMenu.contains(e.target) && 
            !hamburger.contains(e.target)) {
            navMenu.classList.remove('active');
            const lines = hamburger.querySelectorAll('span');
            lines[0].style.transform = 'none';
            lines[1].style.opacity = '1';
            lines[2].style.transform = 'none';
        }
    });
    
    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            message.style.transition = 'all 0.5s ease';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
    
    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                    
                    // Remove error class on input
                    field.addEventListener('input', function() {
                        field.classList.remove('error');
                    });
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                // Show error message
                const firstError = form.querySelector('.error');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    });
    
    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const maxSize = 5 * 1024 * 1024; // 5MB
                if (file.size > maxSize) {
                    alert('File size exceeds 5MB. Please choose a smaller file.');
                    this.value = '';
                    return;
                }
                
                const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Only PDF, JPG, and PNG files are allowed.');
                    this.value = '';
                    return;
                }
                
                // Show file name
                const label = this.nextElementSibling;
                if (label && label.tagName === 'LABEL') {
                    label.textContent = file.name;
                }
            }
        });
    });
    
    // PIN input - only allow numbers and limit to 6 digits
    const pinInputs = document.querySelectorAll('input[name="pin"], input[maxlength="6"]');
    pinInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            // Remove non-numeric characters
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    });
    
    // Study number input - uppercase
    const studyNumberInputs = document.querySelectorAll('input[name="study_number"]');
    studyNumberInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });
    
    // Application ID input - uppercase
    const appIdInputs = document.querySelectorAll('input[name="application_id"]');
    appIdInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });
    
    // Table sorting (if table has data-sort attribute)
    const sortableTables = document.querySelectorAll('table[data-sortable]');
    sortableTables.forEach(function(table) {
        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(function(header) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                const column = this.getAttribute('data-sort');
                sortTable(table, column);
            });
        });
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // Print functionality for reports
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            window.print();
        });
    });
    
    // Confirmation for logout and delete actions
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
    
    // Stream card selection highlight
    const streamCards = document.querySelectorAll('.stream-card');
    streamCards.forEach(function(card) {
        card.addEventListener('click', function() {
            streamCards.forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
    
    // Initialize tooltips (simple implementation)
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(function(el) {
        el.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.bottom + 10 + 'px';
            tooltip.style.opacity = '1';
        });
        
        el.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
    
    // Update available spaces every 30 seconds (if on relevant page)
    const gradeSpacesContainer = document.querySelector('[data-grade-spaces]');
    if (gradeSpacesContainer) {
        setInterval(function() {
            fetch('/api/grade-spaces/')
                .then(response => response.json())
                .then(data => {
                    // Update the display with new data
                    updateGradeSpaces(data.grades);
                })
                .catch(error => console.error('Error fetching grade spaces:', error));
        }, 30000);
    }
    
    // Initialize dynamic widths for marks bars and progress bars
    initMarksBars();
    initProgressBars();
});

// Table sorting function
function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isNumeric = column.includes('marks') || column.includes('grade');
    
    rows.sort(function(a, b) {
        const aValue = a.querySelector('[data-' + column + ']').textContent.trim();
        const bValue = b.querySelector('[data-' + column + ']').textContent.trim();
        
        if (isNumeric) {
            return parseFloat(aValue) - parseFloat(bValue);
        }
        return aValue.localeCompare(bValue);
    });
    
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

// Set dynamic widths for marks bars
function initMarksBars() {
    const marksBars = document.querySelectorAll('[data-marks]');
    marksBars.forEach(function(bar) {
        const marks = bar.getAttribute('data-marks');
        const fill = bar.querySelector('.js-marks-bar');
        if (fill && marks) {
            fill.style.width = marks + '%';
        }
    });
}

// Set dynamic widths for progress bars
function initProgressBars() {
    const progressBars = document.querySelectorAll('[data-filled][data-capacity]');
    progressBars.forEach(function(bar) {
        const filled = parseInt(bar.getAttribute('data-filled')) || 0;
        const capacity = parseInt(bar.getAttribute('data-capacity')) || 1;
        const fill = bar.querySelector('.js-progress-fill');
        if (fill && capacity > 0) {
            const percentage = (filled / capacity) * 100;
            fill.style.width = percentage + '%';
        }
    });
}

// Update grade spaces display
function updateGradeSpaces(grades) {
    grades.forEach(function(grade) {
        const card = document.querySelector('[data-grade="' + grade.grade + '"]');
        if (card) {
            const availableEl = card.querySelector('.available-count');
            const statusEl = card.querySelector('.status-badge');
            
            if (availableEl) {
                availableEl.textContent = grade.available;
                availableEl.className = 'available-count ' + 
                    (grade.available === 0 ? 'full' : grade.available < 5 ? 'limited' : 'available');
            }
            
            if (statusEl) {
                statusEl.className = 'status-badge ' + 
                    (grade.available === 0 ? 'badge-danger' : grade.available < 5 ? 'badge-warning' : 'badge-success');
                statusEl.innerHTML = grade.available === 0 ? 
                    '<i class="fas fa-ban"></i> Full' : 
                    grade.available < 5 ? '<i class="fas fa-exclamation-triangle"></i> Limited' : 
                    '<i class="fas fa-check-circle"></i> Open';
            }
        }
    });
}

// Confirm action helper
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}

// Show notification helper
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = 'notification notification-' + (type || 'info');
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(function() {
        notification.classList.remove('show');
        setTimeout(function() {
            notification.remove();
        }, 300);
    }, 5000);
}
