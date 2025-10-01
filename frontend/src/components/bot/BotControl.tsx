import { useEffect, useState } from "react"
import { SxButton } from "@/components/ui/sx-button"
import { Power, Loader2 } from "lucide-react"

type BotState = "stopped" | "starting" | "running" | "stopping" | "error"

export function BotControl() {
  const [state, setState] = useState<BotState>("stopped")
  const [msg, setMsg] = useState<string>("")

  // 你之後把這三個 fetch 換成實際後端端點
  async function getStatus() {
    try {
      // 假資料：請改成 GET /api/bot/status
      // const res = await fetch("/api/bot/status"); const d = await res.json();
      // setState(d.status)
      setState((s) => s) // 保留現狀（先假資料）
    } catch {
      setState("error")
      setMsg("無法取得狀態")
    }
  }

  async function startBot() {
    setState("starting")
    try {
      await fetch("/api/bot/start", { method: "POST" }) // ← 換成你的後端
      setState("running")
    } catch {
      setState("error")
      setMsg("啟動失敗")
    }
  }

  async function stopBot() {
    setState("stopping")
    try {
      await fetch("/api/bot/stop", { method: "POST" }) // ← 換成你的後端
      setState("stopped")
    } catch {
      setState("error")
      setMsg("停止失敗")
    }
  }

  useEffect(() => {
    getStatus()
  }, [])

  const isBusy = state === "starting" || state === "stopping"
  const label =
    state === "running" ? "停止機器人" :
    state === "stopped" ? "啟動機器人" :
    state === "starting" ? "啟動中…" :
    state === "stopping" ? "停止中…" : "重試"

  const variant =
    state === "running" ? "danger" :
    state === "stopped" ? "gold" :
    state === "error" ? "outline" : "secondary"

  const onClick =
    state === "running" ? stopBot :
    state === "stopped" ? startBot : getStatus

  return (
    <div className="sx-card p-4 flex items-center justify-between">
      <div>
        <div className="text-sm text-sx-sub">機器人狀態</div>
        <div className="text-lg font-semibold mt-0.5 text-sx-text">
          {state === "running" && "運行中"}
          {state === "stopped" && "已停止"}
          {state === "starting" && "啟動中…"}
          {state === "stopping" && "停止中…"}
          {state === "error" && "錯誤"}
        </div>
        {msg && <div className="text-xs text-red-400 mt-1">{msg}</div>}
      </div>
      <SxButton
        variant={variant}
        size="lg"
        onClick={onClick}
        leftIcon={isBusy ? <Loader2 className="animate-spin" size={16} /> : <Power size={16} />}
        disabled={isBusy}
      >
        {label}
      </SxButton>
    </div>
  )
}
