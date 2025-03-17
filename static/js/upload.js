document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const fileTypeRadios = document.querySelectorAll('input[name="file_type"]');
    
    // File type selector functionality
    fileTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const selectedType = this.value;
            
            // Reset file input when changing type
            fileInput.value = '';
            fileNameDisplay.textContent = '';
            dropArea.classList.remove('file-selected');
            
            // Update form action URL with the selected type
            const form = this.closest('form');
            form.action = `/upload/${selectedType}`;
            
            // Update UI based on selected type
            updateDropAreaText(selectedType);
        });
    });
    
    // Initialize with default selected type
    const initialSelectedType = document.querySelector('input[name="file_type"]:checked').value;
    updateDropAreaText(initialSelectedType);
    
    // Show file name when selected
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            dropArea.classList.add('file-selected');
            
            const fileName = this.files[0].name;
            fileNameDisplay.textContent = 'Selected file: ' + fileName;
            
            // Validate file extension (.xls or .xlsx)
            if (!fileName.match(/\.(xls|xlsx)$/i)) {
                fileNameDisplay.innerHTML = '<span style="color: #e53935;">Invalid file type. Please select an Excel file (.xls or .xlsx)</span>';
                this.value = ''; // Reset the input
            }
        } else {
            fileNameDisplay.textContent = '';
            dropArea.classList.remove('file-selected');
        }
    });
    
    // Visual feedback for drag and drop
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropArea.classList.add('highlight');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropArea.classList.remove('highlight');
        }, false);
    });
    
    // Handle file drop by setting the file input value
    dropArea.addEventListener('drop', function(e) {
        fileInput.files = e.dataTransfer.files;
        
        // Validate the dropped file
        if (fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            
            if (!fileName.match(/\.(xls|xlsx)$/i)) {
                fileNameDisplay.innerHTML = '<span style="color: #e53935;">Invalid file type. Please select an Excel file (.xls or .xlsx)</span>';
                fileInput.value = ''; // Reset the input
                return;
            }
        }
        
        // Trigger change event to update UI
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    });
    
    // Template download buttons
    const produseTemplateBtn = document.getElementById('produse-template');
    const furnizoriTemplateBtn = document.getElementById('furnizori-template');
    
    // Highlight active template based on selection
    fileTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const selectedType = this.value;
            if (selectedType === 'produse') {
                produseTemplateBtn.style.fontWeight = 'bold';
                furnizoriTemplateBtn.style.fontWeight = 'normal';
            } else {
                produseTemplateBtn.style.fontWeight = 'normal';
                furnizoriTemplateBtn.style.fontWeight = 'bold';
            }
        });
    });
    
    // Initial highlight
    if (initialSelectedType === 'produse') {
        produseTemplateBtn.style.fontWeight = 'bold';
    } else {
        furnizoriTemplateBtn.style.fontWeight = 'bold';
    }
});

/**
 * Updates the drop area text based on the selected file type
 * @param {string} fileType - The selected file type ('produse' or 'furnizori')
 */
function updateDropAreaText(fileType) {
    const dropAreaTitle = document.querySelector('.drop-area h2');
    
    if (fileType === 'produse') {
        dropAreaTitle.textContent = 'Drag & Drop Produse Excel File Here';
    } else if (fileType === 'furnizori') {
        dropAreaTitle.textContent = 'Drag & Drop Furnizori Excel File Here';
    }
}