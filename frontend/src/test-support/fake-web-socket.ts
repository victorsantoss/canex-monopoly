export class FakeWebSocket {
  static instances: FakeWebSocket[] = []

  static latest(): FakeWebSocket {
    const socket = FakeWebSocket.instances.at(-1)
    if (socket === undefined) throw new Error('No WebSocket was opened')
    return socket
  }

  readonly url: string
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent<string>) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  closedByClient = false

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instances.push(this)
  }

  close(): void {
    this.closedByClient = true
  }

  serverOpen(): void {
    this.onopen?.(new Event('open'))
  }

  serverSend(data: unknown): void {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }))
  }

  serverSendRaw(data: string): void {
    this.onmessage?.(new MessageEvent('message', { data }))
  }

  serverClose(code: number): void {
    this.onclose?.(new CloseEvent('close', { code }))
  }
}
