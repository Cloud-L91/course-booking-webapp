function setupPasswordToggle(buttonId, inputId, iconId) {
    const toggleBtn = document.getElementById(buttonId);
    const inputField = document.getElementById(inputId);
    const icon = document.getElementById(iconId);

    if (toggleBtn && inputField && icon) {
        toggleBtn.addEventListener('click', function () {
            const isPassword = inputField.type === 'password';
            inputField.type = isPassword ? 'text' : 'password';
            
            icon.classList.toggle('bi-eye', !isPassword);
            icon.classList.toggle('bi-eye-slash', isPassword);
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    setupPasswordToggle('togglePassword', 'password', 'togglePasswordIcon');
    setupPasswordToggle('toggleConfirmPassword', 'confirm_password', 'toggleConfirmPasswordIcon');
});