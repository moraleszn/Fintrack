import { useState } from "react"
import {
  atualizarLancamento,
  criarLancamento,
  excluirLancamento,
  listarLancamentos,
} from "../api"
import { formatarData, formatarMoeda } from "../format"
import type {
  Filtros,
  Lancamento,
  LancamentoInput,
  TipoLancamento,
} from "../types"
import { useApiData } from "../useApiData"
import { LancamentoForm } from "./LancamentoForm"
import { IconeEditar, IconeExcluir, IconeMais } from "./Icones"

interface Props {
  tipo: TipoLancamento
  filtros: Filtros
  versao: number
  onMutacao: () => void
}

export function Lancamentos({ tipo, filtros, versao, onMutacao }: Props) {
  const [feedback, setFeedback] = useState("")
  const [erroAcao, setErroAcao] = useState("")
  const [criando, setCriando] = useState(false)
  const [editando, setEditando] = useState<Lancamento | null>(null)
  const [excluindoId, setExcluindoId] = useState<number | null>(null)

  const {
    dados,
    erro: erroConsulta,
    carregando,
  } = useApiData(`lancamentos:${tipo}:${JSON.stringify(filtros)}:${versao}`, () =>
    listarLancamentos(tipo, filtros),
  )

  const itens = dados ?? []
  const singular = tipo === "receitas" ? "receita" : "despesa"

  async function salvar(dadosForm: LancamentoInput) {
    if (editando) {
      await atualizarLancamento(tipo, editando.id, dadosForm)
      setFeedback("Lancamento atualizado.")
    } else {
      await criarLancamento(tipo, dadosForm)
      setFeedback("Lancamento criado.")
    }
    setCriando(false)
    setEditando(null)
    setErroAcao("")
    onMutacao()
  }

  async function excluir(item: Lancamento) {
    const confirmado = window.confirm(
      `Excluir "${item.descricao}"? Essa acao nao pode ser desfeita.`,
    )
    if (!confirmado) return

    setErroAcao("")
    setExcluindoId(item.id)
    try {
      await excluirLancamento(tipo, item.id)
      setFeedback("Lancamento excluido.")
      onMutacao()
    } catch (falha) {
      setErroAcao(falha instanceof Error ? falha.message : "Erro ao excluir.")
    } finally {
      setExcluindoId(null)
    }
  }

  const formularioAberto = criando || editando !== null
  const erro = erroAcao || erroConsulta

  return (
    <section className="painel">
      <div className="painel-topo">
        <h2>{tipo === "receitas" ? "Receitas" : "Despesas"}</h2>
        <button
          type="button"
          className="botao primario"
          onClick={() => {
            setCriando(true)
            setEditando(null)
            setFeedback("")
          }}
        >
          <IconeMais />
          Nova {singular}
        </button>
      </div>

      {feedback && <p className="alerta sucesso compacto">{feedback}</p>}
      {erro && <p className="alerta erro compacto">{erro}</p>}

      {formularioAberto && (
        <LancamentoForm
          key={editando ? `edicao-${editando.id}` : "novo"}
          titulo={editando ? `Editar ${singular}` : `Nova ${singular}`}
          inicial={editando ?? undefined}
          onSalvar={salvar}
          onCancelar={() => {
            setCriando(false)
            setEditando(null)
          }}
        />
      )}

      {carregando ? (
        <p className="estado">Carregando {tipo}...</p>
      ) : itens.length === 0 ? (
        <p className="estado">
          Nenhuma {singular} encontrada com os filtros atuais.
        </p>
      ) : (
        <div className="tabela-container">
          <table className="tabela">
            <thead>
              <tr>
                <th>Data</th>
                <th>Descricao</th>
                <th>Categoria</th>
                <th className="numerico">Valor</th>
                <th className="acoes">Acoes</th>
              </tr>
            </thead>
            <tbody>
              {itens.map((item) => (
                <tr key={item.id}>
                  <td>{formatarData(item.data)}</td>
                  <td>{item.descricao}</td>
                  <td>
                    <span className="tag">{item.categoria}</span>
                  </td>
                  <td
                    className={`numerico ${tipo === "receitas" ? "texto-positivo" : "texto-negativo"}`}
                  >
                    {formatarMoeda(item.valor)}
                  </td>
                  <td className="acoes">
                    <button
                      type="button"
                      className="botao pequeno neutro"
                      onClick={() => {
                        setEditando(item)
                        setCriando(false)
                        setFeedback("")
                      }}
                    >
                      <IconeEditar />
                      Editar
                    </button>
                    <button
                      type="button"
                      className="botao pequeno perigo"
                      onClick={() => excluir(item)}
                      disabled={excluindoId === item.id}
                    >
                      <IconeExcluir />
                      {excluindoId === item.id ? "Excluindo..." : "Excluir"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
