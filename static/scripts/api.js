const chatMessagesApiURL = "/api/chats/messages";
const apiKey = "y28qS1JlSKapp0ekse4si08lY7vYgv928Vvlsd7yFrjW0xBZ";
const messagesApiURL = "/api/messages";
const newMessagesApiURL = "/api/messages/new";
const usersApiURL = "/api/users";
const userChatsApiURL = "/api/users/chats";

var currentChat = {};
var userId = "";
var userData = {};
var userChats = [];
var createdChats = []
var chats = [];
var chatsMessages = {};
var createdMessages = {};
var data = {};

function loadUserChats() {
    userChats = {};
    for (let chatIndex of Object.keys(chats)) {
        chat = chats[chatIndex];
        chatUsers = chat["users"]["users"];

        if (Object.keys(userChats).includes(parseInt(chat["id"]))) {
            continue;
        }

        if (chatUsers.includes(parseInt(userId))) {
            const anotherUserId = chatUsers.filter(uid => uid != userId)[0];
            chat["name"] = data["users"][anotherUserId]["user_name"];

            const chatMessages = Object.values(data["messages"]).filter(msg => msg["chat_id"] == chat["id"]);
            if (chatMessages.length > 0) {
                chat["lastMessage"] = chatMessages.at(-1)["data"];
            } else {
                chat["lastMessage"] = "";
            }
            userChats[parseInt(chat["id"])] = chat;
            chatsMessages[parseInt(chat["id"])] = [];
        }
    }
}

function loadData(responseData) {
    data = responseData;
    userData = responseData["users"][userId];
    chats = responseData["chats"];

    loadUserChats();
    createChatsFromData();
    for (let msgIndex of Object.keys(responseData["messages"])) {
        msg = responseData["messages"][msgIndex];

        if (Object.keys(userChats).includes(msg["chat_id"].toString())) {
            chatsMessages[parseInt(msg["chat_id"])].push(msg);
        }
    }
}

function createChatsFromData() {
    const userChatsArray = Object.values(userChats);
    for (i = 0; i < userChatsArray.length; i++) {
        const chat = userChatsArray[i];

        if (createdChats.includes(chat["id"])) {
            continue;
        }

        createdChats.push(chat["id"]);
        createdMessages[chat["id"]] = [];

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

function scrollCurrentChatMessages() {
    if (Object.keys(currentChat).length == 0) {
        return;
    }
    const scrollArea = document.getElementById("msgArea" + currentChat.id);
    scrollArea.scrollBy(0, scrollArea.scrollHeight);
}

function openChat(chatId) {
    if (Object.keys(currentChat).length != 0) {
        document.getElementById("sendMsgArea").style.display = "none";
        document.getElementById("msgArea" + currentChat.id).style.display = "none";
        document.getElementById("chatHeader" + currentChat.id).style.display = "none";
    }

    currentChat = chats[chatId];
    document.getElementById("sendMsgArea").style.display = "flex";
    document.getElementById("msgArea" + currentChat.id).style.display = "flow-root";
    document.getElementById("chatHeader" + currentChat.id).style.display = "block";

    scrollCurrentChatMessages();
}

function createMessagesFromData(chatId, callback) {
    if (chatsMessages[chatId].length == 0) {
        return;
    }

    for (i = 0; i < chatsMessages[chatId].length; i++) {
        const msg = chatsMessages[chatId][i];

        if (createdMessages[chatId].includes(msg["id"])) {
            continue;
        }

        const formatted_time = msg["time"].split(" ")[1].split(":");

        newMessage = document.createElement("div");

        if (msg["owner"] == userId) {
            newMessage.classList.add("msg", "owner-msg");
        } else {
            newMessage.classList.add("msg");
        }

        content = document.createElement("div");
        content.classList.add("msg-content");
        newMessage.appendChild(content)

        msgText = document.createElement("span");
        msgText.classList.add("msg-text");
        msgText.appendChild(document.createTextNode(msg["data"]));
        content.appendChild(msgText);

        msgTime = document.createElement("span");
        msgTime.appendChild(document.createTextNode(formatted_time[0] + ":" + formatted_time[1]));
        msgTime.classList.add("msg-time");
        content.appendChild(msgTime);

        msgArea = document.getElementById("msgArea" + msg["chat_id"]);
        msgArea.append(newMessage);

        createdMessages[msg["chat_id"]].push(msg["id"]);
    };

    console.log("Messages loaded!", createdMessages);

    if (callback != null) {
        callback();
        console.log(1)
    }
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

    if (currentChat == "") {
        return
    }

    fetch(messagesApiURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chat_id: currentChat["id"],
            owner: user_id,
            data: msgDataInput.value
        })
    })
    .then(response => response.json())
    .then(data => {
//        loadNewMessagesFromServer(null, user_id, scrollCurrentChatMessages);
        chatsMessages[currentChat["id"]].push(data["newMessage"]);
        createMessagesFromData(currentChat["id"], scrollCurrentChatMessages);
        msgDataInput.value = "";
    })
    .catch(error => console.error('Ошибка:', error));
}

//function loadNewMessagesFromServer(chat, user, callback = null) {
//    const chatId = chat ? chat : currentChat;
//    const currentUser = user ? user: userId;
//
//    if (chatId == "" || currentUser == "") {
//        return
//    }
//
//    fetch(newMessagesApiURL + "/" + chatId, {
//        method: 'GET',
//        headers: { 'Content-Type': 'application/json' }
//    })
//    .then(response => response.json())
//    .then(data => {
//        createMessagesFromPromise(data, chatId, currentUser, callback);
//        lastMsg = data["messages"][data["messages"].length - 1]["data"];
//        document.getElementById("lastMsg" + chatId).textContent = lastMsg;
//        // readAllMessagesInChat();
//    })
//    .catch(error => console.error('Ошибка:', error));
//}

//function readAllMessagesInChat(chatId) {
//    fetch(newMessagesApiURL + "/" + (chatId ? chatId : currentChat), {
//        method: 'POST',
//        headers: { 'Content-Type': 'application/json' }
//    })
//    .then(response => response.json())
//    .then(data => console.log(data))
//    .catch(error => console.error('Ошибка:', error));
//}
//
//function loadMessages(chatId, currentUserId) {
//    fetch(chatMessagesApiURL + "/" + chatId, {
//        method: 'GET',
//        headers: { 'Content-Type': 'application/json' }
//    })
//    .then(response => response.json())
//    .then(data => createMessagesFromPromise(data, chatId, currentUserId))
//    .catch(error => console.error("Ошибка:", error))
//}
