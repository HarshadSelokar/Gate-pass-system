document.addEventListener('DOMContentLoaded', function () {
    // Example: show an alert after successfully marking exit time
    const successMessage = document.getElementById('success-message');
    if (successMessage) {
        alert(successMessage.innerText);
    }
});
