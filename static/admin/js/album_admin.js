document.addEventListener('DOMContentLoaded', function() {
    const typeField = document.getElementById('id_type');
    const eventField = document.querySelector('.field-event');
    const batchYearField = document.querySelector('.field-batch_year');
    
    function toggleFields() {
        const selectedType = typeField.value;
        
        // Hide all fields initially
        if (eventField) eventField.style.display = 'none';
        if (batchYearField) batchYearField.style.display = 'none';
        
        // Show relevant fields based on type
        if (selectedType === 'eesa' && eventField) {
            eventField.style.display = 'block';
        } else if (selectedType === 'alumni' && batchYearField) {
            batchYearField.style.display = 'block';
        } else if (selectedType === 'general') {
            // General albums don't need event or batch_year
        }
        
        // Clear values for hidden fields to prevent constraint errors
        if (selectedType !== 'eesa' && document.getElementById('id_event')) {
            document.getElementById('id_event').value = '';
        }
        if (selectedType !== 'alumni' && document.getElementById('id_batch_year')) {
            document.getElementById('id_batch_year').value = '';
        }
    }
    
    // Initial toggle
    toggleFields();
    
    // Toggle on change
    if (typeField) {
        typeField.addEventListener('change', toggleFields);
    }
});
