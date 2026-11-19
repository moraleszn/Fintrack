export type TipoLancamento = "receitas" | "despesas"

export interface Lancamento {
  id: number
  descricao: string
  valor: string
  data: string
  categoria: string
}

export interface LancamentoInput {
  descricao: string
  valor: string
  data: string
  categoria: string
}

export interface Resumo {
  total_receitas: string
  total_despesas: string
  saldo: string
}

export interface CategoriaResumo {
  categoria: string
  total_receitas: string
  total_despesas: string
  saldo: string
}

export interface Filtros {
  data_inicio?: string
  data_fim?: string
  categoria?: string
}
