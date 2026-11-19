import { useState } from "react"
import type { FormEvent } from "react"
import { dataHojeIso } from "../format"
import type { Lancamento, LancamentoInput } from "../types"

interface Props {
  titulo: string
  inicial?: Lancamento
  onSalvar: (dados: LancamentoInput) => Promise<void>
  onCancelar: () => void
}

export function LancamentoForm({
  titulo,
  inicial,
  onSalvar,
  onCancelar,
}: Props) {
  const [descricao, setDescricao] = useState(inicial?.descricao ?? "")
  const [valor, setValor] = useState(inicial?.valor ?? "")
  const [data, setData] = useState(inicial?.data ?? dataHojeIso())
  const [categoria, setCategoria] = useState(inicial?.categoria ?? "")
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")

    if (!descricao.trim() || !categoria.trim()) {
      setErro("Descricao e categoria sao obrigatorias.")
      return
    }

    if (!(Number(valor) > 0)) {
      setErro("O valor deve ser maior que zero.")
      return
    }

    setEnviando(true)
    try {
      await onSalvar({
        descricao: descricao.trim(),
        valor: Number(valor).toFixed(2),
        data,
        categoria: categoria.trim(),
      })
    } catch (falha) {
      setErro(falha instanceof Error ? falha.message : "Erro ao salvar.")
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="formulario" onSubmit={enviar}>
      <h3>{titulo}</h3>

      <div className="formulario-grade">
        <label className="campo largo">
          Descricao
          <input
            value={descricao}
            onChange={(event) => setDescricao(event.target.value)}
            placeholder="Ex.: Salario"
            required
          />
        </label>

        <label className="campo">
          Valor
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={valor}
            onChange={(event) => setValor(event.target.value)}
            placeholder="0,00"
            required
          />
        </label>

        <label className="campo">
          Data
          <input
            type="date"
            value={data}
            onChange={(event) => setData(event.target.value)}
            required
          />
        </label>

        <label className="campo">
          Categoria
          <input
            value={categoria}
            onChange={(event) => setCategoria(event.target.value)}
            placeholder="Ex.: Trabalho"
            required
          />
        </label>
      </div>

      {erro && <p className="alerta erro compacto">{erro}</p>}

      <div className="formulario-acoes">
        <button type="submit" className="botao primario" disabled={enviando}>
          {enviando ? "Salvando..." : "Salvar"}
        </button>
        <button
          type="button"
          className="botao neutro"
          onClick={onCancelar}
          disabled={enviando}
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}
