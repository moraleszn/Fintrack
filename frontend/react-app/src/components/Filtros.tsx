import { useState } from "react"
import type { FormEvent } from "react"
import { dataHojeIso, primeiroDiaDoMesIso } from "../format"
import type { Filtros as FiltrosApi } from "../types"

interface Props {
  onAplicar: (filtros: FiltrosApi) => void
  onLimpar: () => void
}

export function Filtros({ onAplicar, onLimpar }: Props) {
  const [usarPeriodo, setUsarPeriodo] = useState(false)
  const [inicio, setInicio] = useState(primeiroDiaDoMesIso)
  const [fim, setFim] = useState(dataHojeIso)
  const [categoria, setCategoria] = useState("")
  const [erro, setErro] = useState("")

  function aplicar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")

    if (usarPeriodo && inicio > fim) {
      setErro("A data inicial nao pode ser maior que a final.")
      return
    }

    const filtros: FiltrosApi = {}
    if (usarPeriodo) {
      filtros.data_inicio = inicio
      filtros.data_fim = fim
    }
    if (categoria.trim()) {
      filtros.categoria = categoria.trim()
    }
    onAplicar(filtros)
  }

  function limpar() {
    setUsarPeriodo(false)
    setInicio(primeiroDiaDoMesIso())
    setFim(dataHojeIso())
    setCategoria("")
    setErro("")
    onLimpar()
  }

  return (
    <form className="filtros" onSubmit={aplicar}>
      <h2>Filtros</h2>

      <label className="campo-check">
        <input
          type="checkbox"
          checked={usarPeriodo}
          onChange={(event) => setUsarPeriodo(event.target.checked)}
        />
        Filtrar por periodo
      </label>

      <label className="campo">
        De
        <input
          type="date"
          value={inicio}
          onChange={(event) => setInicio(event.target.value)}
          disabled={!usarPeriodo}
        />
      </label>

      <label className="campo">
        Ate
        <input
          type="date"
          value={fim}
          onChange={(event) => setFim(event.target.value)}
          disabled={!usarPeriodo}
        />
      </label>

      <label className="campo">
        Categoria
        <input
          type="text"
          value={categoria}
          onChange={(event) => setCategoria(event.target.value)}
          placeholder="Ex.: Casa"
        />
      </label>

      {erro && <p className="alerta erro compacto">{erro}</p>}

      <div className="filtros-acoes">
        <button type="submit" className="botao primario">
          Aplicar
        </button>
        <button type="button" className="botao neutro" onClick={limpar}>
          Limpar
        </button>
      </div>
    </form>
  )
}
