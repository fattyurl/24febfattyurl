// FattyURL JavaScript

// Copy to clipboard
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        var originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fa-solid fa-check mr-1"></i>Copied!';
        button.classList.add('copy-success');
        setTimeout(function() {
            button.innerHTML = originalHTML;
            button.classList.remove('copy-success');
        }, 2000);
    }).catch(function() {
        // Fallback for older browsers
        var textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        var originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fa-solid fa-check mr-1"></i>Copied!';
        button.classList.add('copy-success');
        setTimeout(function() {
            button.innerHTML = originalHTML;
            button.classList.remove('copy-success');
        }, 2000);
    });
}
