#!/usr/bin/env python3
"""
GHOSTGRAB - YouTube link -> MP3 / MP4, hacker-terminal edition.

Setup:   pip install yt-dlp        (and install ffmpeg: needed for MP3 + merging MP4)
Run:     python ghostgrab.py       then open http://127.0.0.1:8777
No API keys needed: yt-dlp talks to YouTube directly.
Use only for content you own, that is Creative Commons, or that you have permission to download.
"""
import json, os, re, shutil, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

try:
    import yt_dlp
except ImportError:
    raise SystemExit("[!] yt-dlp missing. Run: pip install yt-dlp")

PORT = int(os.environ.get("PORT", 8777))
HOST = os.environ.get("HOST", "127.0.0.1")
ORIGIN = os.environ.get("ALLOW_ORIGIN", "*")  # set to your netlify URL to lock it down
YT = re.compile(r"^(www\.|m\.|music\.)?(youtube\.com|youtu\.be)$")

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GHOSTGRAB</title>
<style>
:root{--g:#00ff41;--d:#008f23;--r:#ff2e4d;--bg:#020a04;--c:#00e5ff}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--g);font:15px/1.5 "Courier New",ui-monospace,monospace;overflow-x:hidden}
#rain{position:fixed;inset:0;z-index:0;opacity:.35}
body:after{content:"";position:fixed;inset:0;z-index:3;pointer-events:none;
background:repeating-linear-gradient(0deg,rgba(0,0,0,.28) 0 1px,transparent 1px 3px);
box-shadow:inset 0 0 160px rgba(0,0,0,.9)}
main{position:relative;z-index:2;max-width:760px;margin:0 auto;padding:28px 16px 60px}
pre.logo{margin:0 0 6px;font-size:clamp(5px,1.55vw,11px);line-height:1.05;color:var(--g);
text-shadow:0 0 8px var(--g),0 0 22px var(--d);animation:flick 4s infinite}
@keyframes flick{0%,92%,100%{opacity:1}93%{opacity:.6;transform:translateX(2px)}95%{opacity:.9;transform:translateX(-2px)}}
.sub{color:var(--d);margin-bottom:18px}
.win{border:1px solid var(--g);background:rgba(0,12,3,.88);box-shadow:0 0 18px rgba(0,255,65,.25),inset 0 0 20px rgba(0,255,65,.06);margin-bottom:16px}
.bar{background:var(--g);color:#001a07;padding:2px 10px;font-weight:bold;display:flex;justify-content:space-between}
.body{padding:14px}
label{color:var(--c);display:block;margin-bottom:6px}
.row{display:flex;gap:8px;align-items:center}
.row span{color:var(--g)}
input{flex:1;background:transparent;border:0;border-bottom:1px dashed var(--g);color:var(--g);font:inherit;padding:6px 2px;outline:none;caret-color:var(--g);min-width:0}
input::placeholder{color:var(--d)}input:focus{border-bottom-style:solid;text-shadow:0 0 6px var(--g)}
button{font:inherit;cursor:pointer;background:transparent;color:var(--g);border:1px solid var(--g);padding:9px 14px;transition:.12s}
button:hover:not(:disabled),button:focus-visible{background:var(--g);color:#001a07;box-shadow:0 0 16px var(--g);outline:none}
button:disabled{opacity:.35;cursor:not-allowed}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px}
button.alt{border-color:var(--c);color:var(--c)}
button.alt:hover:not(:disabled),button.alt:focus-visible{background:var(--c);color:#001a07;box-shadow:0 0 16px var(--c)}
#target{display:none;gap:12px;margin-top:14px}#target.on{display:flex}
#target img{width:128px;height:72px;object-fit:cover;border:1px solid var(--g);filter:grayscale(1) contrast(1.2) sepia(1) hue-rotate(60deg) saturate(3)}
#target b{color:#fff}#target small{color:var(--d);display:block}
#log{height:210px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;font-size:13px}
#log .e{color:var(--r)}#log .o{color:var(--c)}#log .m{color:var(--d)}
.cur:after{content:"█";animation:b 1s steps(1) infinite}@keyframes b{50%{opacity:0}}
.glitch{animation:gl .25s 2}@keyframes gl{25%{transform:translate(3px,-2px);color:var(--r)}75%{transform:translate(-3px,2px);color:var(--c)}}
.foot{color:var(--d);font-size:12px;text-align:center}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style></head><body>
<canvas id="rain"></canvas>
<main>
<pre class="logo">  ▄████  ██░ ██  ▒█████    ██████ ▄▄▄█████▓
 ██▒ ▀█▒▓██░ ██▒▒██▒  ██▒▒██    ▒ ▓  ██▒ ▓▒
▒██░▄▄▄░▒██▀▀██░▒██░  ██▒░ ▓██▄   ▒ ▓██░ ▒░
░▓█  ██▓░▓█ ░██ ▒██   ██░  ▒   ██▒░ ▓██▓ ░
░▒▓███▀▒░▓█▒░██▓░ ████▓▒░▒██████▒▒  ▒██▒ ░
 ░▒   ▒  ▒ ░░▒░▒░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░  ▒ ░░   GRAB</pre>
<div class="sub">root@ghostgrab:~# yt → mp3 / mp4 extraction rig <span class="cur"></span></div>

<div class="win"><div class="bar"><span>[ TARGET ACQUISITION ]</span><span>:: LOCALHOST ::</span></div>
<div class="body">
<label for="url">&gt; feed me a youtube link</label>
<div class="row"><span>$</span><input id="url" placeholder="https://youtube.com/watch?v=..." autocomplete="off" spellcheck="false"></div>
<div class="btns"><button id="scan">SCAN TARGET</button><button id="clr" class="alt">WIPE TRACES</button></div>
<div id="target"><img id="th" alt=""><div><b id="tt"></b><small id="td"></small></div></div>
<div class="btns"><button id="mp3" class="alt" disabled>EXTRACT AUDIO .MP3</button><button id="mp4" disabled>EXTRACT VIDEO .MP4</button></div>
</div></div>

<div class="win"><div class="bar"><span>[ SYSTEM LOG ]</span><span id="st">IDLE</span></div>
<div class="body"><div id="log"></div></div></div>
<div class="foot">only grab what you own, or have permission to download</div>
</main>
<script>
const $=id=>document.getElementById(id),log=$('log');
function w(t,c=''){const d=document.createElement('div');if(c)d.className=c;d.textContent=t;log.appendChild(d);log.scrollTop=log.scrollHeight}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{for(const l of ['[boot] ghostgrab kernel 1.337 online','[boot] mounting yt-dlp engine ...... OK','[boot] ffmpeg link ...... checking','[boot] no api keys required. zero trace. awaiting target.']){w(l,'m');await sleep(260)}})();

// matrix rain
const cv=$('rain'),cx=cv.getContext('2d');let cols,drops;
function rs(){cv.width=innerWidth;cv.height=innerHeight;cols=Math.floor(cv.width/16);drops=Array(cols).fill(1)}
rs();addEventListener('resize',rs);
const ch='アイウエオカキクケコサシスセソ0123456789ABCDEF<>/\\{}$#';
setInterval(()=>{cx.fillStyle='rgba(2,10,4,.08)';cx.fillRect(0,0,cv.width,cv.height);cx.fillStyle='#00ff41';cx.font='15px monospace';
drops.forEach((y,i)=>{cx.fillText(ch[Math.random()*ch.length|0],i*16,y*16);if(y*16>cv.height&&Math.random()>.975)drops[i]=0;drops[i]++})},55);

let ok=false;
function busy(b,s){['scan','mp3','mp4'].forEach(i=>$(i).disabled=b||(i!=='scan'&&!ok));$('st').textContent=s}
async function scan(){
  const url=$('url').value.trim();if(!url)return w('[err] no target supplied','e');
  busy(true,'SCANNING');w('[>] probing '+url,'o');ok=false;$('target').classList.remove('on');
  try{
    const r=await fetch('/api/info',{method:'POST',body:JSON.stringify({url})});const j=await r.json();
    if(!r.ok)throw new Error(j.error);
    $('th').src=j.thumb||'';$('tt').textContent=j.title;$('td').textContent=j.channel+' | '+j.duration;
    $('target').classList.add('on');ok=true;w('[+] target locked: '+j.title,'o');busy(false,'LOCKED');
  }catch(e){w('[err] '+e.message,'e');document.querySelector('.logo').classList.add('glitch');setTimeout(()=>document.querySelector('.logo').classList.remove('glitch'),600);busy(false,'FAIL')}
}
async function grab(fmt){
  const url=$('url').value.trim();busy(true,'EXTRACTING');
  w('[>] extracting '+fmt.toUpperCase()+' ... large files take a while, hold tight','o');
  try{
    const r=await fetch('/api/download?fmt='+fmt+'&url='+encodeURIComponent(url));
    if(!r.ok)throw new Error((await r.json()).error);
    const b=await r.blob();const n=decodeURIComponent((r.headers.get('X-Filename')||'ghostgrab.'+fmt));
    const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=n;a.click();
    w('[+] payload delivered: '+n+' ('+(b.size/1048576).toFixed(1)+' MB)','o');busy(false,'DONE');
  }catch(e){w('[err] '+e.message,'e');busy(false,'FAIL')}
}
$('scan').onclick=scan;$('mp3').onclick=()=>grab('mp3');$('mp4').onclick=()=>grab('mp4');
$('url').addEventListener('keydown',e=>{if(e.key==='Enter')scan()});
$('url').addEventListener('input',()=>{ok=false;$('mp3').disabled=$('mp4').disabled=true});
$('clr').onclick=()=>{log.innerHTML='';$('url').value='';ok=false;$('target').classList.remove('on');busy(false,'IDLE');w('[sys] traces wiped','m')};
</script></body></html>"""


def valid(url):
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(YT.match(p.hostname or ""))
    except Exception:
        return False


def fmt_dur(s):
    if not s:
        return "live/unknown"
    s = int(s)
    h, m = divmod(s, 3600)
    m, sec = divmod(m, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


class H(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Expose-Headers", "X-Filename")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            b = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/api/download":
            q = parse_qs(u.query)
            url = (q.get("url") or [""])[0]
            fmt = (q.get("fmt") or ["mp4"])[0]
            if not valid(url) or fmt not in ("mp3", "mp4"):
                return self._json(400, {"error": "invalid youtube link or format"})
            if not shutil.which("ffmpeg"):
                return self._json(500, {"error": "ffmpeg not found in PATH. install it first"})
            tmp = tempfile.mkdtemp(prefix="ghostgrab_")
            try:
                opts = {"outtmpl": os.path.join(tmp, "%(title).120B.%(ext)s"),
                        "noplaylist": True, "quiet": True, "no_warnings": True}
                if fmt == "mp3":
                    opts.update(format="bestaudio/best", postprocessors=[
                        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}])
                else:
                    opts.update(format="bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                                merge_output_format="mp4")
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                files = [f for f in os.listdir(tmp) if f.endswith("." + fmt)]
                if not files:
                    raise RuntimeError("no output produced")
                path = os.path.join(tmp, files[0])
                size = os.path.getsize(path)
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg" if fmt == "mp3" else "video/mp4")
                self.send_header("Content-Length", str(size))
                self.send_header("X-Filename", quote(files[0]))
                self.end_headers()
                with open(path, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            except Exception as e:
                try:
                    self._json(500, {"error": str(e).replace("ERROR: ", "")[:300]})
                except Exception:
                    pass
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/info":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            url = json.loads(self.rfile.read(n)).get("url", "")
        except Exception:
            return self._json(400, {"error": "bad request"})
        if not valid(url):
            return self._json(400, {"error": "that is not a youtube link"})
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True, "skip_download": True}) as ydl:
                i = ydl.extract_info(url, download=False)
            self._json(200, {"title": i.get("title", "?"), "channel": i.get("uploader", "?"),
                             "duration": fmt_dur(i.get("duration")), "thumb": i.get("thumbnail", "")})
        except Exception as e:
            self._json(502, {"error": str(e).replace("ERROR: ", "")[:300]})


if __name__ == "__main__":
    print(f"[+] GHOSTGRAB online -> http://{HOST}:{PORT}")
    if not shutil.which("ffmpeg"):
        print("[!] ffmpeg not found: MP3/MP4 extraction will fail until you install it")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
