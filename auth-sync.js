"use strict";
/* Optional account and manual upload. Never modifies/deletes local IndexedDB data. */
(()=>{
  const section=document.getElementById("dados");
  if(!section)return;
  const card=document.createElement("article");
  card.className="card";
  card.innerHTML=`<h3>Conta e sincronização (experimental)</h3>
    <p class="muted">Seu histórico permanece neste dispositivo. A conexão e o envio são opcionais; faça um backup JSON antes de importar.</p>
    <label>Endereço HTTPS da API Python <input id="sync-api" type="url" placeholder="https://sua-api.example.com" autocomplete="url"></label>
    <label>E-mail <input id="sync-email" type="email" autocomplete="email"></label>
    <label>Senha <input id="sync-password" type="password" autocomplete="current-password" minlength="12"></label>
    <div class="actions"><button type="button" id="sync-register">Criar conta</button><button type="button" id="sync-login">Entrar</button><button type="button" id="sync-logout">Sair</button></div>
    <p id="sync-user" role="status"></p>\n    <details><summary>Recuperar senha</summary><p>Enviaremos um código ao e-mail informado acima.</p><button type="button" id="sync-forgot">Solicitar código</button><label>Código recebido por e-mail <input id="sync-reset-code" autocomplete="off"></label><label>Nova senha (mínimo 12 caracteres) <input id="sync-new-password" type="password" minlength="12" autocomplete="new-password"></label><button type="button" id="sync-reset">Redefinir senha</button></details>
    <div class="actions"><button type="button" id="sync-preview">Pré-visualizar envio</button><button type="button" id="sync-send" disabled>Enviar cópia para minha conta</button></div>
    <p id="sync-status" role="status"></p>`;
  section.append(card);
  const el=id=>document.getElementById(id);
  let snapshot=null;
  let accessToken=null; // memory-only; sign in again after page reload
  const say=message=>{el("sync-status").textContent=message};
  function base(){
    const raw=el("sync-api").value.trim().replace(/\/$/,"");
    const url=new URL(raw);
    if(url.protocol!=="https:" && !(url.protocol==="http:" && ["localhost","127.0.0.1"].includes(url.hostname)))
      throw Error("Informe uma API HTTPS (HTTP apenas no localhost).");
    return url.origin+url.pathname.replace(/\/$/,"");
  }
  async function api(path,method="GET",body){
    const response=await fetch(base()+path,{method,credentials:"omit",headers:{...(body===undefined?{}:{"Content-Type":"application/json"}),...(accessToken?{"Authorization":"Bearer "+accessToken}:{})},body:body===undefined?undefined:JSON.stringify(body)});
    const data=await response.json().catch(()=>({}));
    if(!response.ok){const e=new Error(data.error||"Falha na requisição ("+response.status+")");e.status=response.status;throw e}
    return data;
  }
  async function account(path){
    try{
      const data=await api(path,"POST",{email:el("sync-email").value,password:el("sync-password").value});
      accessToken=data.access_token;
      el("sync-password").value="";
      el("sync-user").textContent="Conectado: "+data.email;
      say("Conta conectada. Os dados locais ainda não foram enviados.");
    }catch(e){say(e.message)}
  }
  el("sync-forgot").onclick=async()=>{
    try{const r=await api("/api/auth/forgot-password","POST",{email:el("sync-email").value});say(r.message)}
    catch(e){say(e.message)}
  };
  el("sync-reset").onclick=async()=>{
    try{await api("/api/auth/reset-password","POST",{token:el("sync-reset-code").value.trim(),password:el("sync-new-password").value});accessToken=null;el("sync-reset-code").value="";el("sync-new-password").value="";say("Senha alterada. Entre novamente.");}
    catch(e){say(e.message)}
  };
  el("sync-register").onclick=()=>account("/api/auth/register");
  el("sync-login").onclick=()=>account("/api/auth/login");
  el("sync-logout").onclick=async()=>{
    try{if(accessToken)await api("/api/auth/logout","POST",{});el("sync-user").textContent="Desconectado";say("Seus dados locais foram preservados.")}
    catch(e){say(e.message)}
    finally{accessToken=null}
    snapshot=null;el("sync-send").disabled=true;
  };
  async function localSnapshot(){
    return new Promise((resolve,reject)=>{
      const open=indexedDB.open("minha-agenda-v2");
      open.onerror=()=>reject(open.error);
      open.onsuccess=()=>{
        const db=open.result;
        if(!db.objectStoreNames.contains("records")||!db.objectStoreNames.contains("settings")){db.close();reject(Error("Banco local incompleto."));return}
        const tx=db.transaction(["records","settings"],"readonly");
        const result={records:[],settings:[]};
        for(const name of ["records","settings"]){
          const req=tx.objectStore(name).getAll();
          req.onsuccess=()=>{result[name]=req.result};
          req.onerror=()=>reject(req.error);
        }
        tx.oncomplete=()=>{db.close();resolve(result)};
        tx.onerror=()=>{db.close();reject(tx.error)};
      };
    });
  }
  el("sync-preview").onclick=async()=>{
    snapshot=null;el("sync-send").disabled=true;
    try{
      await api("/api/auth/me");
      const data=await localSnapshot();
      const invalid=data.records.some(r=>typeof r.id!=="string")||data.settings.some(s=>typeof s.key!=="string");
      if(invalid)throw Error("Alguns itens não possuem identificadores válidos. Nenhum dado foi enviado.");
      snapshot=data;
      say(`Prévia: ${data.records.length} registros e ${data.settings.length} configurações locais. Nada foi enviado. Exporte seu backup JSON antes de confirmar.`);
      el("sync-send").disabled=!(data.records.length+data.settings.length);
    }catch(e){say(e.message)}
  };
  el("sync-send").onclick=async()=>{
    if(!snapshot)return;
    const total=snapshot.records.length+snapshot.settings.length;
    if(!accessToken){say("Entre novamente antes de enviar.");return}
    if(!window.confirm(`Enviar uma cópia de ${total} itens à conta conectada? Dados locais serão preservados. Itens remotos existentes NÃO serão sobrescritos.`))return;
    el("sync-send").disabled=true;
    let sent=0,existing=0,failed=0;
    try{
      for(const collection of ["records","settings"]){
        const remote=await api("/api/sync/"+collection);
        const ids=new Set(remote.items.map(item=>item.id));
        for(const item of snapshot[collection]){
          const id=collection==="records"?item.id:item.key;
          if(ids.has(id)){existing++;continue}
          try{await api("/api/sync/"+collection+"/"+encodeURIComponent(id),"PUT",{base_revision:0,data:item});sent++}
          catch(e){if(e.status===409)existing++;else failed++}
        }
      }
      say(`Envio finalizado: ${sent} novos itens, ${existing} já existentes/conflitantes, ${failed} falhas. Nenhum dado local foi removido. Faça nova prévia para reenviar.`);
    }catch(e){say(`Envio interrompido: ${e.message}. ${sent} itens enviados até agora; dados locais preservados.`)}
    finally{snapshot=null}
  };
})();
