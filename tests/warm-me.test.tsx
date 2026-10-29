import { expect, mock, test } from 'claude-code/testing'

import { forkRenovouCache } from '../hooks/register'

const BANDA = {
  plugin: 'warm-me',
  component: 'AbovePrompt',
  surface: 'desktop',
  props: { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 80, scroll: { offset: 0, bodyRows: 10 } },
} as const

const SEG = 1000

test('o fogo encolhe a cada quarto do TTL e vira gelo quando o cache esfria', async ($, on) => {
  const relogio = mock.clock(on)
  on('command.register', () => ({ value: { command: 'warm-me' } }))
  // TTL de 5 min salvo pelo /warm-me 5: a mesma conta do de 1 h com menos batidas do contador.
  on('store.get', () => ({ value: 5 }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  // Embaixo do mod: o Pokémon de outro plugin, que tem de continuar na faixa.
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>pokemon</Text>
  })
  on('turn.step', async function* (_, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
  })

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  const ui = await $.ui.mount(BANDA)
  expect((await ui.find({ type: 'Text', text: /frio/ }))?.text).toBe('frio')

  const passo = $.turn.step({ turnId: 't1', index: 0, model: 'claude-opus-5-5', messageCount: 1 })
  for await (const _ of passo) {
    // nada a ler: só importa o horário da requisição
  }

  const largura = async () => (await ui.find({ type: 'Svg' }))?.props.width
  expect(await largura()).toBe(44)
  expect((await ui.find({ type: 'Text', text: /pokemon/ }))?.text).toBe('pokemon')

  await relogio.advance(75 * SEG)
  expect(await largura()).toBe(34)
  expect((await ui.find({ type: 'Text', text: /^3:45$/ }))?.text).toBe('3:45')

  await relogio.advance(75 * SEG)
  expect(await largura()).toBe(26)

  await relogio.advance(75 * SEG)
  expect(await largura()).toBe(18)
  expect((await ui.find({ type: 'Text', text: /^1:15$/ }))?.text).toBe('1:15')

  await relogio.advance(76 * SEG)
  expect((await ui.find({ type: 'Text', text: /frio/ }))?.text).toBe('frio')
  expect((await ui.find({ type: 'Svg' }))?.props.alt).toBe('Cache frio')

  await ui.unmount()
})

test('turno parado esperando o usuário não segura o cache quente', async ($, on) => {
  const relogio = mock.clock(on)
  on('command.register', () => ({ value: { command: 'warm-me' } }))
  on('store.get', () => ({ value: 5 }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>pokemon</Text>
  })
  on('turn.step', async function* (_, e) {
    return { turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: 'end_turn', usage: null }
  })

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  for await (const _ of $.turn.step({ turnId: 't1', index: 0, model: 'claude-opus-5-5', messageCount: 1 })) {
    // só o horário da requisição importa
  }

  // O turno segue "em andamento" (uma pergunta aberta), mas sem requisição nova o cache envelhece.
  const ui = await $.ui.mount({ ...BANDA, props: { ...BANDA.props, isWorking: true } })
  await relogio.advance(60 * SEG)
  expect((await ui.find({ type: 'Text', text: /^4:00$/ }))?.text).toBe('4:00')

  await relogio.advance(241 * SEG)
  expect((await ui.find({ type: 'Text', text: /frio/ }))?.text).toBe('frio')

  await ui.unmount()
})

const uso = (lido: number) => ({ input_tokens: 10, output_tokens: 1, cache_read_input_tokens: lido, cache_creation_input_tokens: 10 })

// O kit não dispara $.model.fork de outro plugin, então a regra é testada fora do hook.
test('ping do keepwarm renova o timer só quando leu o cache', () => {
  expect(forkRenovouCache({ isAnswered: true, text: 'warm', usage: uso(90_000) })).toBe(true)
  expect(forkRenovouCache({ isAnswered: true, text: 'warm', usage: uso(0) })).toBe(false)
  // Cortado depois de ler: a leitura aconteceu e renovou o TTL.
  expect(forkRenovouCache({ isAnswered: false, reason: 'aborted', usage: uso(90_000) })).toBe(true)
  expect(forkRenovouCache({ isAnswered: false, reason: 'nothing-to-fork' })).toBe(false)
})
