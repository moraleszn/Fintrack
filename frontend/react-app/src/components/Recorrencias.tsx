import { useState } from "react"
import type { FormEvent } from "react"
import {
  atualizarRecorrencia,
  criarRecorrencia,
  excluirRecorrencia,
  listarRecorrencias,
  processarRecorrencias,
} from "../api"
import { dataHojeIso, formatarData, formatarMoeda } from "../format"
import type { Recorrencia, TipoRecorrencia } from "../types"
import { useApiData } from "../useApiData"
import {
  IconeAtualizar,
  IconeEditar,
  IconeExcluir,
  IconeMais,
} from "./Icones"

interface Props {
  versao: number
  onMutacao: () => void
}

interface Formulario {
  descricao: string
  valor: string
  categoria: string
  tipo: TipoRecorrencia
  dia_vencimento: number
  data_inicio: string
  data_fim?: string
  ativa: boolean
}

export function Recorrencias({ versao, onMutacao }: Props) {
  const [versaoLocal, setVersaoLocal] = useState(0)
  const [criando, setCriando] = useState(false)
  const [editando, setEditando] = useState<Recorrencia | null>(null)
  const [feedback, setFeedback] = useState("")
  const [erroAcao, setErroAcao] = useState("")
  const [gerando, setGerando] = useState(false)
  const [excluindoId, setExcluindoId] = useState<number | null>(null)

  const {
    dados,
    erro: erroConsulta,
    carregando,
  } = useApiData(`recorrencias:${versao}:${versaoLocal}`, listarRecorrencias)

  const itens = dados ?? []

  async function salvar(dadosForm: Formulario) {
    if (editando) {
      await atualizarRecorrencia(editando.id, {
        descricao: dadosForm.descricao,
        valor: dadosForm.valor,
        categoria: dadosForm.categoria,
        dia_vencimento: dadosForm.dia_vencimento,
        ativa: dadosForm.ativa,
        ...(dadosForm.data_fim ? { data_fim: dadosForm.data_fim } : {}),
      })
      setFeedback("Recorrencia atualizada.")
    } else {
      await criarRecorrencia(dadosForm)
      setFeedback("Recorrencia criada.")
    }
    setCriando(false)
    setEditando(null)
    setErroAcao("")
    setVersaoLocal((valor) => valor + 1)
  }

  async function alternarAtiva(item: Recorrencia) {
    setErroAcao("")
    try {
      await atualizarRecorrencia(item.id, { ativa: !item.ativa })
      setFeedback(item.ativa ? "Recorrencia pausada." : "Recorrencia ativada.")
      setVersaoLocal((valor) => valor + 1)
    } catch (falha) {
      setErroAcao(falha instanceof Error ? falha.message : "Erro ao atualizar.")
    }
  }

  async function excluir(item: Recorrencia) {
    const confirmado = window.confirm(
      `Excluir "${item.descricao}"? Os lancamentos ja gerados serao mantidos.`,
    )
    if (!confirmado) return

    setErroAcao("")
    setExcluindoId(item.id)
    try {
      await excluirRecorrencia(item.id)
      setFeedback("Recorrencia excluida. Lancamentos gerados foram mantidos.")
      setVersaoLocal((valor) => valor + 1)
    } catch (falha) {
      setErroAcao(falha instanceof Error ? falha.message : "Erro ao excluir.")
    } finally {
      setExcluindoId(null)
    }
  }

  async function gerarLancamentos() {
    setErroAcao("")
    setFeedback("")
    setGerando(true)
    try {
      const resultado = await processarRecorrencias()
      setFeedback(
        `Lancamentos gerados: ${resultado.geradas}. Ja existentes: ${resultado.ignoradas}.`,
      )
      setVersaoLocal((valor) => valor + 1)
      onMutacao()
    } catch (falha) {
      setErroAcao(
        falha instanceof Error ? falha.message : "Erro ao gerar lancamentos.",
      )
    } finally {
      setGerando(false)
    }
  }

  const formularioAberto = criando || editando !== null
  const erro = erroAcao || erroConsulta

  return (
    <section className="painel">
      <div className="painel-topo orcamento-topo">
        <div>
          <h2>Recorrencias</h2>
          <p className="painel-sub">
            Cadastre lancamentos fixos e gere as ocorrencias ate hoje. Rodar
            de novo nao duplica.
          </p>
        </div>
        <div className="recorrencia-acoes">
          <button
            type="button"
            className="botao neutro"
            onClick={gerarLancamentos}
            disabled={gerando}
          >
            <IconeAtualizar />
            {gerando ? "Gerando..." : "Gerar lancamentos"}
          </button>
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
            Nova recorrencia
          </button>
        </div>
      </div>

      {feedback && <p className="alerta sucesso compacto">{feedback}</p>}
      {erro && <p className="alerta erro compacto">{erro}</p>}

      {formularioAberto && (
        <RecorrenciaForm
          key={editando ? `edicao-${editando.id}` : "nova"}
          titulo={editando ? "Editar recorrencia" : "Nova recorrencia"}
          inicial={editando ?? undefined}
          onSalvar={salvar}
          onCancelar={() => {
            setCriando(false)
            setEditando(null)
          }}
        />
      )}

      {carregando ? (
        <p className="estado">Carregando recorrencias...</p>
      ) : itens.length === 0 ? (
        <p className="estado">
          Nenhuma recorrencia cadastrada. Crie uma para gerar lancamentos
          fixos automaticamente.
        </p>
      ) : (
        <div className="tabela-container">
          <table className="tabela">
            <thead>
              <tr>
                <th>Descricao</th>
                <th>Tipo</th>
                <th>Categoria</th>
                <th className="numerico">Valor</th>
                <th className="numerico">Vencimento</th>
                <th>Inicio</th>
                <th>Situacao</th>
                <th className="acoes">Acoes</th>
              </tr>
            </thead>
            <tbody>
              {itens.map((item) => (
                <tr key={item.id}>
                  <td>{item.descricao}</td>
                  <td
                    className={
                      item.tipo === "receita"
                        ? "texto-positivo"
                        : "texto-negativo"
                    }
                  >
                    {item.tipo === "receita" ? "Receita" : "Despesa"}
                  </td>
                  <td>
                    <span className="tag">{item.categoria}</span>
                  </td>
                  <td className="numerico">{formatarMoeda(item.valor)}</td>
                  <td className="numerico">Dia {item.dia_vencimento}</td>
                  <td>{formatarData(item.data_inicio)}</td>
                  <td>
                    <span className={`selo ${item.ativa ? "ativa" : "pausada"}`}>
                      {item.ativa ? "Ativa" : "Pausada"}
                    </span>
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
                      className="botao pequeno neutro"
                      onClick={() => alternarAtiva(item)}
                    >
                      {item.ativa ? "Pausar" : "Ativar"}
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

interface FormProps {
  titulo: string
  inicial?: Recorrencia
  onSalvar: (dados: Formulario) => Promise<void>
  onCancelar: () => void
}

function RecorrenciaForm({ titulo, inicial, onSalvar, onCancelar }: FormProps) {
  const [descricao, setDescricao] = useState(inicial?.descricao ?? "")
  const [valor, setValor] = useState(inicial?.valor ?? "")
  const [categoria, setCategoria] = useState(inicial?.categoria ?? "")
  const [tipo, setTipo] = useState<TipoRecorrencia>(inicial?.tipo ?? "despesa")
  const [diaVencimento, setDiaVencimento] = useState(
    String(inicial?.dia_vencimento ?? 1),
  )
  const [dataInicio, setDataInicio] = useState(
    inicial?.data_inicio ?? dataHojeIso(),
  )
  const [dataFim, setDataFim] = useState(inicial?.data_fim ?? "")
  const [ativa, setAtiva] = useState(inicial?.ativa ?? true)
  const [erro, setErro] = useState("")
  const [enviando, setEnviando] = useState(false)

  const editando = inicial !== undefined

  async function enviar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErro("")

    const dia = Number(diaVencimento)
    if (!descricao.trim() || !categoria.trim()) {
      setErro("Descricao e categoria sao obrigatorias.")
      return
    }
    if (!(Number(valor) > 0)) {
      setErro("O valor deve ser maior que zero.")
      return
    }
    if (!Number.isInteger(dia) || dia < 1 || dia > 31) {
      setErro("O dia de vencimento deve ficar entre 1 e 31.")
      return
    }
    if (dataFim && dataFim < dataInicio) {
      setErro("A data fim deve ser maior ou igual a data de inicio.")
      return
    }

    setEnviando(true)
    try {
      await onSalvar({
        descricao: descricao.trim(),
        valor: Number(valor).toFixed(2),
        categoria: categoria.trim(),
        tipo,
        dia_vencimento: dia,
        data_inicio: dataInicio,
        ...(dataFim ? { data_fim: dataFim } : {}),
        ativa,
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
            placeholder="Ex.: Aluguel"
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
          Categoria
          <input
            value={categoria}
            onChange={(event) => setCategoria(event.target.value)}
            placeholder="Ex.: Casa"
            required
          />
        </label>

        <label className="campo">
          Tipo
          <select
            value={tipo}
            onChange={(event) =>
              setTipo(event.target.value as TipoRecorrencia)
            }
            disabled={editando}
          >
            <option value="despesa">Despesa</option>
            <option value="receita">Receita</option>
          </select>
        </label>

        <label className="campo">
          Dia de vencimento
          <input
            type="number"
            min="1"
            max="31"
            value={diaVencimento}
            onChange={(event) => setDiaVencimento(event.target.value)}
            required
          />
        </label>

        <label className="campo">
          Data de inicio
          <input
            type="date"
            value={dataInicio}
            onChange={(event) => setDataInicio(event.target.value)}
            disabled={editando}
            required
          />
        </label>

        <label className="campo">
          Data fim (opcional)
          <input
            type="date"
            value={dataFim}
            onChange={(event) => setDataFim(event.target.value)}
          />
        </label>

        {editando && (
          <label className="campo-check">
            <input
              type="checkbox"
              checked={ativa}
              onChange={(event) => setAtiva(event.target.checked)}
            />
            Recorrencia ativa
          </label>
        )}
      </div>

      {editando && (
        <p className="painel-sub">
          Tipo e data de inicio nao podem ser alterados apos a criacao.
        </p>
      )}

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
