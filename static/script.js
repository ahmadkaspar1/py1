// static/script.js
function sendCommand(command) {
    fetch('/command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `command=${command}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // تحديث الرسائل دون تحديث الصفحة
            const messagesDiv = document.getElementById('messages');
            const newMessage = document.createElement('p');
            newMessage.innerText = data.message;
            messagesDiv.appendChild(newMessage);
            messagesDiv.scrollTop = messagesDiv.scrollHeight; // التمرير للأسفل

            // إدارة عرض الأقسام بناءً على الخطوة
            if (data.message.includes("Choose a language")) {
                document.getElementById('language-selection').style.display = 'block';
                document.getElementById('mode-selection').style.display = 'none';
            } else if (data.message.includes("Choose a mode")) {
                document.getElementById('language-selection').style.display = 'none';
                document.getElementById('mode-selection').style.display = 'block';
            } else {
                document.getElementById('language-selection').style.display = 'none';
                document.getElementById('mode-selection').style.display = 'none';
            }
        } else {
            alert(data.message); // عرض رسالة الخطأ
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred.');
    });
}

// تحديث الرسائل بشكل دوري
setInterval(() => {
    fetch('/get_messages')
        .then(response => response.json())
        .then(data => {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = ''; // مسح الرسائل السابقة
            data.messages.forEach(message => {
                const newMessage = document.createElement('p');
                newMessage.innerText = message;
                messagesDiv.appendChild(newMessage);
            });
            messagesDiv.scrollTop = messagesDiv.scrollHeight; // التمرير للأسفل
        })
        .catch(error => {
            console.error('Error fetching messages:', error);
        });
}, 1000); // تحديث كل ثانية