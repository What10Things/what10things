(()=>{
'use strict';
const root=document.documentElement;
const chapters=[...document.querySelectorAll('.chapter')];
const canvas=document.getElementById('scene');
const caption=document.getElementById('sceneCaption');
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const saveData=Boolean(navigator.connection&&navigator.connection.saveData);
const labels=['ten points · one clear answer','topic territories · one connected map','ten distinct points · no padding','evidence lines · relationships exposed','one fact · another route opens','a clear route forward'];
let pointer={x:0,y:0},targetPointer={x:0,y:0};

function scrollProgress(){
  const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);
  return Math.min(1,Math.max(0,scrollY/max));
}
function stateProgress(){
  const y=scrollY+innerHeight*.5;
  let i=0;
  for(let n=0;n<chapters.length;n++) if(y>=chapters[n].offsetTop) i=n;
  const next=Math.min(chapters.length-1,i+1);
  const a=chapters[i].offsetTop;
  const b=next===i?a+innerHeight:chapters[next].offsetTop;
  const t=next===i?0:Math.min(1,Math.max(0,(y-a)/Math.max(1,b-a)));
  return {i,next,t};
}
function updateUi(){
  const p=scrollProgress(); root.style.setProperty('--p',p.toFixed(4));
  const s=stateProgress(); if(caption) caption.textContent=labels[Math.min(labels.length-1,s.t>.55?s.next:s.i)];
}
addEventListener('scroll',updateUi,{passive:true}); updateUi();

if(reduced||saveData||!canvas||!canvas.getContext){document.body.classList.add('static-scene');return;}
const gl=canvas.getContext('webgl',{alpha:true,antialias:false,powerPreference:'low-power',premultipliedAlpha:true});
if(!gl){document.body.classList.add('static-scene');const fb=document.querySelector('.scene-fallback');if(fb)fb.style.display='block';return;}

const vs=`
attribute vec3 aPos;
attribute vec4 aColor;
uniform float uYaw;
uniform float uPitch;
uniform vec2 uPan;
uniform float uZoom;
uniform float uPoint;
varying vec4 vColor;
void main(){
  float cy=cos(uYaw), sy=sin(uYaw), cp=cos(uPitch), sp=sin(uPitch);
  vec3 p=aPos;
  p=vec3(cy*p.x+sy*p.z,p.y,-sy*p.x+cy*p.z);
  p=vec3(p.x,cp*p.y-sp*p.z,sp*p.y+cp*p.z);
  float depth=2.8+p.z*.18;
  vec2 xy=(p.xy*uZoom)/depth+uPan;
  gl_Position=vec4(xy,0.0,1.0);
  gl_PointSize=uPoint*(1.05+clamp(p.z*.08,-.25,.35));
  vColor=aColor;
}`;
const fs=`
precision mediump float;
varying vec4 vColor;
uniform float uIsPoint;
void main(){
  if(uIsPoint>.5){
    vec2 d=gl_PointCoord-vec2(.5);
    float r=dot(d,d);
    if(r>.25) discard;
    float core=smoothstep(.25,.05,r);
    gl_FragColor=vec4(vColor.rgb,vColor.a*core);
  }else gl_FragColor=vColor;
}`;
function shader(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s)||'shader');return s}
const prog=gl.createProgram();gl.attachShader(prog,shader(gl.VERTEX_SHADER,vs));gl.attachShader(prog,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(prog);if(!gl.getProgramParameter(prog,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(prog)||'link');gl.useProgram(prog);
const loc={pos:gl.getAttribLocation(prog,'aPos'),color:gl.getAttribLocation(prog,'aColor'),yaw:gl.getUniformLocation(prog,'uYaw'),pitch:gl.getUniformLocation(prog,'uPitch'),pan:gl.getUniformLocation(prog,'uPan'),zoom:gl.getUniformLocation(prog,'uZoom'),point:gl.getUniformLocation(prog,'uPoint'),isPoint:gl.getUniformLocation(prog,'uIsPoint')};
const posBuf=gl.createBuffer(), colorBuf=gl.createBuffer(), linePosBuf=gl.createBuffer(), lineColorBuf=gl.createBuffer();

const C=[[.73,1,.25,1],[1,.44,.28,1],[.36,.85,1,1],[.69,.55,1,1],[1,.82,.32,1],[1,.49,.64,1],[.73,1,.25,1],[1,.44,.28,1],[.36,.85,1,1],[.69,.55,1,1]];
const states=[
 [[0,1.9,.2],[1.45,1.15,.6],[2.2,0,.1],[1.45,-1.2,.5],[0,-1.9,-.2],[-1.45,-1.2,.3],[-2.2,0,-.3],[-1.45,1.15,.4],[0,.7,1.1],[0,-.65,1.0]],
 [[-2.6,1.25,.2],[-1.8,.75,.6],[-.65,1.35,.1],[.2,.7,.5],[1.65,1.15,.4],[2.55,.5,.1],[-2.3,-1.1,.3],[-.7,-1.2,.7],[.7,-1.05,.15],[2.25,-1.1,.55]],
 [[-1.7,1.7,.1],[-.8,1.3,.55],[.15,.95,.05],[.95,.48,.5],[1.6,-.05,.1],[1.25,-.75,.55],[.45,-1.2,.05],[-.45,-1.45,.5],[-1.35,-1.05,.05],[-1.75,-.35,.45]],
 [[-2.8,1.35,.15],[-2.1,.85,.55],[-1.4,.3,.05],[-.7,-.2,.5],[0,.55,.1],[.7,-.1,.55],[1.4,.7,.05],[2.1,.05,.5],[2.8,.85,.08],[2.35,-1.1,.5]],
 [[0,1.7,.8],[-1.45,.85,.3],[1.45,.85,.35],[-2.35,-.1,.7],[-.8,-.2,.1],[.8,-.2,.5],[2.35,-.1,.05],[-1.55,-1.25,.55],[0,-1.45,.1],[1.55,-1.25,.65]],
 [[-3.15,-.15,.2],[-2.45,-.1,.45],[-1.75,-.06,.05],[-1.05,-.02,.55],[-.35,0,.1],[.35,.02,.45],[1.05,.05,.05],[1.75,.08,.55],[2.45,.11,.1],[3.15,.15,.5]]
 ];
const cameras=[
 {zoom:1.04,pan:[.30,.02],yaw:-.18,pitch:.08},
 {zoom:.88,pan:[.28,.02],yaw:.14,pitch:-.03},
 {zoom:1.03,pan:[.33,.00],yaw:-.26,pitch:.12},
 {zoom:.92,pan:[.22,.02],yaw:.08,pitch:-.12},
 {zoom:.92,pan:[.30,.03],yaw:-.14,pitch:.08},
 {zoom:.92,pan:[.18,.05],yaw:.03,pitch:0}
];
const connections=[0,8,8,1,1,2,2,3,3,9,9,4,4,5,5,6,6,7,7,0,8,9,0,2,2,4,4,6,6,0];
const evidenceConnections=[0,4,1,5,2,6,3,7,4,8,5,9,0,3,3,6,6,9];

let mobile=innerWidth<760,pointSize=mobile?9.2:8.4,dpr=1;
const mainPos=new Float32Array(10*3),mainColors=new Float32Array(10*4);
for(let i=0;i<10;i++)mainColors.set(C[i],i*4);
const lineColors=[];
function lerp(a,b,t){return a+(b-a)*t}
function smooth(t){return t*t*(3-2*t)}
function rebuildLines(stateIdx){
 const pairs=stateIdx===3?evidenceConnections:connections;
 const arr=[];lineColors.length=0;
 for(let i=0;i<pairs.length;i+=2){const a=pairs[i],b=pairs[i+1];arr.push(mainPos[a*3],mainPos[a*3+1],mainPos[a*3+2],mainPos[b*3],mainPos[b*3+1],mainPos[b*3+2]);const alpha=stateIdx===3?.32:.16;lineColors.push(.82,.82,.78,alpha,.82,.82,.78,alpha)}
 gl.bindBuffer(gl.ARRAY_BUFFER,linePosBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(arr),gl.DYNAMIC_DRAW);
 gl.bindBuffer(gl.ARRAY_BUFFER,lineColorBuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(lineColors),gl.DYNAMIC_DRAW);
 return pairs.length;
}
function resize(){
 mobile=innerWidth<760; const cap=mobile?1.25:1.5; dpr=Math.min(devicePixelRatio||1,cap);
 const w=Math.max(1,Math.floor(canvas.clientWidth*dpr)),h=Math.max(1,Math.floor(canvas.clientHeight*dpr));
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h)} pointSize=(mobile?9.5:8.6)*dpr;
}
addEventListener('resize',resize,{passive:true});resize();
function attach(buffer,loc,size){gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,size,gl.FLOAT,false,0,0)}

let last=0,hidden=document.hidden;
document.addEventListener('visibilitychange',()=>{hidden=document.hidden;if(!hidden)requestAnimationFrame(render)});
addEventListener('pointermove',e=>{targetPointer.x=(e.clientX/innerWidth-.5)*2;targetPointer.y=(e.clientY/innerHeight-.5)*2},{passive:true});
addEventListener('touchmove',e=>{if(!e.touches[0])return;targetPointer.x=(e.touches[0].clientX/innerWidth-.5)*2;targetPointer.y=(e.touches[0].clientY/innerHeight-.5)*2},{passive:true});

function render(ts){
 if(hidden)return;
 if(mobile&&ts-last<22){requestAnimationFrame(render);return} last=ts;
 resize(); updateUi();
 const s=stateProgress(),t=smooth(s.t),A=states[s.i],B=states[s.next],ca=cameras[s.i],cb=cameras[s.next];
 for(let i=0;i<10;i++){mainPos[i*3]=lerp(A[i][0],B[i][0],t);mainPos[i*3+1]=lerp(A[i][1],B[i][1],t);mainPos[i*3+2]=lerp(A[i][2],B[i][2],t)}
 pointer.x=lerp(pointer.x,targetPointer.x,.045);pointer.y=lerp(pointer.y,targetPointer.y,.045);
 const portrait=innerWidth<760;
 const portraitScale=portrait?.72:1;
 for(let i=0;i<10;i++){mainPos[i*3]*=portraitScale;mainPos[i*3+1]*=portrait?.88:1}
 gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 gl.useProgram(prog);
 const yaw=lerp(ca.yaw,cb.yaw,t)+pointer.x*.035,pitch=lerp(ca.pitch,cb.pitch,t)-pointer.y*.02;
 const panX=(portrait?0:.0)+lerp(ca.pan[0],cb.pan[0],t), panY=(portrait?.15:0)+lerp(ca.pan[1],cb.pan[1],t);
 gl.uniform1f(loc.yaw,yaw);gl.uniform1f(loc.pitch,pitch);gl.uniform2f(loc.pan,panX,panY);gl.uniform1f(loc.zoom,lerp(ca.zoom,cb.zoom,t)*(portrait?1.1:1));
 gl.bindBuffer(gl.ARRAY_BUFFER,posBuf);gl.bufferData(gl.ARRAY_BUFFER,mainPos,gl.DYNAMIC_DRAW);attach(posBuf,loc.pos,3);
 gl.bindBuffer(gl.ARRAY_BUFFER,colorBuf);gl.bufferData(gl.ARRAY_BUFFER,mainColors,gl.STATIC_DRAW);attach(colorBuf,loc.color,4);
 gl.uniform1f(loc.point,pointSize);gl.uniform1f(loc.isPoint,1);gl.drawArrays(gl.POINTS,0,10);
 const lineVerts=rebuildLines(s.t>.5?s.next:s.i);attach(linePosBuf,loc.pos,3);attach(lineColorBuf,loc.color,4);gl.uniform1f(loc.isPoint,0);gl.drawArrays(gl.LINES,0,lineVerts);
 requestAnimationFrame(render);
}
requestAnimationFrame(render);
})();