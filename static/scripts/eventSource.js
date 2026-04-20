
const AppAPIKey = "y28qS1JlSKapp0ekse4si08lY7vYgv928Vvlsd7yFrjW0xBZ";
const eventSource = new EventSource('/event-stream?apikey=' + AppAPIKey);
const responseJson = {};

eventSource.onmessage = function (event) {
    responseJson = JSON.parse(event.data);
}

eventSource.onerror = function (error) {
    console.error('EventSource failed:', error);
    eventSource.close();
}