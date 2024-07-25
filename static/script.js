document.addEventListener("DOMContentLoaded", function() {
    function fetchLogs() {
        fetch('/')
            .then(response => response.text())
            .then(data => {
                document.body.innerHTML = data;
                applyTypewriterEffect();
            });
    }

    function applyTypewriterEffect() {
        document.querySelectorAll('pre').forEach((pre) => {
            const text = pre.innerHTML.replace(/<br>/g, "\n");
            pre.innerHTML = '';
            let index = 0;

            function type() {
                if (index < text.length) {
                    pre.innerHTML += text.charAt(index) === '\n' ? '<br>' : text.charAt(index);
                    index++;
                    adjustFontSize(pre);
                    setTimeout(type, 20); // Adjust typing speed here
                }
            }
            type();
        });
    }

    function adjustFontSize(element) {
        let fontSize = 25; // Initial font size
        element.style.fontSize = `${fontSize}px`;

        while (element.scrollHeight > element.clientHeight || element.scrollWidth > element.clientWidth) {
            fontSize--;
            if (fontSize < 10) break; // Minimum font size to prevent it from becoming too small
            element.style.fontSize = `${fontSize}px`;
        }
    }

    fetchLogs();
    setInterval(fetchLogs, 9000); // Refresh every 9 seconds
});