// server/static/admin.js - Simple version
document.addEventListener('DOMContentLoaded', function() {
    // Simple confirmation for delete actions
    const deleteButtons = document.querySelectorAll('button[onclick*="confirm"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure?')) {
                e.preventDefault();
            }
        });
    });
    
    console.log('DealTracker Admin Panel loaded successfully');
});
