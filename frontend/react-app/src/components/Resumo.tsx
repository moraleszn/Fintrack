import { obterResumo } from "../api"
import { formatarMoeda } from "../format"
import type { Filtros } from "../types"
import { useApiData } from "../useApiData"
import {
  IconeCarteira,
  IconeDespesa,
  IconeReceita,
} from "./Icones"

interface Props {
  filtros: Filtros
  versao: number
}

export function Resumo({ filtros, versao }: Props) {
  const { dados, erro, carregando } = useApiData(
    `resumo:${JSON.stringify(filtros)}:${versao}`,
    () => obterResumo(filtros),
  )

  if (carregando) return <p className="estado">Carregando resumo...</p>
  if (erro) return <p className="alerta erro">{erro}</p>
  if (!dados) return null

  const saldoNegativo = Number(dados.saldo) < 0

  return (
    <section className="resumo">
      <article className="cartao receita">
        <div className="cartao-icone">
          <IconeReceita />
        </div>
        <span>Total de receitas</span>
        <strong>{formatarMoeda(dados.total_receitas)}</strong>
      </article>

      <article className="cartao despesa">
        <div className="cartao-icone">
          <IconeDespesa />
        </div>
        <span>Total de despesas</span>
        <strong>{formatarMoeda(dados.total_despesas)}</strong>
      </article>

      <article
        className={`cartao saldo${saldoNegativo ? " negativo" : " positivo"}`}
      >
        <div className="cartao-icone">
          <IconeCarteira />
        </div>
        <span>Saldo do periodo</span>
        <strong>{formatarMoeda(dados.saldo)}</strong>
      </article>

      {saldoNegativo && (
        <p className="alerta atencao largura-total">
          O saldo esta negativo no periodo selecionado.
        </p>
      )}
    </section>
  )
}
