import type {
  CategoriaResumo,
  Filtros,
  Lancamento,
  LancamentoInput,
  Resumo,
  TipoLancamento,
} from "./types"

export const API_URL = (
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "")

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

function paraQueryString(filtros: Filtros): string {
  const params = new URLSearchParams()
  if (filtros.data_inicio) params.set("data_inicio", filtros.data_inicio)
  if (filtros.data_fim) params.set("data_fim", filtros.data_fim)
  if (filtros.categoria) params.set("categoria", filtros.categoria)
  const query = params.toString()
  return query ? `?${query}` : ""
}

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  let resposta: Response
  try {
    resposta = await fetch(`${API_URL}${caminho}`, { ...init, headers })
  } catch {
    throw new ApiError(
      0,
      `Nao foi possivel conectar em ${API_URL}. A API esta rodando?`,
    )
  }

  if (resposta.status === 204) {
    return undefined as T
  }

  const corpo = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    const detalhe =
      corpo && typeof corpo === "object" && "detail" in corpo
        ? (corpo as { detail: unknown }).detail
        : resposta.statusText
    const mensagem =
      typeof detalhe === "string" ? detalhe : JSON.stringify(detalhe)
    throw new ApiError(resposta.status, mensagem)
  }

  return corpo as T
}

export function listarLancamentos(
  tipo: TipoLancamento,
  filtros: Filtros,
): Promise<Lancamento[]> {
  return requisitar<Lancamento[]>(`/${tipo}${paraQueryString(filtros)}`)
}

export function criarLancamento(
  tipo: TipoLancamento,
  dados: LancamentoInput,
): Promise<Lancamento> {
  return requisitar<Lancamento>(`/${tipo}`, {
    method: "POST",
    body: JSON.stringify(dados),
  })
}

export function atualizarLancamento(
  tipo: TipoLancamento,
  id: number,
  dados: LancamentoInput,
): Promise<Lancamento> {
  return requisitar<Lancamento>(`/${tipo}/${id}`, {
    method: "PATCH",
    body: JSON.stringify(dados),
  })
}

export function excluirLancamento(
  tipo: TipoLancamento,
  id: number,
): Promise<void> {
  return requisitar<void>(`/${tipo}/${id}`, { method: "DELETE" })
}

export function obterResumo(filtros: Filtros): Promise<Resumo> {
  return requisitar<Resumo>(`/resumo${paraQueryString(filtros)}`)
}

export function obterResumoPorCategoria(
  filtros: Filtros,
): Promise<CategoriaResumo[]> {
  return requisitar<CategoriaResumo[]>(
    `/resumo/categorias${paraQueryString({ data_inicio: filtros.data_inicio, data_fim: filtros.data_fim })}`,
  )
}
