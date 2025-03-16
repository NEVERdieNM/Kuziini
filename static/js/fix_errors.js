document.addEventListener('DOMContentLoaded', function() {
    // Get all error inputs
    const errorInputs = document.querySelectorAll('.error-input');
    const allInputs = document.querySelectorAll('.error-input, .regular-input');
    
    // Add input validation for each error field
    errorInputs.forEach(input => {
        // Store original value for reset functionality
        const originalValue = input.dataset.original;
        const expectedType = input.dataset.expectedType;
        
        // Add validation on input change
        input.addEventListener('input', function() {
            validateInput(input, expectedType);
        });
        
        // Initial validation
        validateInput(input, expectedType);
    });
    
    // Track changes in all inputs
    allInputs.forEach(input => {
        input.addEventListener('input', function() {
            input.dataset.changed = (input.value !== input.dataset.original).toString();
        });
    });
    
    // Toggle show/hide all fields
    const toggleButtons = document.querySelectorAll('.toggle-details-btn');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Find the parent error card
            const errorCard = this.closest('.error-card');
            // Find the all-fields section
            const allFields = errorCard.querySelector('.all-fields');
            
            // Toggle visibility
            if (allFields.style.display === 'none') {
                allFields.style.display = 'block';
                this.textContent = 'Hide All Fields';
                this.classList.add('active');
            } else {
                allFields.style.display = 'none';
                this.textContent = 'Show All Fields';
                this.classList.remove('active');
            }
        });
    });
    
    // Reset all fields to original values
    const resetAllBtn = document.getElementById('reset-all');
    resetAllBtn.addEventListener('click', function() {
        allInputs.forEach(input => {
            input.value = input.dataset.original;
            input.dataset.changed = 'false';
            
            if (input.classList.contains('error-input')) {
                validateInput(input, input.dataset.expectedType);
            }
        });
    });
    
    // Form submission preparation
    const form = document.getElementById('fix-form');
    const correctionsInput = document.getElementById('corrections-data');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Validate all error inputs first
        let hasErrors = false;
        errorInputs.forEach(input => {
            if (!validateInput(input, input.dataset.expectedType)) {
                hasErrors = true;
            }
        });
        
        if (hasErrors) {
            alert('Please correct all errors before submitting.');
            return;
        }
        
        // Create an array to hold the corrected data
        const corrections = [];
        
        // Get all error cards (representing rows)
        const errorCards = document.querySelectorAll('.error-card');
        errorCards.forEach(card => {
            const rowId = card.dataset.rowId;
            const excelRow = card.dataset.excelRow;
            const rowInputs = card.querySelectorAll('.error-input, .regular-input');
            
            // Create an object for this row's data
            const rowData = {
                row_id: parseInt(rowId),
                excel_row_number: parseInt(excelRow),
                data: {}
            };
            
            // Add all fields to the data object
            rowInputs.forEach(input => {
                const fieldName = input.dataset.field;
                let fieldValue = input.value.trim();
                
                // Convert to appropriate type if it's a number field
                if (input.dataset.expectedType === 'REAL' || input.dataset.expectedType === 'FLOAT') {
                    fieldValue = parseFloat(fieldValue);
                } else if (input.dataset.expectedType === 'INTEGER' || input.dataset.expectedType === 'INT') {
                    fieldValue = parseInt(fieldValue);
                }
                
                rowData.data[fieldName] = fieldValue;
            });
            
            corrections.push(rowData);
        });
        
        // Set the value of the hidden input
        correctionsInput.value = JSON.stringify(corrections);
        
        // Submit the form
        form.submit();
    });
});

/**
 * Validate input based on expected type
 * @param {HTMLInputElement} input - The input element to validate
 * @param {string} expectedType - The expected data type (e.g., "REAL", "TEXT")
 * @returns {boolean} - Whether input is valid
 */
function validateInput(input, expectedType) {
    const value = input.value.trim();
    let isValid = true;
    
    switch (expectedType) {
        case 'REAL':
        case 'FLOAT':
            // Check if value is a valid number
            isValid = /^-?\d*\.?\d+$/.test(value) && !isNaN(parseFloat(value));
            break;
        case 'INTEGER':
        case 'INT':
            // Check if value is a valid integer
            isValid = /^-?\d+$/.test(value) && !isNaN(parseInt(value));
            break;
        case 'TEXT':
            // Text can be anything, but shouldn't be empty
            isValid = value !== '';
            break;
        default:
            // For other types, just ensure not empty
            isValid = value !== '';
    }
    
    // Update input styling
    if (isValid) {
        input.classList.remove('invalid-input');
        input.classList.add('valid-input');
    } else {
        input.classList.remove('valid-input');
        input.classList.add('invalid-input');
    }
    
    return isValid;
}