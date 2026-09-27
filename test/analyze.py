import wave, numpy as np, sys
bpm = float(sys.argv[1]) if len(sys.argv) > 1 else 170
w=wave.open("test/live_render.wav"); sr=w.getframerate(); ch=w.getnchannels(); n=w.getnframes()
b=np.frombuffer(w.readframes(n),np.uint8).reshape(-1,3); a=(b[:,0].astype(np.int32)|(b[:,1].astype(np.int32)<<8)|(b[:,2].astype(np.int32)<<16)); a=np.where(a>=1<<23,a-(1<<24),a)/float(1<<23); a=a.reshape(-1,ch)
print("dur %.2f peak %.3f rms %.4f"%(n/sr,np.abs(a).max(),np.sqrt((a**2).mean())))
blk=int(sr*60/bpm/4); env=[np.abs(a[i:i+blk]).max() for i in range(0,len(a)-blk,blk)]
for bar in range(min(8,len(env)//16)): print("bar",bar+1," ".join("%.2f"%e for e in env[bar*16:bar*16+16]))
