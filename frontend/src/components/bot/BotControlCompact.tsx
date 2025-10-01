import { useEffect, useState } from "react"
import { SxButton } from "@/components/ui/sx-button"
import { Power, Loader2 } from "lucide-react"

type BotState = "stopped" | "starting" | "running" | "stopping" | "error"

export function BotControlCompact() {
  const [state, setState] = useState<BotState>("stopped")

  async function getStatus() {
    try {
      setState((s) => s) // 保留現狀（先假資料）
    } catch {
      setState("error")
    }
  }

  async function startBot() {
    setState("starting")
    try {
      await fetch("/api/bot/start", { method: "POST" })
      setState("running")
    } catch {
      setState("error")
    }
  }

  async function stopBot() {
    setState("stopping")
    try {
      await fetch("/api/bot/stop", { method: "POST" })
      setState("stopped")
    } catch {
      setState("error")
    }
  }

  useEffect(() => {
    getStatus()
  }, [])

  const isBusy = state === "starting" || state === "stopping"
  const label =
    state === "running" ? "停止" :
    state === "stopped" ? "啟動" : "..."

  const variant =
    state === "running" ? "danger" :
    state === "stopped" ? "gold" : "secondary"

  const onClick =
    state === "running" ? stopBot :
    state === "stopped" ? startBot : getStatus

  return (
    <SxButton
      variant={variant}
      size="md"
      onClick={onClick}
      leftIcon={isBusy ? <Loader2 className="animate-spin" size={14} /> : <Power size={14} />}
      disabled={isBusy}
    >
      {label}
    </SxButton>
  )
}
