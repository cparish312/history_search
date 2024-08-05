function attachEnterKeyHandler() {
    const searchInput = document.getElementById('input-search');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('button-search').click();
            }
        });
    } else {
        // If the element is not found, check again after a short delay
        setTimeout(attachEnterKeyHandler, 100);
    }
}

// Attach the event handler initially and reattach whenever the DOM updates
document.addEventListener('DOMContentLoaded', attachEnterKeyHandler);
document.addEventListener('DOMSubtreeModified', function(e) {
    if (e.target.id === 'input-search') {
        attachEnterKeyHandler();
    }
});