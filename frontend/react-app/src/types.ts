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

export interface Orcamento {
  id: number
  categoria: string
  valor_limite: string
  ano: number
  mes: number
}

export interface OrcamentoInput {
  categoria: string
  valor_limite: string
  ano: number
  mes: number
}

export interface OrcamentoAtualizacao {
  categoria?: string
  valor_limite?: string
}

export type StatusOrcamento = "ok" | "atencao" | "estourado"

export type TipoRecorrencia = "receita" | "despesa"

export interface Recorrencia {
  id: number
  descricao: string
  valor: string
  categoria: string
  tipo: TipoRecorrencia
  dia_vencimento: number
  data_inicio: string
  data_fim: string | null
  ativa: boolean
}

export interface RecorrenciaInput {
  descricao: string
  valor: string
  categoria: string
  tipo: TipoRecorrencia
  dia_vencimento: number
  data_inicio: string
  data_fim?: string
  ativa: boolean
}

export interface RecorrenciaAtualizacao {
  descricao?: string
  valor?: string
  categoria?: string
  dia_vencimento?: number
  data_fim?: string
  ativa?: boolean
}

export interface ProcessamentoResultado {
  ate: string
  geradas: number
  ignoradas: number
}

export interface OrcamentoDesempenho {
  id: number
  categoria: string
  valor_limite: string
  total_despesas: string
  disponivel: string
  percentual_usado: string
  projecao_fim_mes: string
  status: StatusOrcamento
}
