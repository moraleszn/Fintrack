import { useState } from "react"
import { API_URL } from "./api"
import { Categorias } from "./components/Categorias"
import { Filtros } from "./components/Filtros"
import { Lancamentos } from "./components/Lancamentos"
import { Resumo } from "./components/Resumo"
import {
  IconeAtualizar,
  IconeCategoria,
  IconeDespesa,
  IconeReceita,
  IconeResumo,
} from "./components/Icones"
import type { Filtros as FiltrosApi } from "./types"

type Aba = "resumo" | "receitas" | "despesas" | "categorias"

const ABAS: {
  id: Aba
  rotulo: string
  titulo: string
  Icone: typeof IconeResumo
}[] = [
  { id: "resumo", rotulo: "Resumo", titulo: "Visao geral", Icone: IconeResumo },
  { id: "receitas", rotulo: "Receitas", titulo: "Receitas", Icone: IconeReceita },
  { id: "despesas", rotulo: "Despesas", titulo: "Despesas", Icone: IconeDespesa },
  {
    id: "categorias",
    rotulo: "Por categoria",
    titulo: "Por categoria",
    Icone: IconeCategoria,
  },
]

export default function App() {
  const [aba, setAba] = useState<Aba>("resumo")
  const [filtros, setFiltros] = useState<FiltrosApi>({})
  const [versao, setVersao] = useState(0)

  function atualizar() {
    setVersao((valor) => valor + 1)
  }

  const abaAtual = ABAS.find((item) => item.id === aba) ?? ABAS[0]

  const descricaoFiltros = [
    filtros.data_inicio && filtros.data_fim
      ? `Periodo: ${filtros.data_inicio} a ${filtros.data_fim}`
      : "",
    filtros.categoria ? `Categoria: ${filtros.categoria}` : "",
  ]
    .filter(Boolean)
    .join("  |  ")

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="marca">
          <span className="marca-simbolo">F</span>
          <div>
            <strong>Fintrack</strong>
            <small>Controle financeiro pessoal</small>
          </div>
        </div>

        <nav className="nav-lateral" aria-label="Secoes do dashboard">
          {ABAS.map((item) => {
            const Icone = item.Icone
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item${aba === item.id ? " ativa" : ""}`}
                onClick={() => setAba(item.id)}
                aria-current={aba === item.id ? "page" : undefined}
              >
                <Icone />
                <span>{item.rotulo}</span>
              </button>
            )
          })}
        </nav>

        <div className="filtros-cartao">
          <Filtros
            onAplicar={(novos) => setFiltros(novos)}
            onLimpar={() => setFiltros({})}
          />
        </div>

        <p className="api-info">API: {API_URL}</p>
      </aside>

      <main className="conteudo">
        <header className="topo">
          <div className="topo-texto">
            <h1>{abaAtual.titulo}</h1>
            <p>
              {descricaoFiltros || "Sem filtros aplicados: todos os lancamentos."}
            </p>
          </div>
          <button type="button" className="botao neutro" onClick={atualizar}>
            <IconeAtualizar />
            Atualizar
          </button>
        </header>

        <div className="aba-conteudo">
          {aba === "resumo" && <Resumo filtros={filtros} versao={versao} />}
          {aba === "receitas" && (
            <Lancamentos
              tipo="receitas"
              filtros={filtros}
              versao={versao}
              onMutacao={atualizar}
            />
          )}
          {aba === "despesas" && (
            <Lancamentos
              tipo="despesas"
              filtros={filtros}
              versao={versao}
              onMutacao={atualizar}
            />
          )}
          {aba === "categorias" && (
            <Categorias filtros={filtros} versao={versao} />
          )}
        </div>
      </main>
    </div>
  )
}
