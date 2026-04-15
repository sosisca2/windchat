const chatMessagesApiURL = "/api/chats/messages";
const apiKey = "y28qS1JlSKapp0ekse4si08lY7vYgv928Vvlsd7yFrjW0xBZ";
const messagesApiURL = "/api/messages";
const newMessagesApiURL = "/api/messages/new";

var current_chat = "";

function scrollCurrentChatMessages() {
    const scrollArea = document.getElementById("msgArea" + current_chat);
    scrollArea.scrollBy(0, scrollArea.scrollHeight);
}

function openChat(chatId) {
    if (current_chat != "") {
        document.getElementById("sendMsgArea").style.display = "none";
        document.getElementById("msgArea" + current_chat).style.display = "none";
        document.getElementById("chatHeader" + current_chat).style.display = "none";
    }

    current_chat = chatId;
    document.getElementById("sendMsgArea").style.display = "flex";
    document.getElementById("msgArea" + chatId).style.display = "flow-root";
    document.getElementById("chatHeader" + current_chat).style.display = "block";

    scrollCurrentChatMessages();
}

function createMessage(chatId, data, time, ownerId, currentUserId) {
    const formatted_time = time.split(" ")[1].split(":");

    newMessage = document.createElement("div");

    if (ownerId == currentUserId) {
        newMessage.classList.add("msg", "owner-msg");
    } else {
        newMessage.classList.add("msg");
    }

    content = document.createElement("div");
    content.classList.add("msg-content");
    newMessage.appendChild(content)

    msgText = document.createElement("span");
    msgText.classList.add("msg-text");
    msgText.appendChild(document.createTextNode(data));
    content.appendChild(msgText);

    msgTime = document.createElement("span");
    msgTime.appendChild(document.createTextNode(formatted_time[0] + ":" + formatted_time[1]));
    msgTime.classList.add("msg-time");
    content.appendChild(msgTime);

    msgArea = document.getElementById("msgArea" + chatId);
    msgArea.append(newMessage);
}

function createMessagesFromPromise(data, chatId, currentUserId) {
    console.log(data["messages"])
    for (i = 0; i < data["messages"].length; i++) {
        msg = data["messages"][i];
        createMessage(chatId, msg["data"], msg["time"], msg["owner"], currentUserId);
    };

    scrollCurrentChatMessages();
}

function sendMessageToServer(user_id, event = null) {
    if (event != null) {
        const keyPressed = event.key;
        if (keyPressed != "Enter") {
            return;
        }
    }

    msgDataInput = document.getElementById("msgDataInput")
    if (msgDataInput.value == "") {
        return
    }

    if (current_chat == "") {
        return
    }

    fetch(messagesApiURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chat_id: current_chat,
            owner: user_id,
            data: msgDataInput.value
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        loadNewMessagesFromServer(null, user_id);
        // document.getElementById("msgArea" + current_chat).scrollTop = 100;
        msgDataInput.value = "";
    })
    .catch(error => console.error('Ошибка:', error));
}

function loadNewMessagesFromServer(chatId, currentUserId) {
    chatId = this.chatId ? this.chatId : current_chat
    fetch(newMessagesApiURL + "/" + chatId, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        createMessagesFromPromise(data, chatId, currentUserId);
        readAllMessagesInChat();
    })
    .catch(error => console.error('Ошибка:', error));
}

function readAllMessagesInChat(chatId) {
    fetch(newMessagesApiURL + "/" + (chatId ? chatId : current_chat), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Ошибка:', error));
}

function loadMessages(chatId, currentUserId) {
    fetch(chatMessagesApiURL + "/" + chatId, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => createMessagesFromPromise(data, chatId, currentUserId))
    .catch(error => console.error("Ошибка:", error))
}
