document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const productCheckboxes = document.querySelectorAll('.product-select');
    const selectedCounter = document.getElementById('selected-counter');
    const totalCount = productCheckboxes.length;
    
    // Update counter function
    function updateCounter() {
        const selectedCount = document.querySelectorAll('.product-select:checked').length;
        selectedCounter.textContent = `${selectedCount} / ${totalCount} selected`;
    }
    
    // Set up select all checkbox
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            
            productCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            updateCounter();
        });
    }
    
    // Set up product checkboxes
    productCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Check if all checkboxes are checked
            const allChecked = Array.from(productCheckboxes).every(cb => cb.checked);
            const anyChecked = Array.from(productCheckboxes).some(cb => cb.checked);
            
            // Update select all checkbox
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = !allChecked && anyChecked;
            }
            
            updateCounter();
        });
    });
    
    // Initial counter update
    updateCounter();
    
    // Toggle details functionality
    const toggleButtons = document.querySelectorAll('.toggle-details-btn');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Find the parent product card
            const productCard = this.closest('.product-card');
            
            // Find the details section
            const productDetails = productCard.querySelector('.product-details');
            
            // Toggle visibility
            if (productDetails.style.display === 'none' || !productDetails.style.display) {
                productDetails.style.display = 'block';
                this.textContent = 'Hide Details';
                this.classList.add('active');
            } else {
                productDetails.style.display = 'none';
                this.textContent = 'Show Details';
                this.classList.remove('active');
            }
        });
    });
    
    // Toggle all details button
    const toggleAllBtn = document.getElementById('toggle-all-btn');
    
    if (toggleAllBtn) {
        toggleAllBtn.addEventListener('click', function() {
            const productDetails = document.querySelectorAll('.product-details');
            const isAnyHidden = Array.from(productDetails).some(detail => 
                detail.style.display === 'none' || !detail.style.display);
            
            // Update all product details visibility
            productDetails.forEach(detail => {
                detail.style.display = isAnyHidden ? 'block' : 'none';
            });
            
            // Update all toggle buttons
            toggleButtons.forEach(button => {
                if (isAnyHidden) {
                    button.textContent = 'Hide Details';
                    button.classList.add('active');
                } else {
                    button.textContent = 'Show Details';
                    button.classList.remove('active');
                }
            });
            
            // Update toggle all button text
            this.textContent = isAnyHidden ? 'Hide All Details' : 'Show All Details';
        });
    }
});