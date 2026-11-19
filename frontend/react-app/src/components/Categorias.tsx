import { obterResumoPorCategoria } from "../api"
import { formatarMoeda } from "../format"
import type { Filtros } from "../types"
import { useApiData } from "../useApiData"

const CORES = [
  "#6366f1",
  "#0ea5e9",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#14b8a6",
  "#f97316",
  "#ec4899",
  "#64748b",
]

const RAIO = 52
const CIRCUNFERENCIA = 2 * Math.PI * RAIO

interface Props {
  filtros: Filtros
  versao: number
}

export function Categorias({ filtros, versao }: Props) {
  const { dados, erro, carregando } = useApiData(
    `categorias:${JSON.stringify(filtros)}:${versao}`,
    () => obterResumoPorCategoria(filtros),
  )

  if (carregando) return <p className="estado">Carregando categorias...</p>
  if (erro) return <p className="alerta erro">{erro}</p>
  if (!dados) return null

  if (dados.length === 0) {
    return (
      <p className="estado">Nenhuma categoria encontrada com os filtros atuais.</p>
    )
  }

  const despesas = dados
    .filter((item) => Number(item.total_despesas) > 0)
    .sort((a, b) => Number(b.total_despesas) - Number(a.total_despesas))

  const totalDespesas = despesas.reduce(
    (soma, item) => soma + Number(item.total_despesas),
    0,
  )

  const fracoes = despesas.map(
    (item) => Number(item.total_despesas) / totalDespesas,
  )
  const fatias = despesas.map((item, indice) => {
    const fracao = fracoes[indice]
    const inicio = fracoes
      .slice(0, indice)
      .reduce((soma, valor) => soma + valor, 0)
    return {
      item,
      cor: CORES[indice % CORES.length],
      trecho: fracao * CIRCUNFERENCIA,
      offset: inicio * CIRCUNFERENCIA,
      percentual: fracao * 100,
    }
  })

  return (
    <section className="painel">
      <div className="painel-topo">
        <div>
          <h2>Despesas por categoria</h2>
          <p className="painel-sub">
            Onde seu dinheiro foi gasto no periodo selecionado.
          </p>
        </div>
      </div>

      {totalDespesas > 0 ? (
        <div className="categoria-visual">
          <div className="donut-wrapper">
            <svg
              viewBox="0 0 120 120"
              className="donut"
              role="img"
              aria-label="Distribuicao das despesas por categoria"
            >
              <circle
                cx="60"
                cy="60"
                r={RAIO}
                className="donut-trilho"
                strokeWidth="15"
              />
              {fatias.map((fatia) => (
                <circle
                  key={fatia.item.categoria}
                  cx="60"
                  cy="60"
                  r={RAIO}
                  strokeWidth="15"
                  fill="none"
                  stroke={fatia.cor}
                  strokeDasharray={`${fatia.trecho} ${CIRCUNFERENCIA - fatia.trecho}`}
                  strokeDashoffset={-fatia.offset}
                  transform="rotate(-90 60 60)"
                  strokeLinecap="butt"
                />
              ))}
            </svg>
            <div className="donut-centro">
              <span>Despesas</span>
              <strong>{formatarMoeda(totalDespesas)}</strong>
            </div>
          </div>

          <ul className="legenda">
            {fatias.map((fatia) => (
              <li key={fatia.item.categoria}>
                <span
                  className="legenda-cor"
                  style={{ background: fatia.cor }}
                  aria-hidden
                />
                <span className="legenda-nome">{fatia.item.categoria}</span>
                <span className="legenda-pct">
                  {fatia.percentual.toFixed(1)}%
                </span>
                <span className="legenda-valor">
                  {formatarMoeda(fatia.item.total_despesas)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="estado">Nenhuma despesa registrada no periodo.</p>
      )}

      <div className="tabela-container">
        <table className="tabela">
          <thead>
            <tr>
              <th>Categoria</th>
              <th className="numerico">Receitas</th>
              <th className="numerico">Despesas</th>
              <th className="numerico">Saldo</th>
            </tr>
          </thead>
          <tbody>
            {dados.map((item) => (
              <tr key={item.categoria}>
                <td>
                  <span className="tag">{item.categoria}</span>
                </td>
                <td className="numerico texto-positivo">
                  {formatarMoeda(item.total_receitas)}
                </td>
                <td className="numerico texto-negativo">
                  {formatarMoeda(item.total_despesas)}
                </td>
                <td
                  className={`numerico ${Number(item.saldo) < 0 ? "texto-negativo" : "texto-positivo"}`}
                >
                  {formatarMoeda(item.saldo)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
