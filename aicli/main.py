#!/usr/bin/env python3
"""
aicli — Terminal AI Assistant powered by local Ollama
Usage: python aicli.py [model_name]
"""

import os, sys, json, shutil, subprocess, readline, textwrap
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("[!] Run: pip install requests"); sys.exit(1)

OLLAMA_BASE   = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("AICLI_MODEL", "llama3.2")
WORK_DIR      = Path.cwd()
HISTORY_FILE  = Path.home() / ".aicli_history"

_C = {"reset":"\033[0m","bold":"\033[1m","dim":"\033[2m","cyan":"\033[96m",
      "green":"\033[92m","yellow":"\033[93m","red":"\033[91m","blue":"\033[94m"}
def c(text, *keys): return "".join(_C[k] for k in keys)+str(text)+_C["reset"]

# ── Tools ──────────────────────────────────────────────────────
def _r(path): p=Path(path); return p if p.is_absolute() else WORK_DIR/p
def _sz(n):
    for u in ["B","KB","MB","GB"]:
        if n<1024: return f"{n:.0f}{u}"
        n/=1024
    return f"{n:.1f}TB"

def tool_read_file(path):
    p=_r(path)
    if not p.exists(): return f"Error: '{p}' not found"
    text=p.read_text(errors="replace"); lines=text.splitlines()
    return f"── {p} ({len(lines)} lines) ──\n"+"\n".join(f"{i+1:4} │ {l}" for i,l in enumerate(lines))

def tool_write_file(path,content):
    p=_r(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content,encoding="utf-8")
    return f"✓ Wrote {len(content)} chars → '{p}'"

def tool_append_file(path,content):
    p=_r(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.open("a").write(content)
    return f"✓ Appended to '{p}'"

def tool_delete_file(path):
    p=_r(path)
    if not p.exists(): return f"Error: not found"
    shutil.rmtree(p) if p.is_dir() else p.unlink()
    return f"✓ Deleted '{p}'"

def tool_list_dir(path="."):
    p=_r(path)
    entries=sorted(p.iterdir(),key=lambda x:(x.is_file(),x.name.lower()))
    lines=["📁 "+e.name+"/" if e.is_dir() else f"📄 {e.name} ({_sz(e.stat().st_size)})" for e in entries]
    return f"── {p} ──\n"+"  \n".join(lines) if lines else "(empty)"

def tool_create_dir(path):
    _r(path).mkdir(parents=True,exist_ok=True); return f"✓ Created"

def tool_move_file(src,dst):
    s,d=_r(src),_r(dst); d.parent.mkdir(parents=True,exist_ok=True)
    shutil.move(str(s),str(d)); return f"✓ Moved '{s}' → '{d}'"

def tool_run_command(command,timeout=30):
    res=subprocess.run(command,shell=True,capture_output=True,text=True,timeout=int(timeout),cwd=str(WORK_DIR))
    parts=[]
    if res.stdout.strip(): parts.append(f"STDOUT:\n{res.stdout.strip()}")
    if res.stderr.strip(): parts.append(f"STDERR:\n{res.stderr.strip()}")
    parts.append(f"Exit: {res.returncode}"); return "\n".join(parts)

def tool_search_in_files(pattern,directory=".",extension=None):
    d=_r(directory); glob=f"**/*{extension}" if extension else "**/*"
    matches=[]
    for f in d.glob(glob):
        if not f.is_file(): continue
        for i,line in enumerate(f.read_text(errors="replace").splitlines(),1):
            if pattern.lower() in line.lower():
                matches.append(f"{f.relative_to(d)}:{i}: {line.strip()}")
    return (f"{len(matches)} match(es):\n"+"\n".join(matches[:60])) if matches else f"No matches for '{pattern}'"

TOOL_MAP = {
    "read_file":       lambda a: tool_read_file(a["path"]),
    "write_file":      lambda a: tool_write_file(a["path"], a["content"]),
    "append_file":     lambda a: tool_append_file(a["path"], a["content"]),
    "delete_file":     lambda a: tool_delete_file(a["path"]),
    "list_dir":        lambda a: tool_list_dir(a.get("path",".")),
    "create_dir":      lambda a: tool_create_dir(a["path"]),
    "move_file":       lambda a: tool_move_file(a["src"], a["dst"]),
    "run_command":     lambda a: tool_run_command(a["command"], a.get("timeout",30)),
    "search_in_files": lambda a: tool_search_in_files(a["pattern"],a.get("directory","."),a.get("extension")),
}

def execute_tool(name, args):
    fn = TOOL_MAP.get(name)
    if not fn: return f"Unknown tool: {name}"
    print(c(f"  ⚙  {name}({', '.join(f'{k}={repr(v)[:40]}' for k,v in args.items())})", "yellow"))
    result = fn(args)
    print(c(f"  ↳  {str(result)[:120]}", "dim"))
    return result

# ── Ollama client ───────────────────────────────────────────────
SYSTEM_PROMPT_TEMPLATE = """You are aicli, a local terminal AI assistant.
CWD: {cwd}   Time: {time}

Available tools — call with: TOOL_CALL: {{"name":"...","args":{{...}}}}
  read_file(path)
  write_file(path, content)
  append_file(path, content)
  delete_file(path)
  list_dir(path=".")
  create_dir(path)
  move_file(src, dst)
  run_command(command, timeout=30)
  search_in_files(pattern, directory=".", extension=None)

Rules: Think step by step. Use tools for real filesystem/shell work.
Read files before editing. Give a clear summary when done.
Put TOOL_CALL on its own line. Only emit TOOL_CALL lines when calling tools."""

def system_prompt():
    return SYSTEM_PROMPT_TEMPLATE.format(cwd=WORK_DIR, time=datetime.now().strftime('%Y-%m-%d %H:%M'))

def list_models():
    try:
        r=requests.get(f"{OLLAMA_BASE}/api/tags",timeout=5)
        return [m["name"] for m in r.json().get("models",[])] if r.ok else []
    except: return []

def call_ollama(messages, model):
    try:
        r=requests.post(f"{OLLAMA_BASE}/api/chat",
            json={"model":model,"messages":messages,"stream":False,
                  "options":{"num_predict":4096,"temperature":0.2}},timeout=180)
        r.raise_for_status(); return r.json()["message"]["content"]
    except requests.exceptions.ConnectionError: return None
    except Exception as e: return f"[Error: {e}]"

def parse_tool_calls(text):
    calls=[]
    for line in text.splitlines():
        line=line.strip()
        if line.startswith("TOOL_CALL:"):
            try:
                obj=json.loads(line[10:].strip())
                calls.append((obj["name"],obj.get("args",{})))
            except: pass
    return calls

def agent_loop(user_input, conversation, model):
    conversation.append({"role":"user","content":user_input})
    messages=[{"role":"system","content":system_prompt()}]+conversation

    for _ in range(12):
        print(c("  ◌ thinking...","dim"),end="\r",flush=True)
        response=call_ollama(messages,model)
        print("                   ",end="\r")

        if response is None:
            err=c("✗ Cannot reach Ollama. Run:  ollama serve","red")
            return err, conversation

        tool_calls=parse_tool_calls(response)
        if not tool_calls:
            clean="\n".join(l for l in response.splitlines() if not l.strip().startswith("TOOL_CALL:")).strip()
            conversation.append({"role":"assistant","content":clean})
            return clean, conversation

        results=[]
        for name,args in tool_calls:
            results.append(f"TOOL_RESULT({name}):\n{execute_tool(name,args)}")
        messages.append({"role":"assistant","content":response})
        messages.append({"role":"user","content":"\n\n".join(results)+"\n\nContinue or give final answer."})

    return c("(too many tool rounds)","yellow"), conversation

# ── REPL ────────────────────────────────────────────────────────
def render(text):
    w=min(shutil.get_terminal_size().columns,80)
    print(); print(c("┌─ AI "+"─"*(w-5),"green"))
    for line in text.split("\n"):
        if line.startswith("```") or line.startswith("    "):
            print(c("│ ","green")+c(line,"yellow"))
        else:
            for wl in (textwrap.wrap(line,w-4) or [""]):
                print(c("│ ","green")+wl)
    print(c("└"+"─"*(w-1),"green")); print()

def main():
    global WORK_DIR
    model = sys.argv[1] if len(sys.argv)>1 else DEFAULT_MODEL
    try:
        if HISTORY_FILE.exists(): readline.read_history_file(HISTORY_FILE)
        readline.set_history_length(1000)
    except: pass

    w=min(shutil.get_terminal_size().columns,62)
    print(c("═"*w,"cyan"))
    print(c("  🤖  aicli","cyan","bold")+c(" — local Ollama terminal AI","dim"))
    print(c(f"  model: {model}   dir: {WORK_DIR}","dim"))
    print(c("  /help for commands","dim")); print(c("═"*w,"cyan"))

    ms=list_models()
    if not ms: print(c("  ⚠  Ollama not running → ollama serve","yellow"))
    elif model not in ms: print(c(f"  ⚠  Pull model first → ollama pull {model}","yellow"))
    else: print(c(f"  ✓  Ollama connected ({len(ms)} models)\n","green"))

    conversation=[]
    while True:
        try: user=input(c(f"[{WORK_DIR.name}]","blue")+c(" ❯ ","cyan","bold")).strip()
        except (EOFError,KeyboardInterrupt): print("\n"+c("Bye!","cyan")); break
        if not user: continue
        try: readline.write_history_file(HISTORY_FILE)
        except: pass

        if user.startswith("/"):
            parts=user.split(None,1); cmd=parts[0].lower(); arg=parts[1].strip() if len(parts)>1 else ""
            if   cmd=="/exit":   print(c("Bye!","cyan")); break
            elif cmd=="/clear":  conversation=[]; print(c("  ✓ cleared","green"))
            elif cmd=="/pwd":    print(c(f"  {WORK_DIR}","cyan"))
            elif cmd=="/cd":
                t=(Path(arg).expanduser() if arg else Path.home())
                t=(WORK_DIR/t).resolve() if not t.is_absolute() else t.resolve()
                if t.is_dir(): WORK_DIR=t; print(c(f"  ✓ {WORK_DIR}","green"))
                else: print(c(f"  ✗ not a directory","red"))
            elif cmd=="/model":
                if arg: model=arg; print(c(f"  ✓ switched to '{model}'","green"))
                else: print(c(f"  model: {model}","cyan"))
            elif cmd=="/models":
                ms=list_models()
                [print(f"    {m}"+c(" ←","green")*(m==model)) for m in ms] if ms else print(c("  none found","yellow"))
            elif cmd=="/help":
                print(c("""
  /help            this help
  /clear           clear conversation
  /model <name>    switch model
  /models          list available models
  /cd <path>       change directory
  /pwd             print directory
  /exit            quit

  Examples:
    > list files here
    > create a flask app in app.py
    > read main.py and add error handling
    > run python app.py
    > find all TODO comments in .py files
""","cyan"))
            else: print(c(f"  unknown: {cmd}","red"))
            continue

        resp, conversation = agent_loop(user, conversation, model)
        render(resp)

if __name__=="__main__": main()