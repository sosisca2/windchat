const chatMessagesApiURL = "/api/chats/messages";
const apiKey = "y28qS1JlSKapp0ekse4si08lY7vYgv928Vvlsd7yFrjW0xBZ";
const messagesApiURL = "/api/messages";
const newMessagesApiURL = "/api/messages/new";
const usersApiURL = "/api/users";
const userChatsApiURL = "/api/users/chats";

var current_chat = "";
var userId = "";
var chats = [];
var messages = {}

function createChatsFromPromise(data) {
    const userChats = data["chats"];
    for (i = 0; i < userChats.length; i++) {
        const chat = userChats[i];

        if (chats.includes(chat["id"])) {
            continue;
        }

        chats.push(chat["id"]);
        messages[chat["id"]] = [];

        const chatBtn = document.createElement("div");
        chatBtn.id = "chatBtn" + chat["id"];
        chatBtn.classList.add("chat-btn");
        chatBtn.onclick = () => openChat(chat["id"]);

        const iconImage = document.createElement("img");
        iconImage.src = "static/images/chat-default.svg";
        iconImage.alt = "";

        const chatIcon = document.createElement("div");
        chatIcon.classList.add("chat-icon");
        chatIcon.appendChild(iconImage);
        chatBtn.append(chatIcon);

        const chatInfo = document.createElement("div");
        chatInfo.classList.add("chat-info");

        const chatName = document.createElement("div");
        chatName.appendChild(document.createTextNode(chat["name"]));
        chatName.classList.add("chat-name");
        chatInfo.appendChild(chatName);

        const lastMsg = document.createElement("div");
        lastMsg.classList.add("last-msg");
        lastMsg.id = "lastMsg" + chat["id"];
        lastMsg.appendChild(document.createTextNode(chat["lastMessage"]));
        chatInfo.appendChild(lastMsg);

        chatBtn.appendChild(chatInfo);

        const chatsArea = document.getElementById("chatsArea");
        chatsArea.append(chatBtn);
    }
}

function loadChatsFromServer() {
    fetch(userChatsApiURL + "/" + userId, {
        method: 'get',
        headers: { 'Content-Type': 'application/json' },
    })
    .then(response => response.json())
    .then(data => {
        console.log("Chats updated!");
        createChatsFromPromise(data);
    })
    .catch(error => console.error('Ошибка:', error));
}

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

function createMessagesFromPromise(data, chatId, currentUserId, callback = null) {
    if (data["messages"].length == 0) {
        return;
    }

    for (i = 0; i < data["messages"].length; i++) {
        msg = data["messages"][i];

        if (messages[chatId].includes(msg["id"])) {
            continue;
        }

        createMessage(chatId, msg["data"], msg["time"], msg["owner"], currentUserId);
        messages[chatId].push(msg["id"]);
    };

    console.log("Messages loaded!", messages);

    if (callback != null) {callback()}
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
        loadNewMessagesFromServer(null, user_id, scrollCurrentChatMessages);
        msgDataInput.value = "";
    })
    .catch(error => console.error('Ошибка:', error));
}

function loadNewMessagesFromServer(chat, user, callback = null) {
    const chatId = chat ? chat : current_chat;
    const currentUser = user ? user: userId;

    if (chatId == "" || currentUser == "") {
        return
    }

    fetch(newMessagesApiURL + "/" + chatId, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        createMessagesFromPromise(data, chatId, currentUser, callback);
        lastMsg = data["messages"][data["messages"].length - 1]["data"];
        document.getElementById("lastMsg" + chatId).textContent = lastMsg;
        // readAllMessagesInChat();
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
