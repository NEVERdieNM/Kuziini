// Simple JavaScript just for UI feedback, not file handling
document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    
    // Show file name when selected
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            dropArea.classList.add('file-selected');
            
            if (this.files.length === 1) {
                fileNameDisplay.textContent = 'Selected file: ' + this.files[0].name;
            } else {
                fileNameDisplay.textContent = 'Selected files: ' + this.files.length + ' files';
            }
        } else {
            fileNameDisplay.textContent = '';
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
        
        // Trigger change event to update UI
        const event = new Event('change');
        fileInput.dispatchEvent(event);
    });
});