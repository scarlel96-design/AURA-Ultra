// Synthetic authorization oracle; NOT production code.
// Run: node oracle.js. No external dependencies.
function runOracle() {
  const MAX=3; // reduced saturation boundary, not a production value
  const make=(session,mut="")=>{
    const scopes=new Map(), visible=new Map();
    function state(scope){if(!scopes.has(scope))scopes.set(scope,{status:"UNKNOWN",g:0,seq:0,locked:false});return scopes.get(scope)}
    function clear(scope){for(const [k,v] of visible)if(v.scope===scope)visible.delete(k)}
    function bump(s,scope){clear(scope);if(s.g===MAX){s.locked=true;s.status="UNKNOWN";return false} s.g++;return true}
    function control(scope,seq,status,verified=true){
      const s=state(scope);
      if(!verified||!Number.isSafeInteger(seq)||seq<=0||!["GRANTED","DENIED","UNKNOWN"].includes(status)){
        if(s.status!=="UNKNOWN"){bump(s,scope);s.status="UNKNOWN"}return false
      }
      if(seq<s.seq)return false;
      if(seq===s.seq){if(status!==s.status){if(s.status!=="UNKNOWN")bump(s,scope);s.status="UNKNOWN"}return false}
      s.seq=seq;if(s.locked)return false;
      if(s.status!==status){if(!bump(s,scope))return false;s.status=status}
      return true
    }
    function acquire(scope){const s=state(scope);return s.status==="GRANTED"&&!s.locked?Object.freeze({scope,session,g:s.g}):null}
    function permitted(scope,t){const s=state(scope);return !!t&&t.scope===scope&&(mut==="ignore-session"||t.session===session)&&(mut==="ignore-generation"||t.g===s.g)&&(mut==="ignore-authority"||s.status==="GRANTED")&&!s.locked}
    function offer(scope,stream,t,value,opts={}){
      if(!permitted(scope,t)||opts.valid===false)return null;
      return Object.freeze({scope,stream,t,value,revision:opts.revision??1,observedAt:opts.observedAt??null,kind:opts.kind??"OBSERVED"})
    }
    function publish(msg){
      if(!msg||(!permitted(msg.scope,msg.t)&&mut!=="skip-final-check"))return false;
      if(msg.kind==="FORECAST")return false;
      visible.set(msg.scope+"/"+msg.stream,msg);return true
    }
    function withdraw(scope,stream,status,t){
      if(!permitted(scope,t)||!["ERROR","UNAVAILABLE"].includes(status))return false;
      visible.delete(scope+"/"+stream);
      if(mut==="error-revokes")control(scope,state(scope).seq+1,"DENIED");
      return true
    }
    function read(scope,stream){const v=visible.get(scope+"/"+stream);return v&&permitted(scope,v.t)?v.value:null}
    return {control,acquire,offer,publish,withdraw,read,state:scope=>({...state(scope)})}
  };
  const tests=[
    ["RV-01",m=>{let a=m("s");a.control("health",1,"GRANTED");let t=a.acquire("health");a.publish(a.offer("health","pulse",t,80));a.control("health",2,"DENIED");return a.read("health","pulse")===null&&!a.publish(a.offer("health","pulse",t,33,{revision:99,observedAt:12}))}],
    ["RV-02",m=>{let a=m("s");a.control("h",1,"GRANTED");a.control("h",2,"DENIED");a.control("h",3,"GRANTED");return a.publish(a.offer("h","p",a.acquire("h"),45))&&a.read("h","p")===45}],
    ["RV-03",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h");a.control("h",2,"DENIED");a.control("h",3,"GRANTED");return !a.publish(a.offer("h","p",t,33,{revision:99}))}],
    ["RV-04",m=>{let a=m("s");a.control("h",1,"GRANTED");a.control("h",2,"DENIED");a.control("h",1,"GRANTED");a.control("h",2,"GRANTED");return a.acquire("h")===null&&a.state("h").status==="UNKNOWN"}],
    ["RV-05",m=>{let a=m("s");return a.offer("h","p",null,5,{observedAt:999999,revision:99})===null&&a.acquire("h")===null}],
    ["RV-06",m=>{let a=m("s");a.control("shared",1,"GRANTED");a.control("other",1,"GRANTED");let x=a.acquire("shared"),y=a.acquire("other");a.control("shared",2,"DENIED");return !a.publish(a.offer("shared","providerB",x,2))&&a.publish(a.offer("other","providerB",y,3))&&!a.publish(a.offer("other","providerB",x,4))}],
    ["RV-07",m=>{let a=m("old");a.control("h",1,"GRANTED");let t=a.acquire("h");let b=m("new");if(b.acquire("h")!==null)return false;b.control("h",1,"GRANTED");return !b.publish(b.offer("h","p",t,33))}],
    ["RV-08",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h");a.publish(a.offer("h","p",t,7));if(!a.withdraw("h","p","ERROR",t)||a.read("h","p")!==null||a.state("h").status!=="GRANTED")return false;a.publish(a.offer("h","p",t,9));if(!a.withdraw("h","p","UNAVAILABLE",t)||a.read("h","p")!==null)return false;a.control("h",2,"DENIED");return a.state("h").status==="DENIED"&&a.acquire("h")===null}],
    ["RV-09",m=>{let a=m("s");a.control("h",1,"GRANTED");a.control("h",2,"DENIED");a.control("h",3,"GRANTED");let t=a.acquire("h");a.control("h",4,"DENIED");a.control("h",5,"GRANTED");return a.state("h").locked&&a.state("h").g===MAX&&a.acquire("h")===null&&!a.publish(a.offer("h","p",t,1,{revision:999}))}],
    ["RV-10",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h");let q=a.offer("h","p",t,1);a.control("h",2,"DENIED",true);return !a.publish(q)&&a.read("h","p")===null}],
    ["RV-11",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h"),q=a.offer("h","p",t,1);a.publish(q);a.control("h",2,"DENIED");return a.read("h","p")===null&&!a.publish(q)}],
    ["RV-12",m=>{let a=m("s");a.control("h",1,"GRANTED");let old=a.acquire("h");a.control("h",2,"DENIED");a.control("h",3,"GRANTED");let q=a.offer("h","p",a.acquire("h"),33,{observedAt:10});return q.observedAt===10&&a.publish(q)&&!a.publish(a.offer("h","p",old,33,{observedAt:10}))}],
    ["RV-13",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h");return a.publish(a.offer("h","p",t,0))&&a.read("h","p")===0&&a.publish(a.offer("h","flag",t,false))&&a.read("h","flag")===false&&a.offer("h","bad",t,[],{valid:false})===null&&!a.publish(a.offer("h","p",t,2,{kind:"FORECAST"}))}],
    ["RV-14",m=>{let a=m("s");a.control("h",1,"GRANTED");a.control("independent",1,"GRANTED");a.publish(a.offer("independent","p",a.acquire("independent"),9));a.control("h",2,"DENIED");return a.read("independent","p")===9}],
    ["RV-15",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h");a.control("h",2,"GRANTED",false);return a.acquire("h")===null&&!a.publish(a.offer("h","p",t,3))}],
    ["RV-16",m=>{let a=m("s");a.control("h",1,"GRANTED");let t=a.acquire("h");a.control("h",2,"DENIED");return !a.publish(Object.freeze({scope:"h",stream:"p",t:Object.freeze({scope:"h",session:"s",g:a.state("h").g}),value:9,kind:"OBSERVED"}))}]
  ];
  const normal=tests.map(([id,test])=>({id,pass:test(make)}));
  const mutations=["ignore-session","ignore-generation","ignore-authority","skip-final-check","error-revokes"].map(mut=>({mut,rejectedBy:tests.filter(([id,test])=>!test(s=>make(s,mut))).map(([id])=>id)}));
  return {normal,mutations,pass:normal.every(x=>x.pass)&&mutations.every(x=>x.rejectedBy.length>0)};
}
const result = runOracle(); console.log(JSON.stringify(result, null, 2)); if (!result.pass) process.exitCode = 1;
