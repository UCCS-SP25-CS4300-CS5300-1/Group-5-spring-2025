document.addEventListener("DOMContentLoaded", () => {
    // Chat toggle
    const chatToggle = document.getElementById('chat-toggle');
    const chatBox = document.getElementById('chat-box');
  
    if (chatToggle && chatBox) {
      chatToggle.addEventListener('click', () => {
        chatBox.classList.toggle('open');
      });
    }
  
    // Initial chatbot prompt
    const chatOptions = [
      "What are the best tips for first-time campers?",
      "I'm an expert camper, give me a challenge.",
    ];
    
    const container = document.getElementById('chat-options');
    if (container) {
        renderOptions(chatOptions);
        }

    function renderOptions(options) {
      const container = document.getElementById('chat-options');
      container.innerHTML = '';
      options.forEach(option => {
        const btn = document.createElement('button');
        btn.innerText = option;
        btn.className = "btn btn-outline-primary my-1";
        btn.onclick = () => sendPrewritten(option);
        container.appendChild(btn);
      });
    }
  
    function sendPrewritten(message) {
      const log = document.getElementById('chat-log');
      log.innerHTML += `<div><strong>You:</strong> ${message}</div>`;
  
      fetch('/chatbot/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ message })
      })
        .then(res => res.json())
        .then(data => {
          const reply = data.reply;
          let mainResponse = reply;
          const followupSplit = reply.split("Follow-up questions:");
          if (followupSplit.length > 1) {
            mainResponse = followupSplit[0].trim();
          }
  
          log.innerHTML += `<div><strong>Bot:</strong> ${mainResponse}</div>`;
          log.scrollTop = log.scrollHeight;
  
          const followUps = data.followups;
          if (followUps && Array.isArray(followUps)) {
            const container = document.getElementById('chat-options');
            container.innerHTML = '';
            followUps.forEach(q => {
              if (q.length <= 100) {
                const btn = document.createElement('button');
                btn.innerText = q;
                btn.className = "btn btn-outline-secondary my-1";
                btn.onclick = () => sendPrewritten(q);
                container.appendChild(btn);
              }
            });
          }
        })
        .catch(err => {
          log.innerHTML += `<div><strong>Bot:</strong> Sorry, something went wrong.</div>`;
        });
    }
  
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
          cookie = cookie.trim();
          if (cookie.startsWith(name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  });
  