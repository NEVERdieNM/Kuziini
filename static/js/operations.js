document.addEventListener('DOMContentLoaded', function() {
    const calculatePricesBtn = document.getElementById('calculate-prices-btn');
    const updateSuppliersBtn = document.getElementById('update-suppliers-btn');
    const resultContainer = document.getElementById('result-container');
    const resultContent = document.getElementById('result-content');
    
    // Helper function for displaying loading state
    function setButtonLoading(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            const originalText = button.textContent.trim();
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = `<span class="spinner"></span> Processing...`;
        } else {
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            button.textContent = originalText;
        }
    }
    
    // Handle Calculate Prices button
    calculatePricesBtn.addEventListener('click', function() {
        executeOperation('calculate_prices', calculatePricesBtn);
    });
    
    // Handle Update Suppliers button
    updateSuppliersBtn.addEventListener('click', function() {
        executeOperation('update_suppliers', updateSuppliersBtn);
    });
    
    // Execute operation via AJAX
    function executeOperation(operation, button) {
        // Show loading state
        setButtonLoading(button, true);
        
        // Make AJAX request
        fetch(`/operations/${operation}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Display results
            displayResults(data, operation);
            
            // Reset button state
            setButtonLoading(button, false);
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Display error message
            resultContent.innerHTML = `
                <div class="result-summary result-error">
                    <strong>Error:</strong> ${error.message || 'An error occurred during the operation.'}
                </div>
            `;
            resultContainer.style.display = 'block';
            
            // Reset button state
            setButtonLoading(button, false);
        });
    }
    
    // Display results based on operation type
    function displayResults(data, operation) {
        let html = '';
        
        if (operation === 'calculate_prices') {
            // Results for price calculation
            html = `
                <div class="result-summary ${data.success ? 'result-success' : 'result-warning'}">
                    <strong>${data.success ? 'Success!' : 'Completed with warnings'}</strong> Price calculation completed.
                </div>
                <div class="result-details">
                    <div class="result-item">
                        <span class="result-label">Total Products:</span>
                        <span class="result-value">${data.stats.total_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Updated Products:</span>
                        <span class="result-value result-success">${data.stats.updated_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">No initial price:</span>
                        <span class="result-value ${data.stats.no_initial_price_products > 0 ? 'result-error' : ''}">${data.stats.no_initial_price_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Failed:</span>
                        <span class="result-value ${data.stats.failed_products > 0 ? 'result-error' : ''}">${data.stats.failed_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">No Supplier:</span>
                        <span class="result-value ${data.stats.no_supplier_products > 0 ? 'result-warning' : ''}">${data.stats.no_supplier_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Missing Markup:</span>
                        <span class="result-value ${data.stats.no_adaos_suppliers > 0 ? 'result-warning' : ''}">${data.stats.no_adaos_suppliers}</span>
                    </div>
                </div>
            `;
            
            // Add list of suppliers without markup if any
            if (data.stats.suppliers_without_adaos && data.stats.suppliers_without_adaos.length > 0) {
                html += `
                    <div class="result-warning" style="margin-top: 15px;">
                        <strong>Suppliers without markup:</strong>
                        <div class="result-list">
                            ${data.stats.suppliers_without_adaos.map(supplier => 
                                `<div class="result-list-item">${supplier}</div>`
                            ).join('')}
                        </div>
                    </div>
                `;
            }
        } else if (operation === 'update_suppliers') {
            // Results for supplier update
            html = `
                <div class="result-summary ${data.success ? 'result-success' : 'result-warning'}">
                    <strong>${data.success ? 'Success!' : 'Completed with warnings'}</strong> Supplier update completed.
                </div>
                <div class="result-details">
                    <div class="result-item">
                        <span class="result-label">Total Products:</span>
                        <span class="result-value">${data.stats.total_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Updated Products:</span>
                        <span class="result-value result-success">${data.stats.updated_products}</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">Failed:</span>
                        <span class="result-value ${data.stats.failed_products > 0 ? 'result-error' : ''}">${data.stats.failed_products}</span>
                    </div>
                </div>
            `;
            
            // Add list of suppliers not found if any
            if (data.stats.not_found_suppliers && data.stats.not_found_suppliers.length > 0) {
                html += `
                    <div class="result-warning" style="margin-top: 15px;">
                        <strong>Suppliers not found:</strong>
                        <div class="result-list">
                            ${data.stats.not_found_suppliers.map(supplier => 
                                `<div class="result-list-item">${supplier}</div>`
                            ).join('')}
                        </div>
                    </div>
                `;
            }
        } else {
            // Generic result display
            html = `
                <div class="result-summary ${data.success ? 'result-success' : 'result-error'}">
                    <strong>${data.success ? 'Success!' : 'Error'}</strong> ${data.message || 'Operation completed.'}
                </div>
            `;
        }
        
        // Update the result container and show it
        resultContent.innerHTML = html;
        resultContainer.style.display = 'block';
        
        // Scroll to results
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }
});