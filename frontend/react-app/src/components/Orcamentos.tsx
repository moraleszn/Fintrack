import { useState } from "react"
import type { FormEvent } from "react"
import {
  atualizarOrcamento,
  criarOrcamento,
  excluirOrcamento,
  obterDesempenhoOrcamentos,
} from "../api"
import { formatarMoeda, mesAtualIso } from "../format"
import type { OrcamentoDesempenho, StatusOrcamento } from "../types"
import { useApiData } from "../useApiData"
import { IconeEditar, IconeExcluir, IconeMais } from "./Icones"

const ROTULOS: Record<StatusOrcamento, string> = {
  ok: "Dentro do orcamento",
  atencao: "Atencao",
  estourado: "Estourado",
}

interface Props {
  versao: number
}

interface Formulario {
  categoria: string
  valor_limite: string
}

export function Orcamentos({ versao }: Props) {
  const [periodo, setPeriodo] = useState(mesAtualIso)
  const [versaoLocal, setVersaoLocal] = useState(0)
  const [criando, setCriando] = useState(false)
  const [editando, setEditando] = useState<OrcamentoDesempenho | null>(null)
  const [feedback, setFeedback] = useState("")
  const [erroAcao, setErroAcao] = useState("")
  const [excluindoId, setExcluindoId] = useState<number | null>(null)

  const [anoTexto, mesTexto] = periodo.split("-")
  const ano = Number(anoTexto)
  const mes = Number(mesTexto)

  const abreviacaoPeriodo = `${mesTexto}/${anoTexto}`

  const {
    dados,
    erro: erroConsulta,
    carregando,
  } = useApiData(`orcamentos:${ano}:${mes}:${versao}:${versaoLocal}`, () =>
    obterDesempenhoOrcamentos(ano, mes),
  )

  const itens = dados ?? []
  const totalPlanejado = itens.reduce(
    (soma, item) => soma + Number(item.valor_limite),
    0,
  )
  const totalGasto = itens.reduce(
    (soma, item) => soma + Number(item.total_despesas),
    0,
  )
  const totalDisponivel = totalPlanejado - totalGasto

  async function salvar(dadosForm: Formulario) {
    if (editando) {
      await atualizarOrcamento(editando.id, dadosForm)
      setFeedback("Orcamento atualizado.")
    } else {
      await criarOrcamento({ ...dadosForm, ano, mes })
      setFeedback("Orcamento criado.")
    }
    setCriando(false)
    setEditando(null)
    setErroAcao("")
    setVersaoLocal((valor) => valor + 1)
  }

  async function excluir(item: OrcamentoDesempenho) {
    const confirmado = window.confirm(
      `Excluir o orcamento de "${item.categoria}" em ${abreviacaoPeriodo}?`,
    )
    if (!confirmado) return

    setErroAcao("")
    setExcluindoId(item.id)
    try {
      await excluirOrcamento(item.id)
      setFeedback("Orcamento excluido.")
      setVersaoLocal((valor) => valor + 1)
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
      <div className="painel-topo orcamento-topo">
        <div>
          <h2>Orcamentos</h2>
          <p className="painel-sub">
            Defina um teto por categoria e acompanhe o ritmo de gasto do mes.
          </p>
        </div>
        <div className="orcamento-controles">
          <label className="campo">
            Mes
            <input
              type="month"
              value={periodo}
              onChange={(event) =>
                setPeriodo(event.target.value || mesAtualIso())
              }
            />
          </label>
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
            Novo orcamento
          </button>
        </div>
      </div>

      {feedback && <p className="alerta sucesso compacto">{feedback}</p>}
      {erro && <p className="alerta erro compacto">{erro}</p>}

      {formularioAberto && (
        <OrcamentoForm
          key={editando ? `edicao-${editando.id}` : "novo"}
          titulo={editando ? "Editar orcamento" : "Novo orcamento"}
          inicial={editando ?? undefined}
          onSalvar={salvar}
          onCancelar={() => {
            setCriando(false)
            setEditando(null)
          }}
        />
      )}

      {carregando ? (
        <p className="estado">Carregando orcamentos...</p>
      ) : itens.length === 0 ? (
        <p className="estado">
          Nenhum orcamento definido para {abreviacaoPeriodo}. Crie um para
          comparar planejado x realizado.
        </p>
      ) : (
        <>
          <div className="orcamento-totais">
            <div className="orcamento-total">
              <span>Planejado</span>
              <strong>{formatarMoeda(totalPlanejado)}</strong>
            </div>
            <div className="orcamento-total gasto">
              <span>Gasto</span>
              <strong>{formatarMoeda(totalGasto)}</strong>
            </div>
            <div
              className={`orcamento-total ${totalDisponivel < 0 ? "negativo" : "positivo"}`}
            >
              <span>Disponivel</span>
              <strong>{formatarMoeda(totalDisponivel)}</strong>
            </div>
          </div>

          <div className="orcamentos-lista">
            {itens.map((item) => {
              const percentual = Number(item.percentual_usado)
              const disponivel = Number(item.disponivel)
              const largura = Math.min(Math.max(percentual, 0), 100)

              return (
                <article
                  key={item.id}
                  className={`orcamento-item ${item.status}`}
                >
                  <div className="orcamento-item-topo">
                    <div className="orcamento-ident">
                      <span className="tag">{item.categoria}</span>
                      <span className={`selo ${item.status}`}>
                        {ROTULOS[item.status]}
                      </span>
                    </div>
                    <div className="orcamento-acoes">
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
                    </div>
                  </div>

                  <div className="orcamento-valores">
                    <strong>{formatarMoeda(item.total_despesas)}</strong>
                    <span>de {formatarMoeda(item.valor_limite)}</span>
                  </div>

                  <div
                    className="barra"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(percentual)}
                    aria-label={`${item.categoria}: ${percentual.toFixed(0)}% do orcamento`}
                  >
                    <div
                      className={`barra-preenchida ${item.status}`}
                      style={{ width: `${largura}%` }}
                    />
                  </div>

                  <div className="orcamento-meta">
                    <span>{percentual.toFixed(0)}% do limite</span>
                    <span className={disponivel < 0 ? "texto-negativo" : ""}>
                      {disponivel < 0
                        ? `${formatarMoeda(Math.abs(disponivel))} acima`
                        : `${formatarMoeda(disponivel)} disponivel`}
                    </span>
                    <span>
                      Projecao no mes: {formatarMoeda(item.projecao_fim_mes)}
                    </span>
                  </div>
                </article>
              )
            })}
          </div>

          <p className="painel-sub">
            A projecao estima o gasto ate o fim do mes mantendo o ritmo atual.
          </p>
        </>
      )}
    </section>
  )
}

interface FormProps {
  titulo: string
  inicial?: OrcamentoDesempenho
  onSalvar: (dados: Formulario) => Promise<void>
  onCancelar: () => void
}

function OrcamentoForm({ titulo, inicial, onSalvar, onCancelar }: FormProps) {
  const [categoria, setCategoria] = useState(inicial?.categoria ?? "")
  const [valorLimite, setValorLimite] = useState(inicial?.valor_limite ?? "")
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")

    if (!categoria.trim()) {
      setErro("Informe a categoria.")
      return
    }

    if (!(Number(valorLimite) > 0)) {
      setErro("O limite deve ser maior que zero.")
      return
    }

    setEnviando(true)
    try {
      await onSalvar({
        categoria: categoria.trim(),
        valor_limite: Number(valorLimite).toFixed(2),
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
          Categoria
          <input
            value={categoria}
            onChange={(event) => setCategoria(event.target.value)}
            placeholder="Ex.: Alimentacao"
            required
          />
        </label>

        <label className="campo">
          Limite mensal
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={valorLimite}
            onChange={(event) => setValorLimite(event.target.value)}
            placeholder="0,00"
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
