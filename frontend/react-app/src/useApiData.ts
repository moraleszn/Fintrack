import { useEffect, useRef, useState } from "react"

type Estado<T> =
  | { chave: string; dados: T; erro: "" }
  | { chave: string; dados: null; erro: string }

export function useApiData<T>(chave: string, carregar: () => Promise<T>) {
  const [estado, setEstado] = useState<Estado<T> | null>(null)
  const carregarRef = useRef(carregar)

  useEffect(() => {
    carregarRef.current = carregar
  })

  useEffect(() => {
    let ativo = true

    carregarRef
      .current()
      .then((dados) => {
        if (ativo) setEstado({ chave, dados, erro: "" })
      })
      .catch((falha: Error) => {
        if (ativo) setEstado({ chave, dados: null, erro: falha.message })
      })

    return () => {
      ativo = false
    }
  }, [chave])

  if (!estado || estado.chave !== chave) {
    return { carregando: true, dados: null, erro: "" }
  }

  return { carregando: false, dados: estado.dados, erro: estado.erro }
}
