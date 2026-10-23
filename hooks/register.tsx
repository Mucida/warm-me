import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import { FOGO, GELO } from './sprites'

const ultimaRequisicao = atom({ plugin: 'warm-me', key: 'ultimaRequisicao' } as const, null)
const ttlMinutos = atom({ plugin: 'warm-me', key: 'ttlMinutos' } as const, 60)
const agora = atom({ plugin: 'warm-me', key: 'agora' } as const, 0)

const CHAVE_TTL = 'warm-me.ttlMinutos'

// Largura do fogo por quarto do TTL que ainda resta: do maior (cache recém-renovado) ao menor
// (último quarto, ex.: 15 min no TTL de 1 h). O desenho é o mesmo, só a escala muda.
const LARGURAS = [18, 26, 34, 44]

function formatar(ms: number): string {
  const total = Math.max(0, Math.ceil(ms / 1000))
  const min = Math.floor(total / 60)
  const seg = total % 60

  return `${min}:${String(seg).padStart(2, '0')}`
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const salvo = await $.store.get(CHAVE_TTL)
    if (salvo === 5 || salvo === 60) {
      await update($, ttlMinutos, () => salvo)
    }

    await $.command.register({
      name: 'warm-me',
      description: 'TTL do cache usado pelo warm-me: /warm-me 60 ou /warm-me 5',
    })

    // Só o contador precisa de redesenho; a dança do fogo é animação do próprio SVG.
    $.clock.every(1000, () => {
      void $.clock.now().then(t => update($, agora, () => t))
    })

    return next(e)
  })

  on('command.run', { command: 'warm-me' }, async ($, e) => {
    const minutos = Number(e.args.trim())
    if (minutos !== 5 && minutos !== 60) {
      return { text: `warm-me: TTL atual ${await read($, ttlMinutos)} min. Use /warm-me 60 ou /warm-me 5.` }
    }

    await update($, ttlMinutos, () => minutos)
    await $.store.set(CHAVE_TTL, minutos)

    return { text: `warm-me: TTL do cache agora é ${minutos} min.` }
  })

  // Cada requisição da conversa principal lê ou grava o cache e renova o TTL. Subagentes têm
  // prefixo próprio e não aquecem o cache desta conversa.
  on('turn.step', async function* ($, e, next) {
    if (e.agentId === undefined) {
      const t = await $.clock.now()
      await update($, ultimaRequisicao, () => t)
    }

    return yield* next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const outros = await next(e)
    if (e.props.hasSurvey) {
      return outros
    }

    const ultima = await read($, ultimaRequisicao)
    const ttlMs = (await read($, ttlMinutos)) * 60_000
    const tick = await read($, agora)
    const t = Math.max(tick, await $.clock.now())

    // Conta sempre da última requisição, mesmo com o turno em andamento: um turno parado numa
    // pergunta ao usuário ou numa ferramenta demorada não renova o cache (antes mostrava "quente").
    const restante = ultima === null ? 0 : ultima + ttlMs - t
    const quente = restante > 0
    // Arredonda para cima: com exatamente 1/4 do TTL restante (15 min no de 1 h) já é o menor fogo.
    const quarto = Math.max(0, Math.min(3, Math.ceil((restante / ttlMs) * 4) - 1))
    const rotulo = quente ? formatar(restante) : 'frio'

    const { Box, Text } = $.ui.resolve(e)
    let sprite
    if (e.surface === 'terminal') {
      sprite = <Text>{quente ? '🔥' : '❄'}</Text>
    } else {
      const { Svg } = $.ui.resolve(e)
      const largura = quente ? LARGURAS[quarto] : 40
      sprite = (
        <Svg
          source={quente ? FOGO : GELO}
          alt={quente ? `Cache quente, ${rotulo} restantes` : 'Cache frio'}
          width={largura}
          height={Math.round(quente ? (largura * 22) / 18 : largura)}
        />
      )
    }

    // Sem width/height no Box: ali a medida não é em pixels, e 52x72 estourava a faixa inteira.
    const meu = (
      <Box flexDirection="column" alignItems="center" marginRight={1}>
        {sprite}
        <Text color={quente ? (quarto === 0 ? '#ff5a1f' : '#ffb347') : '#7cc4ff'}>
          {rotulo}
        </Text>
      </Box>
    )

    return (
      <Box flexDirection="row" alignItems="flex-start">
        {meu}
        <Box flexGrow={1}>{outros}</Box>
      </Box>
    )
  })
}
