function toggleNav(){
  const nav=document.getElementById("mainNav");
  if(nav) nav.classList.toggle("open");
}
function toggleChat(){
  const box=document.getElementById("chatbox");
  if(box) box.style.display=box.style.display==="block"?"none":"block";
}
document.addEventListener("DOMContentLoaded",()=>{
  const form=document.getElementById("chatform");
  const input=document.getElementById("chatinput");
  const log=document.getElementById("chatlog");
  if(!form) return;
  form.addEventListener("submit", async e=>{
    e.preventDefault();
    const message=input.value.trim();
    if(!message) return;
    const csrf=document.querySelector("[name=csrfmiddlewaretoken]").value;
    log.innerHTML += `<div class="user">${escapeHtml(message)}</div>`;
    input.value="";
    const body=new URLSearchParams({message});
    const res=await fetch("/chatbot/",{method:"POST",headers:{"X-CSRFToken":csrf,"X-Requested-With":"XMLHttpRequest"},body});
    const data=await res.json();
    log.innerHTML += `<div class="bot">${escapeHtml(data.reply)}</div>`;
    log.scrollTop=log.scrollHeight;
  });
});
function escapeHtml(s){
  return s.replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
}
