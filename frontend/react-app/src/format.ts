const formatadorMoeda = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
})

export function formatarMoeda(valor: string | number): string {
  return formatadorMoeda.format(Number(valor))
}

export function formatarData(dataIso: string): string {
  const [ano, mes, dia] = dataIso.split("-")
  return `${dia}/${mes}/${ano}`
}

export function dataHojeIso(): string {
  const agora = new Date()
  const local = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

export function primeiroDiaDoMesIso(): string {
  const agora = new Date()
  const mes = String(agora.getMonth() + 1).padStart(2, "0")
  return `${agora.getFullYear()}-${mes}-01`
}
