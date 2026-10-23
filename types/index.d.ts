export type Ttl = 5 | 60

declare module 'claude-code' {
  interface PluginState {
    'warm-me': {
      /** Quando a última requisição da conversa principal foi enviada ($.clock.now(), ms). */
      ultimaRequisicao: number | null
      /** TTL do cache em minutos (o cache de 1 h ou o de 5 min). */
      ttlMinutos: Ttl
      /** Batida de 1 s que redesenha o contador. */
      agora: number
    }
  }
}

