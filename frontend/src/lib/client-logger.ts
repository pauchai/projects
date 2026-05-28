interface LogEntry {
  level: "log" | "warn" | "error"
  message: string
  stack?: string
  timestamp: string
}

interface PageEntry {
  path: string
  time: string
}

interface LogSnapshot {
  logs: LogEntry[]
  pages: PageEntry[]
  url: string
  ua: string
  screen: string
  lang: string
  timestamp: string
}

const MAX_LOGS = 100
const MAX_PAGES = 50

class ClientLogger {
  private logs: LogEntry[] = []
  private pages: PageEntry[] = []
  private patched = false
  private listeners = new Set<() => void>()

  subscribe(fn: () => void): () => void {
    this.listeners.add(fn)
    return () => this.listeners.delete(fn)
  }

  init(): void {
    if (this.patched) return
    this.patched = true

    const originalLog = console.log.bind(console)
    const originalWarn = console.warn.bind(console)
    const originalError = console.error.bind(console)

    console.log = (...args: unknown[]) => {
      this._add("log", args)
      originalLog(...args)
    }
    console.warn = (...args: unknown[]) => {
      this._add("warn", args)
      originalWarn(...args)
    }
    console.error = (...args: unknown[]) => {
      this._add("error", args)
      originalError(...args)
    }

    window.addEventListener("error", (event) => {
      this._add("error", [event.message, event.filename, `line ${event.lineno}`])
    })
    window.addEventListener("unhandledrejection", (event) => {
      this._add("error", ["Unhandled promise rejection", String(event.reason)])
    })

    let prevPath = location.pathname
    this.pages.push({ path: prevPath, time: new Date().toISOString() })

    const originalPushState = history.pushState.bind(history)
    history.pushState = (...args) => {
      originalPushState(...args)
      const path = location.pathname
      if (path !== prevPath) {
        this.pages.push({ path, time: new Date().toISOString() })
        if (this.pages.length > MAX_PAGES) this.pages.shift()
        prevPath = path
      }
    }

    window.addEventListener("popstate", () => {
      const path = location.pathname
      if (path !== prevPath) {
        this.pages.push({ path, time: new Date().toISOString() })
        if (this.pages.length > MAX_PAGES) this.pages.shift()
        prevPath = path
      }
    })

    const originalFetch = window.fetch.bind(window)
    window.fetch = async (...args: Parameters<typeof fetch>): Promise<Response> => {
      const response = await originalFetch(...args)
      let url = "unknown"
      if (typeof args[0] === "string") {
        url = args[0]
      } else if (args[0] instanceof Request) {
        url = args[0].url
      }
      if (!response.ok) {
        this._add("error", [`${response.status} ${response.statusText} ${url}`])
      }
      return response
    }
  }

  getSnapshot(): LogSnapshot {
    return {
      logs: [...this.logs],
      pages: [...this.pages],
      url: location.href,
      ua: navigator.userAgent,
      screen: `${screen.width}x${screen.height}`,
      lang: navigator.language,
      timestamp: new Date().toISOString(),
    }
  }

  getLogCount(): number {
    return this.logs.length
  }

  private _add(level: LogEntry["level"], args: unknown[]): void {
    this.logs.push({
      level,
      message: args.map((a) => (typeof a === "string" ? a : JSON.stringify(a))).join(" "),
      stack: new Error().stack,
      timestamp: new Date().toISOString(),
    })
    if (this.logs.length > MAX_LOGS) this.logs.shift()
    this.listeners.forEach((fn) => fn())
  }
}

export const clientLogger = new ClientLogger()

if (typeof window !== "undefined") {
  ;(window as unknown as { clientLogger: typeof clientLogger }).clientLogger = clientLogger
}
