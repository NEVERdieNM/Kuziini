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


















// document.addEventListener('DOMContentLoaded', function() {
//     const dropArea = document.getElementById('drop-area');
//     const fileInput = document.getElementById('file-input');
//     const browseBtn = document.getElementById('browse-btn');
//     const fileList = document.getElementById('file-list');
//     const uploadBtn = document.getElementById('upload-btn');
    
//     let currentFile = null; // Store only one file
    
//     // Prevent default drag behaviors
//     ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
//         dropArea.addEventListener(eventName, preventDefaults, false);
//         document.body.addEventListener(eventName, preventDefaults, false);
//     });
    
//     function preventDefaults(e) {
//         e.preventDefault();
//         e.stopPropagation();
//     }
    
//     // Highlight drop area when item is dragged over it
//     ['dragenter', 'dragover'].forEach(eventName => {
//         dropArea.addEventListener(eventName, highlight, false);
//     });
    
//     ['dragleave', 'drop'].forEach(eventName => {
//         dropArea.addEventListener(eventName, unhighlight, false);
//     });
    
//     function highlight() {
//         dropArea.classList.add('active');
//     }
    
//     function unhighlight() {
//         dropArea.classList.remove('active');
//     }
    
//     // Handle dropped files
//     dropArea.addEventListener('drop', handleDrop, false);
    
//     function handleDrop(e) {
//         const dt = e.dataTransfer;
//         const droppedFiles = dt.files;
//         // Take only the first file if multiple are dropped
//         if (droppedFiles.length > 0) {
//             handleFile(droppedFiles[0]);
//         }
//     }
    
//     // Open file browser when the browse button is clicked
//     browseBtn.addEventListener('click', () => {
//         fileInput.click();
//     });
    
//     // Handle file from file input
//     fileInput.addEventListener('change', () => {
//         if (fileInput.files.length > 0) {
//             handleFile(fileInput.files[0]);
//         }
//         fileInput.value = ''; // Reset input so same file can be selected again
//     });
    
//     // Process the single file
//     function handleFile(file) {
//         currentFile = file;
//         updateFileDisplay();
//         updateUploadButton();
//     }
    
//     // Update the file display
//     function updateFileDisplay() {
//         // Clear the file list first
//         fileList.innerHTML = '';
        
//         if (currentFile) {
//             const fileSize = formatFileSize(currentFile.size);
            
//             const fileItem = document.createElement('div');
//             fileItem.className = 'file-item';
            
//             fileItem.innerHTML = `
//                 <div class="file-info">
//                     <span class="file-icon">📄</span>
//                     <span class="file-name">${currentFile.name}</span>
//                     <span class="file-size">${fileSize}</span>
//                 </div>
//                 <button class="remove-btn">✕</button>
//             `;
            
//             fileList.appendChild(fileItem);
            
//             // Add event listener to remove button
//             const removeBtn = fileItem.querySelector('.remove-btn');
//             removeBtn.addEventListener('click', () => {
//                 currentFile = null;
//                 fileList.innerHTML = '';
//                 updateUploadButton();
//             });
//         }
//     }
    
//     // Format file size
//     function formatFileSize(bytes) {
//         if (bytes === 0) return '0 Bytes';
//         const k = 1024;
//         const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
//         const i = Math.floor(Math.log(bytes) / Math.log(k));
//         return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
//     }
    
//     // Update upload button state
//     function updateUploadButton() {
//         uploadBtn.disabled = !currentFile;
//     }
    
//     // Handle the upload process
//     uploadBtn.addEventListener('click', () => {
//         if (!currentFile) return;
        
//         // Prepare file for pywebview
//         uploadBtn.textContent = 'Uploading...';
//         uploadBtn.disabled = true;
        
//         // Convert file to base64 and collect metadata
//         const reader = new FileReader();
        
//         reader.onload = () => {
//             // Get base64 data without MIME prefix
//             const base64Data = reader.result.split(',')[1];
            
//             const fileData = {
//                 name: currentFile.name,
//                 type: currentFile.type,
//                 size: currentFile.size,
//                 data: base64Data
//             };
            
//             // Call Python function via pywebview API
//             console.log('Sending file to Python:', fileData);
//             window.pywebview.api.process_file(fileData).then(response => {
//                 console.log('Python response:', response);
//                 alert('File processed successfully!');
                
//                 const data = JSON.parse(response);
//                 console.log(data);

//                 // Clear file display after upload
//                 currentFile = null;
//                 fileList.innerHTML = '';
//                 uploadBtn.textContent = 'Upload File';
//                 updateUploadButton();
//             }).catch(error => {
//                 console.error('Error processing file:', error);
//                 alert('Error processing file: ' + error);
//                 uploadBtn.textContent = 'Upload File';
//                 uploadBtn.disabled = false;
//             });
//         };
        
//         reader.readAsDataURL(currentFile);
//     });
// });