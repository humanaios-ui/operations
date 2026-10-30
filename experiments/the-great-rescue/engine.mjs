/** The Great Rescue S0 - deterministic, server-run 2D projectile + contact model.
 * Visual units are game units. No browser authority or generative AI. */
export const GRID = Object.freeze({cols:13,rows:5,firstX:260,dx:40,firstY:270,dy:30});
export const PARTS = Object.freeze({beam:{cost:1,length:120},ramp:{cost:2,length:120},spring:{cost:2,length:75},lever:{cost:2,length:75}});
export const START_INVENTORY = Object.freeze({beam:4,ramp:2,spring:1,lever:1});
export const MAX_BUDGET = 12;
export const MAX_FRAMES = 215;
export const position = (c,r) => ({x:GRID.firstX+c*GRID.dx,y:GRID.firstY+r*GRID.dy});
export function validPlacement(type,c,r,angle=0){
 return Object.hasOwn(PARTS,type)&&Number.isInteger(c)&&c>=0&&c<GRID.cols&&Number.isInteger(r)&&r>=0&&r<GRID.rows&&Number.isInteger(angle)&&[-1,0,1].includes(angle)&&(type==='ramp'?angle!==0:angle===0);
}
function surface(part,x){
 const {x:cx,y:cy}=position(part.c,part.r),len=PARTS[part.type].length;
 if(Math.abs(x-cx)>len/2)return null;
 const slope=part.type==='ramp'?part.angle*0.28:0;
 return {y:cy+slope*(x-cx),slope};
}
/** A capsule flies from the western ledge toward the eastern extraction dock.
 * Obstacles, gaps, gravity and component contacts are deterministic. Each collision is visible in the event log.
 * Test variants perturb launch speed slightly to measure actual robustness. */
export function simulate(parts=[],variant=0){
 if(!Array.isArray(parts)||parts.length>12)throw Error('Invalid construction');
 const list=parts.map(p=>{if(!validPlacement(p.type,p.c,p.r,p.angle||0))throw Error('Invalid part position');return {...p};});
 let x=82,y=314,vx=7.15*(1+variant),vy=-4.8;
 const radius=10, gravity=0.28, touched=new Set(),frames=[],events=[];
 let outcome='TIMEOUT',steps=0;
 for(let t=0;t<MAX_FRAMES;t++){
  steps=t+1;
  const ox=x,oy=y;
  vy+=gravity;
  x+=vx;y+=vy;
  // The left ledge and the far-side landing are solid. The middle is a deep gap.
  const onGround=x<252||x>763;
  if(onGround&&y+radius>=410&&oy+radius<=410&&vy>=0){y=410-radius;vy=0;vx*=0.997;}
  // A capsule traverses a machine only via real contact, not a scored proximity shortcut.
  const collisionList=[];
  for(let j=0;j<list.length;j++){
   const p=list[j],now=surface(p,x),prev=surface(p,ox);
   if(!now)continue;
   if(vy<0)continue;
   const prevY=prev?.y??now.y;
   if(oy+radius<=prevY+7&&y+radius>=now.y-1){
    collisionList.push({part:p,idx:j,y:now.y,slope:now.slope});
   }
  }
  if(collisionList.length){
   collisionList.sort((a,b)=>a.y-b.y);
   const hit=collisionList[0];
   y=hit.y-radius;
   if(hit.part.type==='spring'&&!touched.has(hit.idx)){
    vy=-8.4;vx+=2.1;touched.add(hit.idx);events.push({frame:t,description:'Spring launches the capsule forward.'});
   }else if(hit.part.type==='lever'&&!touched.has(hit.idx)){
    vy=-5.8;vx+=3.1;touched.add(hit.idx);events.push({frame:t,description:'Lever transfers momentum to the capsule.'});
   }else if(hit.part.type==='ramp'){vy=Math.min(0,hit.slope*vx-1.1);vx*=0.997;}
   else{vy=0;vx*=0.997;}
  }
  frames.push({x:Math.round(x*10)/10,y:Math.round(y*10)/10});
  if(x>=895&&x<=975&&y>=355&&y<=410){outcome='DELIVERED';events.push({frame:t,description:'Capsule reached the extraction dock.'});break;}
  if(x>1020||y>515||x<-20){outcome='LOST';events.push({frame:t,description:'Capsule left the safe course.'});break;}
  if(vx<0.05){outcome='STALLED';break;}
 }
 return {outcome,success:outcome==='DELIVERED',steps,frames,events};
}
export function evaluate(parts){
 const used=parts.reduce((n,p)=>n+PARTS[p.type].cost,0);
 if(used>MAX_BUDGET)throw Error('Build exceeds material budget');
 const center=simulate(parts,0),runs=[simulate(parts,-0.016),center,simulate(parts,0.016)];
 const consistency=runs.filter(r=>r.success).length;
 const score=center.success?{
  completion:40,
  speed:Math.max(0,Math.round(20*(1-center.steps/MAX_FRAMES))),
  efficiency:Math.max(0,Math.round(20*(1-used/MAX_BUDGET))),
  reliability:Math.round(20*consistency/3)
 }:{completion:0,speed:0,efficiency:0,reliability:0};
 return {center,consistency,used,score,total:Object.values(score).reduce((a,b)=>a+b,0)};
}
