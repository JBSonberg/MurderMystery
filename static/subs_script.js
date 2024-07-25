document.addEventListener("DOMContentLoaded", function () {
    const CHUNK_SIZE = 100; // target number of characters per chunk
    let audio = document.getElementById('audio');
    let subtitleDiv = document.getElementById('subtitles');
    let subtitleChunks = [];
    let currentIndex = 0;

    // Function to play audio automatically when the page loads
    const playAudio = () => {
        audio.play().catch(error => {
            console.error('Autoplay was prevented:', error);
        });
    };

    // Fetch the subtitle data from the Flask endpoint
    const fetchSubtitles = async () => {
        try {
            let response = await fetch('/subtitles');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            let subtitles = await response.json();
            console.log('Subtitles fetched:', subtitles); // Debugging line

            // Group subtitles into chunks
            groupSubtitlesIntoChunks(subtitles);
            console.log('Grouped Subtitles:', subtitleChunks); // Debugging line
        } catch (error) {
            console.error("Error fetching subtitles:", error);
        }
    };

    // Function to group subtitle characters into words
    const groupCharactersIntoWords = (subtitles) => {
        let words = [];
        let word = '';
        let wordStartTime = 0;
        let wordEndTime = 0;

        subtitles.forEach((subtitle, index) => {
            if (subtitle.character.match(/\s+/)) {
                words.push({ text: word, start_time: wordStartTime, end_time: wordEndTime });
                word = '';
            } else {
                if (word === '') {
                    wordStartTime = subtitle.start_time;
                }
                word += subtitle.character;
                wordEndTime = subtitle.end_time;
            }

            // Add the last word
            if (index === subtitles.length - 1 && word !== '') {
                words.push({ text: word, start_time: wordStartTime, end_time: wordEndTime });
            }
        });

        return words;
    };

    // Function to group words into chunks based on the target character length
    const groupSubtitlesIntoChunks = (subtitles) => {
        let words = groupCharactersIntoWords(subtitles);
        let chunk = '';
        let chunkStartTime = 0;
        let chunkEndTime = 0;

        words.forEach((word, index) => {
            let nextWord = word.text;
            let nextEndTime = word.end_time;

            // Check if adding the next word would exceed the target character length
            if (chunk.length + nextWord.length <= CHUNK_SIZE || chunk === '') { // Ensure we start a new chunk on an empty string
                if (chunk === '') {
                    chunkStartTime = word.start_time;
                }
                chunk += ' ' + nextWord;
                chunkEndTime = word.end_time;
            } else {
                subtitleChunks.push({ text: chunk.trim(), start_time: chunkStartTime, end_time: chunkEndTime });
                chunk = nextWord;
                chunkStartTime = word.start_time;
                chunkEndTime = word.end_time;
            }

            // Add the last chunk if this is the last word
            if (index === words.length - 1 && chunk !== '') {
                subtitleChunks.push({ text: chunk.trim(), start_time: chunkStartTime, end_time: chunkEndTime });
            }
        });
    };

    fetchSubtitles();

    audio.addEventListener('timeupdate', function () {
        if (subtitleChunks.length > 0) {
            let currentTime = audio.currentTime;
            let currentChunk = subtitleChunks[currentIndex];

            // Display the current chunk if its start time is less than the current time
            if (currentChunk && currentTime >= currentChunk.start_time) {
                subtitleDiv.innerHTML = currentChunk.text;
                console.log('Current Chunk:', currentChunk.text); // Debugging line

                // Move to the next chunk if the end time of the current chunk is exceeded
                if (currentTime >= currentChunk.end_time) {
                    currentIndex++;
                }
            }
        }
    });
    playAudio();
});